#!/usr/bin/env python3
import sys
import json
import time
import random
import threading

MAX_DELAY = 2

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.pending = {}
        self.replies = {}
        self.lock = threading.Lock();

    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            msg_id = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        print(json.dumps(message), flush=True)
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def send_rpc(self, dest, body):
        event = threading.Event()
        with self.lock:
            msg_id = self.next_msg_id
            self.next_msg_id += 1
            self.pending[msg_id] = event
            body["msg_id"] = msg_id
            print(json.dumps({"src": self.node_id, "dest": dest, "body": body}), flush=True)
        return msg_id

    def compute_backoff_delay(self, attempt, base_delay=0.1, max_delay=2.0):
        default_delay = base_delay * 1000 * pow(2, attempt)
        jitter = random.randint(0, default_delay * 0.1)
        delay = min(MAX_DELAY * 1000, default_delay + jitter)
        return delay

    def get_delay_schedule(self, max_retries=5, base_delay=0.1, max_delay=2.0):
        schedule_ms = []
        for attempt in range(0, max_retries):
            schedule_ms.append(self.compute_backoff_delay(attempt, base_delay, max_delay))
        return schedule_ms

    def send_compute_backoff(self, message):
        body = message["body"]
        schedule_ms = self.get_delay_schedule(body["max_retries"])
        total_ms = sum(schedule_ms)
        self.reply(message, {"type": "compute_backoff_ok", "schedule_ms": schedule_ms, "total_ms":  total_ms, "retries": len(schedule_ms)})

    def wait_reply(self, msg_id, timeout):
        with self.lock:
            event = self.pending[msg_id]
        event.wait(timeout=timeout)
        with self.lock:
            self.pending.pop(msg_id, None)
            return self.replies.pop(msg_id, None)

    def rpc_with_retry(self, dest, body, first_msg_id, max_retries):
        attempts = 0
        delay_schedule = self.get_delay_schedule(max_retries)
        delay_time = 0

        while attempts < max_retries:
            attempts += 1
            msg_id = self.send_rpc(dest, body["payload"])
            result = self.wait_reply(msg_id, delay_schedule[attempts - 1] / 1000)
            delay_time += delay_schedule[attempts - 1]
            if result is not None:
                return {"type": "backoff_relay_ok", "attempts": attempts, "total_delay_ms": delay_time}
        
        return {"type": "error", "code": 0, "text": f"RPC failed after {max_retries} attempts"}
        

    def proxy_reply(self, message, msg_id):
        body = message["body"]
        result = self.rpc_with_retry(body["target"], body, msg_id, body["max_retries"])
        self.reply(message, result)

    def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        with self.lock:
            if reply_to is not None and reply_to in self.pending:
                self.replies[reply_to] = body
                self.pending[reply_to].set()

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
            node.send_compute_backoff(message)
        elif msg_type == "backoff_relay":
            t = threading.Thread(target=node.proxy_reply, args=(message, body["msg_id"], ))
            t.start()
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()

# TODO: Write a comment explaining why exponential backoff helps under high load
# (at least 100 words)
