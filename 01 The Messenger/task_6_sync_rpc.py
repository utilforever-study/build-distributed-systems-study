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
        return self.send(dest, body)

    def wait_reply(self, msg_id, timeout=1.0):
        evt = threading.Event()
        with self.lock:
            self.pending[msg_id] = evt
            self.replies[msg_id] = None

        is_set = self.pending[msg_id].wait(timeout = timeout)
        if is_set:
            return self.replies[msg_id]
        return None
        

    def handle_reply(self, body):
        in_reply_to = body["in_reply_to"]
        with self.lock:
            if in_reply_to in self.pending:
                self.replies[in_reply_to] = body
                self.pending[in_reply_to].set()

    def proxy_reply(self, message, msg_id):        
        result = self.wait_reply(msg_id, 1.0)
        if result is None:
            self.reply(message, {"type": "error", "code": 0, "text": "RPC timeout"})
        else:
            self.reply(message, {"type": "proxy_ok", "result": result})            
    

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
            msg_id = node.send_rpc(body["target"], body["inner"])
            thread = threading.Thread(target = node.proxy_reply, args = (message, msg_id))
            thread.start()
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
