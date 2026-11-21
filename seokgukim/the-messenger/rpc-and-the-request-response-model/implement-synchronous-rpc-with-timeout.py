#!/usr/bin/env python3
import sys
import json
import threading

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.RLock()  # send_rpc registers and sends atomically
        self.pending = {}  # msg_id -> threading.Event
        self.replies = {}  # msg_id -> reply body

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
        # TODO: Send the message and register a waiter for it
        # 1. Create a threading.Event and store it in self.pending under the msg_id
        # 2. Make sure it is registered before a reply can be handled
        # 3. Return the msg_id
        with self.lock:
            msg_id = self.next_msg_id
            self.pending[msg_id] = threading.Event()
            self.send(dest, body)
            return msg_id

    def wait_reply(self, msg_id, timeout=1.0):
        # TODO: Block until the reply arrives or the timeout passes
        # Return the reply body, or None on timeout; remove the pending entry either way
        with self.lock:
            event = self.pending[msg_id]
        event.wait(timeout)
        with self.lock:
            self.pending.pop(msg_id, None)
            return self.replies.pop(msg_id, None)

    def handle_reply(self, body):
        # TODO: Check if this is a reply to a pending RPC
        # Match using in_reply_to field, store the body and wake the waiter
        with self.lock:
            msg_id = body.get("in_reply_to")
            event = self.pending.get(msg_id)
            if event is not None and not event.is_set():
                self.replies[msg_id] = body
                event.set()

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
        elif msg_type == "proxy":
            #   "error": code, text.
            #   "proxy_ok": result.
            # TODO: Forward the inner message to the target with send_rpc here,
            # then wait for the reply and answer the caller on a new thread
            def proxy(request):
                body = request["body"]
                msg_id = node.send_rpc(body["target"], body["inner"])
                result = node.wait_reply(msg_id)
                if result is None:
                    node.reply(request, {"type": "error", "code": 0, "text": "RPC timeout"})
                else:
                    node.reply(request, {"type": "proxy_ok", "result": result})

            threading.Thread(target=proxy, args=(message,)).start()
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
