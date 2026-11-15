#!/usr/bin/env python3
import sys
import json

class MessageBody:
    def __init__(self, msg_type, msg_id=None, in_reply_to=None, **extra):
        self.type = msg_type
        self.msg_id = msg_id
        self.in_reply_to = in_reply_to
        self.extra = extra

    def to_dict(self):
        d = {"type": self.type}
        d.update(self.extra)
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        if self.msg_id is not None:
            d["msg_id"] = self.msg_id
        return d

    @classmethod
    def from_dict(cls, data):
        # TODO: Parse a dictionary into a MessageBody
        # Validate that 'type' field exists
        if "type" not in data:
            return None

        body = MessageBody(data["type"])

        if "msg_id" in data:
            body.msg_id = data["msg_id"]
        if "in_reply_to" in data:
            body.in_reply_to = data["in_reply_to"]

        body.extra ={}
        for key in data:
            if key != "msg_id" and key != "in_reply_to" and key != "type":
                body.extra[key] = data[key]

        return body
        

class Message:
    def __init__(self, src, dest, body):
        self.src = src
        self.dest = dest
        self.body = body

    def to_json(self):
        dict = {}
        dict["src"] = self.src
        dict["dest"] = self.dest
        dict["body"] = self.body.to_dict()
        return dict

    @classmethod
    def from_json(cls, json_str):
        # TODO: Deserialize from JSON string
        # Validate required fields: src, dest, body, body.type
        try:
            json_obj = json.loads(json_str)
    
            if "src" not in json_obj:
                return None
    
            if "dest" not in json_obj:
                return None
    
            if "body" not in json_obj:
                return None
    
            body = json_obj["body"]
            msg_body = MessageBody.from_dict(body)
    
            if msg_body is None:
                return None
    
            return Message(json_obj["src"], json_obj["dest"], msg_body)
        except (ValueError, KeyError) as e:
            print(f"Invalid message: {e}", file=sys.stderr)

        return None
            

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0

    def send(self, dest, body_dict):
        body_dict["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        msg = Message(self.node_id, dest, MessageBody.from_dict(body_dict))
        print(json.dumps(msg.to_json()), flush=True)

    def reply(self, request_msg, body_dict):
        body_dict["in_reply_to"] = request_msg.body.msg_id
        self.send(request_msg.src, body_dict)

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = Message.from_json(line)
        except (ValueError, KeyError) as e:
            print(f"Invalid message: {e}", file=sys.stderr)
            continue

        if msg is None:
            print(f"Invalid message", file=sys.stderr)
            continue

        if msg.body.type == "init":
            node.node_id = msg.body.extra["node_id"]
            node.node_ids = msg.body.extra["node_ids"]
            node.reply(msg, {"type": "init_ok"})
        elif msg.body.type == "echo":
            node.reply(msg, {"type": "echo_ok", "echo": msg.body.extra["echo"]})
        elif msg.body.type == "validate":
            # The request body has: payload.
            # Reply with "validate_ok": valid, fields.
            # TODO: Parse the payload and report found fields
            payload_msg = Message.from_json(msg.body.extra["payload"])
            if payload_msg is not None:
                fields = ["src", "dest", "body.type"]
                if payload_msg.body.msg_id is not None:
                    fields.append("body.msg_id")
                if payload_msg.body.in_reply_to is not None:
                    fields.append("body.in_reply_to")
                for key in payload_msg.body.extra:
                    fields.append(f"body.{key}")
                node.reply(msg, {"type": "validate_ok", "valid": True, "fields": fields})
            else:
                node.reply(msg, {"type": "validate_ok", "valid": False, "fields": []})

if __name__ == "__main__":
    main()
