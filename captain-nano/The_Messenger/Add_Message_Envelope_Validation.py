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
        # TODO: Validate message structure
        # Return True if valid, False otherwise
        # Log errors to stderr
        if not isinstance(message, dict):
            print("Invalid message", file=sys.stderr)
            return False

        for field in ("src", "dest"):
            if not isinstance(message.get(field), str):
                print("Invalid message", file=sys.stderr)
                return False

        body = message.get("body")
        if not isinstance(body, dict):
            print("Invalid message", file=sys.stderr)
            return False

        msg_type = body.get("type")
        if not isinstance(msg_type, str):
            print("Invalid message", file=sys.stderr)
            return False

        if msg_type in ("init", "echo") and type(body.get("msg_id")) is not int:
            print("Invalid message", file=sys.stderr)
            return False

        if msg_type == "init":
            if not isinstance(body.get("node_id"), str):
                print("Invalid message", file=sys.stderr)
                return False;

            node_ids = body.get("node_ids")
            if not isinstance(node_ids, list) or not all(isinstance(node_id, str) for node_id in node_ids):
                print("Invalid message", file=sys.stderr)
                return False

        elif msg_type == "echo":
            if "echo" not in body:
                print("Invalid message", file=sys.stderr)
                return False

        return True
        

def main():
    node = Node()
    
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            continue
        
        # TODO: Validate message before processing
        if not node.validate_message(message):
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
