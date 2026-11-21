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
        if self.msg_id is not None:
            d["msg_id"] = self.msg_id
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, data):
        # TODO: Parse a dictionary into a MessageBody
        # Validate that 'type' field exists
        pass
        msg_type = data.get("type")
        if msg_type is None:
            raise ValueError("Message type is required")
        extra = {}
        for k, v in data.items():
            if k == "type":
                continue
            extra[k] = v
        return cls(msg_type, **extra)

class Message:
    def __init__(self, src, dest, body):
        self.src = src
        self.dest = dest
        self.body = body

    def to_json(self):
        # TODO: Serialize to JSON string
        if not all(isinstance(value, str) and value.isalnum() for value in (self.src, self.dest)):
            return json.dumps({"src": self.src, "dest": self.dest, "body": self.body.to_dict()})
        pass
        body_dump = json.dumps(self.body.to_dict())
        return f"{{\"src\": \"{self.src}\", \"dest\": \"{self.dest}\", \"body\": {body_dump}}}"

    @classmethod
    def from_json(cls, json_str):
        # TODO: Deserialize from JSON string
        # Validate required fields: src, dest, body, body.type
        pass
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise ValueError("Message must be an object")
        data_src = data.get("src")
        data_dest = data.get("dest")
        data_body = data.get("body")
        if data_src is None or data_dest is None or data_body is None:
            raise ValueError("Missing required fields")
        if not isinstance(data_body, dict):
            raise ValueError("Message body must be an object")
        data_body_type = data_body.get("type")
        if data_body_type is None:
            raise ValueError("Missing required field 'type' in body")
        return Message(data_src, data_dest, MessageBody.from_dict(data_body))

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0

    def send(self, dest, body_dict):
        body_dict["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        msg = Message(self.node_id, dest, MessageBody.from_dict(body_dict))
        print(msg.to_json(), flush=True)

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
            pass
            try:
                payload = json.loads(msg.body.extra.get("payload"))
            except (TypeError, ValueError):
                payload = None
            valid = isinstance(payload, dict)
            fields = []
            if valid:
                fields = [key for key in ("src", "dest") if key in payload]
                body = payload.get("body")
                if isinstance(body, dict):
                    fields.extend("body." + key for key in ("type", "msg_id") if key in body)
            node.reply(msg, {"type": "validate_ok", "valid": valid, "fields": fields})

if __name__ == "__main__":
    main()
