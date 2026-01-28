#!/usr/bin/env python3
"""
Check why descriptions have inline RW markers
"""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[685]  # Page 686 (0-indexed)
    text = page.extract_text()

    # Find the first field description
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if line.strip().startswith('0 I/O Space Enable'):
            print("Found field at line", i)
            print()
            # Print this line and next 10 lines
            for j in range(15):
                if i + j < len(lines):
                    print(f"{i+j}: {lines[i+j]}")
            break
