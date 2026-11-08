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
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
    
    def validate_message(self, message):
        field_list = ('src', 'dest', 'body')
        require_msg_id_type_list = ("echo", "init")

        for field in field_list:
            if not field in message:
                raise KeyError(f"field '{field}' not found")

        body = message["body"]
        
        if not isinstance(body, dict) or not "type" in body:
            raise KeyError(f"field 'type' not found in 'body'")

        if any(types in body for types in require_msg_id_type_list) and not "msg_id" in body:
            raise KeyError(f"field 'msg_id' not found in 'body', type = {body['type']}")
       
def main():
    node = Node()
    
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            continue
        
        try:
            node.validate_message(message)
        except KeyError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            continue
        
        body = message["body"]
        msg_type = body["type"]
        
        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})

if __name__ == "__main__":
    main()

