#!/usr/bin/env python3
import sys
import json
from datetime import datetime
from collections import deque

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.log_buffer = deque(maxlen=100)

    def log_message(self, direction, src, dest, msg_type):
        # TODO: Add a log entry to the buffer
        # Include timestamp, direction, src, dest, msg_type
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%dT%H:%M:%S')

        if len(self.log_buffer) >= self.log_buffer.maxlen:
            self.log_buffer.popleft()
        self.log_buffer.append({"ts": now_str, "dir": direction, "src": src, "dest": dest, "msg_type":msg_type})

    def send(self, dest, body):
        body["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        # TODO: Log the sent message
        self.log_message("SENT", message["src"], message["dest"], message["body"]["type"])
        print(json.dumps(message), flush=True)

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
        
    def get_recent_logs(self, count):
        # TODO: Return the most recent 'count' log entries
        logs = []

        for log in reversed(self.log_buffer):
            logs.append(log)
            if len(logs) == count:
                break

        logs.reverse()
        return logs

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)

        node.log_message("RECV", message["src"], message["dest"], message["body"]["type"])

        body = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "get_log":
            # The request body has: count.
            # Reply with "get_log_ok": entries.
            # TODO: Return recent log entries
            logs = node.get_recent_logs(body["count"])
            node.reply(message, {"type": "get_log_ok", "entries": logs})
            pass

if __name__ == "__main__":
    main()
