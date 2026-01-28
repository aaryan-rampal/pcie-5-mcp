#!/usr/bin/env python3
"""
Try parsing register fields directly from text since table extraction is broken.
"""

import sys
from pathlib import Path
import pdfplumber
import re

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"
page_num = 686

print(f"=== Text-based Parsing - Page {page_num} ===\n")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[page_num - 1]
    text = page.extract_text()

    # Find table start (after "Attributes" header)
    print("Looking for table patterns...\n")

    # Pattern: bit number at start of line, followed by field name, description, and RW/RO attribute
    # Example: "0 I/O Space Enable- Controls a Function's response... RW"
    field_pattern = re.compile(
        r'^(\d+(?::\d+)?)\s+(.+?)\s+(RW|RO|RWC|RW1C|RW1CS|RsvdP|RsvdZ|HwInit)\s*$',
        re.MULTILINE
    )

    matches = list(field_pattern.finditer(text))
    print(f"Found {len(matches)} field patterns\n")

    for i, match in enumerate(matches[:5]):  # First 5
        bits = match.group(1)
        rest = match.group(2)
        attr = match.group(3)

        # Extract field name (before the dash or first 50 chars)
        if '-' in rest:
            field_name = rest.split('-')[0].strip()
            description = rest.split('-', 1)[1].strip()
        else:
            field_name = rest[:50]
            description = rest

        print(f"{i+1}. Bit {bits}: {field_name}")
        print(f"   Attribute: {attr}")
        print(f"   Description: {description[:100]}...")
        print()

    # Also try to find where descriptions continue on next lines
    print("\n=== Looking for multi-line field entries ===\n")

    # Split text into lines
    lines = text.split('\n')

    # Find lines starting with bit numbers
    for i, line in enumerate(lines):
        if re.match(r'^\d+(?::\d+)?\s+\w', line):
            print(f"Line {i}: {line[:100]}")
            # Print next few lines
            for j in range(1, min(4, len(lines) - i)):
                next_line = lines[i + j]
                if next_line.strip():
                    print(f"  +{j}: {next_line[:100]}")
            print()
            if i > 10:  # Just show first few
                break
