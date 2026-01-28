#!/usr/bin/env python3
"""
Debug script to understand the actual table structure.
"""

import sys
from pathlib import Path
import pdfplumber

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

# Page 686 has Command Register table
page_num = 686

print(f"=== Detailed Table Analysis - Page {page_num} ===\n")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[page_num - 1]
    tables = page.extract_tables()

    for i, table in enumerate(tables):
        print(f"--- TABLE {i+1} ---")
        if not table:
            print("Empty\n")
            continue

        print(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")
        print()

        # Print ALL rows for small tables, first 5 for large ones
        max_rows = min(len(table), 10)
        for j, row in enumerate(table[:max_rows]):
            print(f"Row {j}: {row}")

        if len(table) > max_rows:
            print(f"... ({len(table) - max_rows} more rows)")

        print("\n")
