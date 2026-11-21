
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
        required_fields = ["src", "dest", "body"]
        for field in required_fields:
            if field not in message:
                print(f"Missing field: {field}", file=sys.stderr)
                return False

        body = message["body"]
        required_body_fields = ["type", "msg_id"]
        for field in required_body_fields:
            if field not in body:
                print(f"Missing field in body: {field}", file=sys.stderr)
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
        if node.validate_message(message) == False:
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
