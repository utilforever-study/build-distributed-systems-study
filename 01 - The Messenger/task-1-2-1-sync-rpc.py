#!/usr/bin/env python3
import sys
import json
import threading

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.pending = {}  # msg_id -> threading.Event
        self.replies = {}  # msg_id -> reply body

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
        # TODO: Send the message and register a waiter for it
        # 1. Create a threading.Event and store it in self.pending under the msg_id
        # 2. Make sure it is registered before a reply can be handled
        # 3. Return the msg_id
        msg_id = self.send(dest, body) # send한 다음에
        with self.lock:
            self.pending[msg_id] = threading.Event() # send에 대한 응답 기다리기 위해 event만들고 넣음
        return msg_id

    def wait_reply(self, msg_id, timeout=1.0):
        # TODO: Block until the reply arrives or the timeout passes
        # Return the reply body, or None on timeout; remove the pending entry either way
        with self.lock:
            event = self.pending[msg_id] # send한거 뽑아서 timeout만큼 기다림
        event.wait(timeout)
        with self.lock:
            self.pending.pop(msg_id, None) # timeout 끝나면 pending에서 뺌
            return self.replies.pop(msg_id, None) #응답온거 return

    def handle_reply(self, body):
        # TODO: Check if this is a reply to a pending RPC
        # Match using in_reply_to field, store the body and wake the waiter
        in_reply_to = body.get("in_reply_to")
        with self.lock:
            event = self.pending.get(in_reply_to) # send된거에 reply하기 위해 해당 event 가져옴
            if event is None: # 없으면 그냥 return
                return
            self.replies[in_reply_to] = body 
        event.set()

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
        elif msg_type == "proxy":
            #   "error": code, text.
            #   "proxy_ok": result.
            # TODO: Forward the inner message to the target with send_rpc here,
            # then wait for the reply and answer the caller on a new thread
            target = body.get("target")
            inner = dict(body.get("inner")) # send에서 body[msg_id] = ... 해서 복사로 바꿈
            msg_id = node.send_rpc(target, inner) # target에 inner보내면 msg_id return
            def process_proxy(node, message, msg_id):
                result = node.wait_reply(msg_id) # msg_id에 대한 응답 기다리고
                if result is None: # timeout 되면 error
                    e = {
                        "type" : "error",
                        "code" : 0,
                        "text" : "RPC timeout"
                    }
                    node.reply(message, e)
                else:
                    m = {
                        "type" : "proxy_ok",
                        "result" : result
                    }
                    node.reply(message, m)
            threading.Thread(target = process_proxy, args = (node, message, msg_id)).start()
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
