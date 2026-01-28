#!/usr/bin/env python3
"""
Check pages with "empty" registers to see if they actually have field tables
"""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

# Check a few empty register pages
test_cases = [
    (685, "Vendor ID Register"),
    (686, "Device ID Register"),
    (691, "Revision ID Register"),
]

with pdfplumber.open(pdf_path) as pdf:
    for page_num, reg_name in test_cases:
        page = pdf.pages[page_num - 1]
        text = page.extract_text()

        print(f"\n=== Page {page_num}: {reg_name} ===\n")

        # Check if register name appears
        if reg_name in text:
            # Find the line and print surrounding context
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if reg_name in line:
                    print(f"Found at line {i}:")
                    # Print 10 lines after
                    for j in range(min(10, len(lines) - i)):
                        print(f"  {lines[i+j]}")
                    break

        # Check for field patterns (lines starting with bit numbers)
        import re
        field_lines = [line for line in text.split('\n')
                      if re.match(r'^\d+(?::\d+)?\s+[A-Z]', line.strip())]

        print(f"\nField-like lines found: {len(field_lines)}")
        if field_lines:
            print("Examples:")
            for line in field_lines[:3]:
                print(f"  {line.strip()}")
