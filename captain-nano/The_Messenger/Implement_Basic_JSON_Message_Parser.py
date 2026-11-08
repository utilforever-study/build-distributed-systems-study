#!/usr/bin/env python3
import json
import sys


class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
    
    def send(self, dest, body):
        # TODO: Implement message sending
        send_body = body.copy()
        send_body["msg_id"] = self.next_msg_id
        self.next_msg_id += 1

        message = {
            "src": self.node_id,
            "dest": dest,
            "body": send_body,
        }

        print(json.dumps(message), flush=True)
        
    
    def reply(self, request, body):
        # TODO: Implement reply with in_reply_to
        reply_body = body.copy()
        reply_body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], reply_body)


def main():
    node = Node()
    
    for line in sys.stdin:
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]
        
        if msg_type == "init":
            # TODO: Handle init message
            # 1. Store node_id and node_ids
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            # 2. Reply with init_ok
            node.reply(message, {"type": "init_ok"})


if __name__ == "__main__":
    main()
