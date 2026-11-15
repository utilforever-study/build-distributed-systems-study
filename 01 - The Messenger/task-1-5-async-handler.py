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
        self.message_lock = threading.Lock()
        self.dict_lock = threading.Lock()
        self.wait_dict = {}
    
    def send(self, dest, body):
        with self.message_lock:
            body["msg_id"] = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        with self.message_lock:
            print(json.dumps(message), flush=True)
        
    
    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
    
    def handle_message(self, message):
        # TODO: Handle message in separate thread
        # The tests send these body types:
        #   "init": save body.node_id and body.node_ids, reply with "init_ok".
        #   "echo" (body has echo): reply with "echo_ok": echo.
        #   "wait" (body has key): reply with "wait_ok": key once that key has been
        #       released (possibly before the wait arrived); keep answering
        #       other messages meanwhile.
        #   "release" (body has key): reply with "release_ok": key.
        if(message["body"].get("type") == "init"):
            self.node_id = message["body"].get("node_id")
            self.node_ids = message["body"].get("node_ids")            
            self.reply(message, {"type" : "init_ok"})
        elif(message["body"].get("type") == "echo"):
            response = {
                "type" : "echo_ok",
                "echo" : message["body"].get("echo")
            }
            self.reply(message, response)
        elif(message["body"].get("type") == "wait"):
            key = message["body"].get("key")
            response = {
                "type" : "wait_ok",
                "key" : key
            }
            with self.dict_lock:
                if key not in self.wait_dict:
                    self.wait_dict[key] = threading.Event()
                event = self.wait_dict[key]
            event.wait()
            self.reply(message, response)
    
        elif(message["body"].get("type") == "release"):
            key = message["body"].get("key")
            response = {
                "type" : "release_ok",
                "key" : key
            }
            with self.dict_lock:
                if key not in self.wait_dict:
                    self.wait_dict[key] = threading.Event()
                event = self.wait_dict[key]
            event.set()
            self.reply(message, response)

def main():
    node = Node()
    
    # TODO: Implement concurrent message handling
    # 1. Read messages in main thread
    # 2. Dispatch to handlers concurrently
    
    for line in sys.stdin:
        message = json.loads(line)
        # Currently synchronous - make this concurrent
        t = threading.Thread(target = node.handle_message, args = (message,))
        t.start()
        # node.handle_message(message)

if __name__ == "__main__":
    main()
