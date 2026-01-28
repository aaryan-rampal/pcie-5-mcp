#!/usr/bin/env python3
"""
Debug script to check multiple pages and understand register table structure.
"""

import sys
from pathlib import Path
import pdfplumber
import re

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

# Test several pages
test_pages = [686, 687, 688, 700, 750]

print(f"=== Testing Multiple Pages ===\n")

with pdfplumber.open(pdf_path) as pdf:
    for page_num in test_pages:
        page = pdf.pages[page_num - 1]
        text = page.extract_text()

        print(f"=== PAGE {page_num} ===")

        # Look for section headers like "7.5.1.1.3 Command Register (Offset 04h)"
        # Note: section and name may have no space between them
        pattern = re.compile(
            r'^(\d+(?:\.\d+)+)\s*([A-Z][^(]+?)\s*\(Offset\s+([0-9A-Fa-f]+h)\)',
            re.MULTILINE
        )

        matches = list(pattern.finditer(text))
        print(f"Register headers found: {len(matches)}")
        for match in matches:
            print(f"  Section: '{match.group(1)}' Name: '{match.group(2).strip()}' Offset: {match.group(3)}")

        # Check table structure
        tables = page.extract_tables()
        print(f"Tables found: {len(tables)}")

        # Look for table with bit field structure
        for i, table in enumerate(tables):
            if not table or len(table) < 2:
                continue

            header = table[0]
            # Check if this looks like a register bit field table
            header_text = ' '.join([str(c) if c else '' for c in header]).lower()

            if 'bit' in header_text and 'location' in header_text:
                print(f"\n  Table {i+1} looks like a register table!")
                print(f"  Header: {header}")
                print(f"  Columns: {len(header)}")
                print(f"  Rows: {len(table)}")

                # Print first 2 data rows
                for j, row in enumerate(table[1:3]):
                    print(f"  Row {j+1}: {row[:3] if len(row) > 3 else row}")  # First 3 columns

        print()
