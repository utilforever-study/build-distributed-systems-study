#!/usr/bin/env python3
import sys
import json
import time

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.callbacks = {}      # msg_id -> callback
        self.callback_times = {} # msg_id -> registration timestamp
        self.reap_threshold = 2.0  # seconds

    def send(self, dest, body):
        body["msg_id"] = self.next_msg_id
        msg_id = self.next_msg_id
        self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        print(json.dumps(message), flush=True)
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def async_rpc(self, dest, body, callback):
        msg_id = self.send(dest, body)
        self.callbacks[msg_id] = callback
        self.callback_times[msg_id] = time.time()

    def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        if reply_to is not None and reply_to in self.callbacks:
            callback = self.callbacks.pop(reply_to)
            self.callback_times.pop(reply_to, None)
            callback(body)

    def reap_expired_callbacks(self):
        now = time.time()
        expired = [msg_id for msg_id, t in self.callback_times.items() if (now - t) > self.reap_threshold]
        for msg_id in expired:
            callback = self.callbacks.pop(msg_id, None)
            self.callback_times.pop(msg_id, None)
            if callback is not None:
                callback(None)
        return len(expired)

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]

        # Reap before processing each message
        node.reap_expired_callbacks()

        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "pending_count":
            m = {
                "type" : "pending_count_ok", 
                "count" : len(node.callbacks)
            }
            node.reply(message, m)
        elif msg_type == "send_fire_forget":
            node.async_rpc(body["target"], dict(body["payload"]), lambda reply_body: None)
            m = {
                "type": "send_fire_forget_ok", 
                "pending": len(node.callbacks)
            }
            node.reply(message, m)
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
