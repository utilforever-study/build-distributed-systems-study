#!/usr/bin/env python3
import sys
import json

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
    
    def send(self, dest, body):
        body["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        msg = {"src" : self.node_id, "dest" : dest, "body" : body}
        print(json.dumps(msg), flush = True)
    
    def reply(self, request, body):
        dest = request["src"]
        in_reply_to = body["msg_id"]
        msg = {"type" : "init_ok", "in_reply_to" : in_reply_to}
        self.send(dest, msg)

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
            node.node_id = message["body"].get("node_id")
            node.node_ids = message["body"].get("node_ids")
            node.reply(message, body)
            

if __name__ == "__main__":
    main()
