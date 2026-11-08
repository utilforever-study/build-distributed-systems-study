#!/usr/bin/env python3
import sys
import json

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
    
    def send(self, dest, body):
        # TODO: Implement message sending
        body["msg_id"] = self.next_msg_id
        self.next_msg_id += 1

        message = {
            "src": self.node_id,
            "dest": dest,
            "body": body
        }

        print(json.dumps(message))
    
    def reply(self, request, body):
        # TODO: Implement reply with in_reply_to
        dest = request.get("src", None)
        if dest is None:
            print(f"No src for request {request}")
            return

        msg_id = body.get("msg_id", None)
        if msg_id is None:
            print(f"No msg_id for request {request}")
            return

        message = {
            "type": "init_ok",
            "in_reply_to": msg_id
        }

        self.send(dest, message)
        pass


def main():
    node = Node()
    
    for line in sys.stdin:
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]
        
        if msg_type == "init":
            # TODO: Handle init message
            # 1. Store node_id and node_ids
            # 2. Reply with init_ok
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]

            node.reply(message, body)

            pass

if __name__ == "__main__":
    main()

