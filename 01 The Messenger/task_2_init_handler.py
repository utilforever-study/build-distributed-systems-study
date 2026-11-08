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

        message = {"src": self.node_id, "dest": dest, "body": body}
        
        print(json.dumps(message), flush=True)
        pass
    
    def reply(self, request, body):
        dest = request["src"]
        req_msg_id = request["body"]["msg_id"]
        body["in_reply_to"] = req_msg_id
        
        self.send(dest, body)
        pass

def main():
    node = Node()
    
    for line in sys.stdin:
        message = json.loads(line)
        
        body = message["body"]
        msg_type = body["type"]
        
        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
            pass

if __name__ == "__main__":
    main()
