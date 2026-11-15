#!/usr/bin/env python3
import sys
import json

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
    
    def send(self, dest, body):
        message = dict()

        message["src"] = self.node_id
        message["dest"] = dest
        message["body"] = body

        print(json.dumps(message))

    
    def reply(self, request, body):
        message = dict()

        message["type"] = "init_ok"
        message["in_reply_to"] = body["msg_id"]
        message["msg_id"] = self.next_msg_id

        self.next_msg_id += 1

        self.send(request, message)

def main():
    node = Node()
    
    for line in sys.stdin:
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]
        
        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message["src"], body)


if __name__ == "__main__":
    main()
