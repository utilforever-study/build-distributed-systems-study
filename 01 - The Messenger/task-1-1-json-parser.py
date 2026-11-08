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
        if message["body"].get("type") == None:
            print("PARSED:", message["src"] + '|' + message["dest"] + '|' + "unknown")
        else:
            print("PARSED:", message["src"] + '|' + message["dest"] + '|' + message["body"]["type"])
        # Your code here: print "PARSED: src|dest|body_type".
        # message["src"], message["dest"] and message["body"] hold the fields.
        # When the body has no "type", print "unknown" instead.


if __name__ == "__main__":
    main()
