#!/usr/bin/env python3
import json
import sys


def main():
    # Each input line is one JSON message. Blank and malformed lines are skipped.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as error:
            continue

        # Your code here: print "PARSED: src|dest|body_type".
        # message["src"], message["dest"] and message["body"] hold the fields.
        # When the body has no "type", print "unknown" instead.
        src = message.get("src")
        dest = message.get("dest")
        body = message.get("body")
        type = body.get("type", "unknown")
        print(f"PARSED: {src}|{dest}|{type}")

if __name__ == "__main__":
    main()