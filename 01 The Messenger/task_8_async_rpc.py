#!/usr/bin/env python3
import sys
import json
import threading

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.callbacks = {}  # msg_id -> callback function
        self.lock = threading.Lock()

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

    def async_rpc(self, dest, body, callback):
        msg_id = self.send(dest, body);
        with self.lock:
            self.callbacks[msg_id] = callback;

    def handle_reply(self, body):
        reply_to = body["in_reply_to"]
        callback = self.callbacks[reply_to]
        callback(body)
        
    def batch_echo(self, message, body):
        values = body["values"]
        threads = []
        result = []
        
        remain = len(values)

        def callback(body):
            nonlocal remain
            
            with self.lock:
                if body["type"] == "echo_ok":
                    result.append(body["echo"])
                    remain -= 1

            if remain <= 0 and len(result) > 0:
                self.reply(message, {"type": "batch_echo_ok", "results": sorted(result)})

        for value in values:
            t = threading.Thread(target = self.async_rpc, args=(self.node_id, {"type": "echo", "echo": value}, callback))
            t.start()
            threads.append(t)

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
        elif msg_type == "batch_echo":
            node.batch_echo(message, body);
        elif msg_type == "echo_ok":
            node.handle_reply(body)
        else:
            pass

if __name__ == "__main__":
    main()
