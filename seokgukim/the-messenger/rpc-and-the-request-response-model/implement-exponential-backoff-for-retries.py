#!/usr/bin/env python3
import sys
import json
import time
import random
import threading

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.RLock()
        self.pending = {}

    def send(self, dest, body):
        with self.lock:
            msg_id = self.next_msg_id
            self.next_msg_id += 1
            message = {
                "src": self.node_id, "dest": dest,
                "body": dict(body, msg_id=msg_id),
            }
            print(json.dumps(message), flush=True)
            return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def compute_backoff_delay(self, attempt, base_delay=0.1, max_delay=2.0):
        delay = min(base_delay * 2 ** attempt, max_delay)
        return min(delay + random.uniform(0, delay * 0.1), max_delay)

    def get_delay_schedule(self, max_retries=5, base_delay=0.1, max_delay=2.0):
        return [
            self.compute_backoff_delay(attempt, base_delay, max_delay)
            for attempt in range(max_retries)
        ]

    def send_rpc(self, dest, body):
        # Register before writing so even an immediate reply finds its waiter.
        with self.lock:
            msg_id = self.next_msg_id
            self.pending[msg_id] = {"event": threading.Event(), "reply": None}
            return self.send(dest, body)

    def wait_reply(self, msg_id, timeout):
        with self.lock:
            pending = self.pending[msg_id]
        pending["event"].wait(timeout)
        with self.lock:
            self.pending.pop(msg_id)
            return pending["reply"]

    def handle_reply(self, body):
        with self.lock:
            pending = self.pending.get(body.get("in_reply_to"))
            if pending is not None:
                pending["reply"] = body
                pending["event"].set()

    def rpc_with_backoff(self, dest, body, first_msg_id,
                         max_retries=5, base_delay=0.1):
        total_delay_ms = 0
        for attempt in range(max_retries):
            delay = self.compute_backoff_delay(attempt, base_delay)
            total_delay_ms += int(delay * 1000)
            msg_id = first_msg_id if attempt == 0 else self.send_rpc(dest, body)
            result = self.wait_reply(msg_id, delay)
            if result is not None:
                return result, attempt + 1, total_delay_ms
        return None, max_retries, total_delay_ms

    def finish_relay(self, request, first_msg_id):
        body = request["body"]
        result, attempts, total_delay_ms = self.rpc_with_backoff(
            body["target"], body["payload"], first_msg_id,
            body.get("max_retries", 5), body.get("base_delay", 0.1),
        )
        if result is None:
            self.reply(request, {
                "type": "error", "code": 0,
                "text": f"RPC failed after {attempts} attempts",
            })
        else:
            self.reply(request, {
                "type": "backoff_relay_ok", "attempts": attempts,
                "total_delay_ms": total_delay_ms,
            })


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
            max_retries = body.get("max_retries", 5)
            schedule_ms = [
                int(delay * 1000) for delay in node.get_delay_schedule(
                    max_retries, body.get("base_delay", 0.1)
                )
            ]
            node.reply(message, {
                "type": "compute_backoff_ok", "schedule_ms": schedule_ms,
                "total_ms": sum(schedule_ms), "retries": max_retries,
            })
        elif msg_type == "backoff_relay":
            max_retries = body.get("max_retries", 5)
            if max_retries <= 0:
                node.reply(message, {
                    "type": "error", "code": 0,
                    "text": f"RPC failed after {max_retries} attempts",
                })
                continue
            first_msg_id = node.send_rpc(body["target"], body["payload"])
            threading.Thread(
                target=node.finish_relay, args=(message, first_msg_id)
            ).start()
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
