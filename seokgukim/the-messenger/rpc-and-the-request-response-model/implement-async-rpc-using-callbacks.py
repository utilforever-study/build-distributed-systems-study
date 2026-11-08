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
        # TODO: Send message and register callback for the reply
        # The callback should be called with the reply body when it arrives
        msg_id = self.send(dest, body)
        self.callbacks[msg_id] = callback

    def handle_reply(self, body):
        # TODO: Look up callback by in_reply_to and invoke it
        msg_id = body["in_reply_to"]
        callback = self.callbacks.pop(msg_id, None)
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
            # The request body has: values.
            # Reply with "batch_echo_ok": results.
            # TODO: Send async echo RPCs for each value, collect results
            results = [None] * len(body["values"])
            remaining = [len(body["values"])]
            def get_callback(idx, request = message):
                def callback(reply_body):
                    results[idx] = reply_body["echo"]
                    remaining[0] -= 1
                    if remaining[0] == 0:
                        node.reply(request, {"type": "batch_echo_ok", "results": results}
                        )
                return callback

            for i, value in enumerate(body["values"]):
                node.async_rpc(node.node_id, {"type": "echo", "echo": value}, get_callback(i))
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
