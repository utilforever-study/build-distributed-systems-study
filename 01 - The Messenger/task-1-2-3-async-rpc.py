#!/usr/bin/env python3
import sys
import json

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.callbacks = {}  # msg_id -> callback function

    def send(self, dest, body):
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
        msg_id = self.send(dest, body)
        self.callbacks[msg_id] = callback
        return callback

    def handle_reply(self, body):
        callback = self.callbacks.pop(body.get("in_reply_to"), None)
        if callback is not None:
            callback(body)

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
            values = body["values"]
            if not values:
                empty_result = []
                m = {
                    "type" : "batch_echo_ok",
                    "results" : empty_result
                }
                node.reply(message, m)
                continue
            results = [None] * len(values)
            remaining = [len(values)] # unbound local error

            def make_callback(i, message = message, results = results, remaining = remaining):
                def callback(reply_body):
                    results[i] = reply_body["echo"]
                    remaining[0] -= 1
                    if remaining[0] == 0:
                        m = {
                            "type" : "batch_echo_ok",
                            "results" : results
                        }
                        node.reply(message, m)
                return callback

            for i, v in enumerate(values):
                m = {
                    "type" : "echo",
                    "echo" : v
                }
                node.async_rpc(node.node_id, m, make_callback(i))
            
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
