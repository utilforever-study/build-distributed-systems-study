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

    def handle_reply(self, body):
        callback = self.callbacks.pop(body.get("in_reply_to"), None)
        if callback is not None:
            callback(body)

    def handle_batch_echo(self, request):
        values = request["body"]["values"]
        if not values:
            self.reply(request, {"type": "batch_echo_ok", "results": []})
            return
        
        results = [ None for _ in values ]
        remaining = len(values)

        for index, value in enumerate(values):
            def on_echo(reply_body, index=index):
                nonlocal remaining
                results[index] = reply_body["echo"]
                remaining -= 1
                if remaining == 0:
                    self.reply(request, {"type": "batch_echo_ok", "results": results})

            self.async_rpc(self.node_id, {"type": "echo", "echo": value}, on_echo)


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
            node.handle_batch_echo(message)          
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
