#!/usr/bin/env python3
"""Summarize Nginx JSON request logs without claiming unique users or execution."""
from collections import Counter
import json
import sys

paths, statuses = Counter(), Counter()
bytes_sent = requests = ignored = 0
for line in sys.stdin:
    try:
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get('path'), str):
            raise ValueError('Not a request')
        status, size = int(row['status']), int(row['bytes'])
        if status < 100 or status > 599 or size < 0:
            raise ValueError('Bad request metrics')
        paths[row['path']] += 1
        statuses[str(status)] += 1
        bytes_sent += size
        requests += 1
    except (ValueError, TypeError, KeyError):
        ignored += 1
print(json.dumps({'requests': requests, 'bytes_sent': bytes_sent,
                  'statuses': dict(statuses), 'paths': dict(paths), 'ignored_lines': ignored,
                  'meaning': 'HTTP requests only; not unique people, consoles or successful jailbreaks'}, indent=2))
