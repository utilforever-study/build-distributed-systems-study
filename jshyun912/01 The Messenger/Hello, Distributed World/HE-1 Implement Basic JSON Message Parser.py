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
            print(f"Skipping malformed line: {error}", file=sys.stderr)
            continue

        print(f"PARSED: {message['src']}|{message['dest']}|{message['body']['type']  if 'type' in message['body'] else 'unknown'}")

if __name__ == "__main__":
    main()
