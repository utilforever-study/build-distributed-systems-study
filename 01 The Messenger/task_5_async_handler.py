#!/usr/bin/env python3
import sys
import json
import threading
import time
from queue import Queue

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.message_queue = Queue()
    
    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        # TODO: Thread-safe output
        print(json.dumps(message), flush=True)
    
    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
    
    def handle_message(self, message):
        body = message["body"]
        type = body["type"]

        if type == "init":
            self.node_id = body["node_id"]
            self.node_ids = body["node_ids"]
            self.reply(message, {"type": "init_ok"})
        elif type == "echo":
            self.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif type == "wait":
            self.reply(message, {"type": "wait_ok", "key": body["key"]})
        elif type == "release":
            self.reply(message, {"type": "release_ok", "key": body["key"]})
        pass

class ThreadPoolManager:
    def __init__(self):
        self.max_thread = 0
        self.threads = []
        self.q = Queue()
        self.lock = threading.Lock()
        
    def initialize(self, max_thread):
        self.max_thread = max_thread

    def loop(self):
        while True:
            alive_threads = []
            for t in self.threads:
                if t.is_alive():
                    alive_threads.append(t)
            self.threads = alive_threads

            print(len(self.threads), end = " ", flush=True)

            while not self.q.empty() and len(self.threads) < self.max_thread:
                work_func = self.q.get()
                new_thread = threading.Thread(target=work_func)
                self.threads.append(new_thread)
                new_thread.start()

            time.sleep(0.1)

    def start(self):
        pool_thread = threading.Thread(target=self.loop, daemon=True)
        pool_thread.start()

    def add_work(self, work):
        self.q.put(work)

    def is_complete(self):
        return self.q.empty() and not self.threads
        
def main():
    node = Node()
    thread_pool = ThreadPoolManager()
    thread_pool.initialize(10)
    thread_pool.start()
    
    for line in sys.stdin:
        message = json.loads(line)
        thread_pool.add_work(lambda m=message: node.handle_message(m))

    while not thread_pool.is_complete():
        time.sleep(0.1)

if __name__ == "__main__":
    main()
