#!/usr/bin/env python3
import sys
import json
import time
import random

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0

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

    def compute_backoff_delay(self, attempt, base_delay=0.1, max_delay=2.0):
        # TODO: Calculate exponential backoff delay with jitter
        # attempt starts at 0
        # Return delay in seconds
        pass

    def get_delay_schedule(self, max_retries=5, base_delay=0.1, max_delay=2.0):
        # TODO: Return list of delays for each retry attempt
        # Each delay should use compute_backoff_delay
        pass

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "compute_backoff":
            # The request body has: max_retries, base_delay.
            # Reply with "compute_backoff_ok": schedule_ms, total_ms, retries.
            # Return the delay schedule for visualization
            # TODO: Compute and return the schedule
            pass
        elif msg_type == "backoff_relay":
            # The request body has: target, payload, max_retries, base_delay.
            #   "backoff_relay_ok": attempts, total_delay_ms.
            #   "error": code, text.
            # TODO: Send the first attempt to the target here, then wait for a reply
            # and retry with backoff on a new thread
            pass
        else:
            # TODO: Match replies to pending requests by in_reply_to
            pass

if __name__ == "__main__":
    main()

# TODO: Write a comment explaining why exponential backoff helps under high load
# (at least 100 words)
