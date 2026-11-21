#!/usr/bin/env python3
import sys
import json
import threading
from queue import Queue

msg_queue = Queue(maxsize=64)


def worker(node):
    while True:
        message = msg_queue.get()
        try:
            if message is None:
                return
            if not node.validate_message(message):
                continue

            body = message["body"]
            if body["type"] == "init":
                node.handle_init(body)
                node.reply(message, {"type": "init"})
            elif node.node_id is None:
                print("No node_id set", file=sys.stderr)
            elif body["type"] == "echo":
                node.reply(message, {"type": "echo", "echo": body["echo"]})
            elif body["type"] == "wait":
                key = body["key"]
                if key in node.released_keys:
                    node.reply(message, {"type": "wait", "key": key})
                else:
                    node.pending_waits.setdefault(key, []).append(message)
            elif body["type"] == "release":
                key = body["key"]
                node.released_keys.add(key)
                node.reply(message, {"type": "release", "key": key})
                for waiting in node.pending_waits.pop(key, []):
                    node.reply(waiting, {"type": "wait", "key": key})
        finally:
            msg_queue.task_done()


class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.released_keys = set()
        self.pending_waits = {}

    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            self.next_msg_id += 1
            message = {"src": self.node_id, "dest": dest, "body": body}
            print(json.dumps(message), flush=True)

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        body["type"] = f'{body["type"]}_ok'
        self.send(request["src"], body)

    def validate_message(self, message):
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

    def handle_init(self, body):
        with self.lock:
            self.node_id = body["node_id"]
            self.node_ids = body["node_ids"]

    def handle_message(self, message):
        # TODO: Handle message in separate thread
        # The tests send these body types:
        #   "init": save body.node_id and body.node_ids, reply with "init_ok".
        #   "echo" (body has echo): reply with "echo_ok": echo.
        #   "wait" (body has key): reply with "wait_ok": key once that key has been
        #       released (possibly before the wait arrived); keep answering
        #       other messages meanwhile.
        #   "release" (body has key): reply with "release_ok": key.
        msg_queue.put(message)


def main():
    node = Node()
    thread = threading.Thread(target=worker, args=(node,))
    thread.start()
    try:
        for line in sys.stdin:
            message = json.loads(line)
            node.handle_message(message)
    finally:
        msg_queue.put(None)
        thread.join()


if __name__ == "__main__":
    main()
