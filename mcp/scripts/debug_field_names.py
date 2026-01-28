#!/usr/bin/env python3
"""
Debug field name extraction to understand why we're getting "I/O" instead of "I/O Space Enable"
"""

import re

test_lines = [
    "0 I/O Space Enable- Controls a Function's response to I/O Space accesses...",
    "1 Memory Space Enable- Controls a Function's response to Memory Space accesses...",
    "2 Bus Master Enable- Controls the ability of a Function to issue Memory138and I/O...",
    "10 Interrupt Disable- Controls the ability of a Function to generate INTx emulation...",
]

# Current pattern
pattern = re.compile(r'^(\d+(?::\d+)?)\s+([A-Z][\w\s/]+?)[-\s]')

print("=== Testing Field Name Extraction ===\n")

for line in test_lines:
    match = pattern.match(line)
    if match:
        bit_str = match.group(1)
        field_name = match.group(2).strip()
        print(f"Line: {line[:60]}...")
        print(f"  Bit: {bit_str}")
        print(f"  Name: '{field_name}'")
        print()

print("\n=== Testing improved pattern ===\n")

# Improved pattern: capture until the dash
improved_pattern = re.compile(r'^(\d+(?::\d+)?)\s+([A-Z][\w\s/]+?)\s*-')

for line in test_lines:
    match = improved_pattern.match(line)
    if match:
        bit_str = match.group(1)
        field_name = match.group(2).strip()
        print(f"Line: {line[:60]}...")
        print(f"  Bit: {bit_str}")
        print(f"  Name: '{field_name}'")
        print()
