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
    
    def reply(self, request, body):
        if not self.validate_message(request):
            print(f"Invalid JSON: invalid message", file=sys.stderr)
            return
            
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
    
    def validate_message(self, message):
        body = message["body"]
        msg_type = body["type"]
        need_reply = msg_type == "init" or msg_type == "echo"

        if need_reply:
            return "msg_id" in body

        return True

def main():
    node = Node()
    
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            continue
        
        if not "src" in message:
            print(f"Invalid JSON: field \"src\" does not exist", file=sys.stderr)
            continue

        if not "dest" in message:
            print(f"Invalid JSON: field \"dest\" does not exist", file=sys.stderr)
            continue

        if not "body" in message:
            print(f"Invalid JSON: field \"type\" does not exist", file=sys.stderr)
            continue
        
        body = message["body"]
        if not "type" in body:
            print(f"Invalid JSON: field \"body\" does not exist in body", file=sys.stderr)
            continue
            
        msg_type = body["type"]
        
        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})

if __name__ == "__main__":
    main()
