#!/usr/bin/env python3
import sys
import json
import threading
from queue import Queue

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.events = {}
    
    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        with self.lock:
            print(json.dumps(message), flush=True)
    
    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
    
    def handle_message(self, message):
        body = message["body"]
        _type = body["type"]

        if _type == "init":
            with self.lock:
                self.node_id = body["node_id"]
                self.node_ids = body["node_ids"]
            self.reply(message, {"type": "init_ok"})

        elif _type == "echo":
            self.reply(message, {"type": "echo_ok", "echo": body["echo"]})

        elif _type == "wait":
            key = body['key']

            if key in self.events:
                self.events.pop(key)

            self.events[key] = threading.Event()
            self.events[key].wait()
            self.reply(message, {"type": "wait_ok", "key": key})

        elif _type == "release":
            key = body["key"]
            self.reply(message, {"type": "release_ok", "key": key})
            self.events[body["key"]].set()

def main():
    node = Node()

    for line in sys.stdin:
        message = json.loads(line)
        threading.Thread(target=node.handle_message, args=(message, )).start()
        

if __name__ == "__main__":
    main()