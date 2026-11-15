#!/usr/bin/env python3
import sys
import json
import threading

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.pending = {}  # msg_id -> threading.Event
        self.replies = {}  # msg_id -> reply body

        self.proxy_lock = threading.Lock()

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
        with self.proxy_lock:
            msg_id = self.send(dest, body)
            self.pending[msg_id] = threading.Event()
        return msg_id

    def wait_reply(self, msg_id, timeout=1.0):
        with self.lock:
            event = self.pending[msg_id]

        if event.wait(timeout):
            body = {
                "type": "proxy_ok",
                "result": self.replies[msg_id]
            }

        else:
            body = {
            "type": "error",
            "code": 0,
            "text": "RPC timeout"
        }
            
        return body

    def handle_reply(self, body):
        with self.proxy_lock:
            msg_id = body.get("in_reply_to")

        with self.lock:
            event = self.pending.get(msg_id)

            if event is None:
                return

            self.replies[msg_id] = body
            event.set()

    def proxy_response(self, requset, body):
        msg_id = self.send_rpc(body["target"], body["inner"])
        self.reply(requset, self.wait_reply(msg_id))

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
            threading.Thread(target=node.proxy_response, args=(message, body)).start()

        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
