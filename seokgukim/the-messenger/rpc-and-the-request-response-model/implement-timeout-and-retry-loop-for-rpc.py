#!/usr/bin/env python3
import sys
import json
import threading
import time

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.pending = {}

        self.replies = {}

    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            msg_id = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        print(json.dumps(message), flush=True)
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def send_rpc(self, dest, body):
        # Registers the waiter before the message is written, so a fast reply always finds it.
        event = threading.Event()
        with self.lock:
            msg_id = self.next_msg_id
            self.next_msg_id += 1
            self.pending[msg_id] = event
            body = dict(body, msg_id=msg_id)
            print(json.dumps({"src": self.node_id, "dest": dest, "body": body}), flush=True)
        return msg_id

    def wait_reply(self, msg_id, timeout=0.5):
        with self.lock:
            event = self.pending[msg_id]
        event.wait(timeout=timeout)
        with self.lock:
            self.pending.pop(msg_id, None)
            return self.replies.pop(msg_id, None)

    def rpc_with_retry(self, dest, body, first_msg_id, timeout=0.5, max_retries=3):
        # TODO: Implement the retry loop
        # The first attempt (first_msg_id) was already sent by the reading loop;
        # wait for it, and send each retry with send_rpc (a new msg_id).
        # Return (result, attempts) tuple
        attempts = 1
        reply = self.wait_reply(first_msg_id, timeout=timeout)
        if reply is not None:
            return (reply, attempts)

        while attempts < max_retries:
            msg_id = self.send_rpc(dest, body)
            reply = self.wait_reply(msg_id, timeout=timeout)
            if reply is not None:
                return (reply, attempts)
            attempts += 1

        return (None, attempts)


    def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        with self.lock:
            if reply_to is not None and reply_to in self.pending:
                self.replies[reply_to] = body
                self.pending[reply_to].set()

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "relay":
            # The request body has: target, payload.
            #   "error": code, text.
            #   "relay_ok": attempts, result.
            # TODO: Send the first attempt to the target with send_rpc here,
            # then run rpc_with_retry and answer the caller on a new thread
            msg_id = node.send_rpc(body["target"], body["payload"])
            def finish_relay(request, first_msg_id):
                request_body = request["body"]
                result, attempts = node.rpc_with_retry(
                    request_body["target"], request_body["payload"], first_msg_id
                )
                if result is not None:
                    node.reply(request, {"type": "relay_ok", "attempts": attempts, "result": result})
                else:
                    node.reply(request, {"type": "error", "code": 0, "text": "RPC failed after 3 attempts"})

            threading.Thread(target=finish_relay, args=(message, msg_id)).start()
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
