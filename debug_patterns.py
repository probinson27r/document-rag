#!/usr/bin/env python3
"""
Debug script to test regex patterns
"""

import re

# Test the fixed patterns
patterns = [
    r'^([a-z])\)\s+(.+)$',        # a) Sub-objective
    r'^([A-Z])\.\s+(.+)$',        # A. Major objective
    r'^\(([A-Z])\)\s+(.+)$',      # (A) Major objective
    r'^([A-Z])\)\s+(.+)$',        # A) Major objective
]

test_lines = [
    "a) This is a test",
    "A. This is a test",
    "(A) This is a test",
    "A) This is a test",
]

for i, pattern in enumerate(patterns):
    print(f"Testing pattern {i+1}: {pattern}")
    try:
        compiled = re.compile(pattern)
        print(f"  ✅ Pattern compiles successfully")
        
        for line in test_lines:
            match = compiled.match(line)
            if match:
                print(f"  ✅ Matches: '{line}' -> {match.groups()}")
            else:
                print(f"  ❌ No match: '{line}'")
    except Exception as e:
        print(f"  ❌ Pattern error: {e}")
    print()
