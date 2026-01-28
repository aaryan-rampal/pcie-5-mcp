#!/usr/bin/env python3
"""Test 5: Find register definition pages"""

import pdfplumber
import re

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"

print("=" * 80)
print("Test 5: Finding Register Definitions")
print("=" * 80)

register_pages = []

with pdfplumber.open(PDF_PATH) as pdf:
    # Search for pages with register tables (they usually have "Bit" headers)
    print("Searching for pages with register bit fields...")

    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        text = page.extract_text()

        if not text:
            continue

        # Look for patterns like "Bit Location" or "Bits" followed by numbers
        if re.search(r'Bit\s+(Location|Offset|\d+:\d+)', text, re.IGNORECASE):
            register_pages.append(page_num + 1)

            if len(register_pages) <= 15:  # Show first 15
                print(f"\nPage {page_num + 1}: Register content found")
                lines = text.split('\n')
                # Show section header
                for line in lines[:10]:
                    if re.match(r'^\d+(\.\d+)+ .+Register', line, re.IGNORECASE):
                        print(f"  Section: {line[:80]}")
                        break

print(f"\n{'=' * 80}")
print(f"Found register definitions on {len(register_pages)} pages")
print(f"Sample pages: {register_pages[:30]}")

# Look at one register page in detail
if len(register_pages) >= 10:
    target_page = register_pages[10] - 1

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[target_page]
        text = page.extract_text()

        print(f"\n{'=' * 80}")
        print(f"EXAMPLE REGISTER PAGE {target_page + 1}")
        print('=' * 80)

        lines = text.split('\n')

        # Show first 30 lines
        print("\nFirst 30 lines:")
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:3}: {line[:120]}")

        # Check tables
        tables = page.extract_tables()
        print(f"\nTables found: {len(tables)}")

        if tables:
            for idx, table in enumerate(tables[:1], 1):
                print(f"\nTable {idx} structure:")
                print(f"  Rows: {len(table)}, Cols: {len(table[0]) if table and table[0] else 0}")

                if table and len(table) > 0:
                    print(f"\n  First 5 rows:")
                    for row_idx, row in enumerate(table[:5]):
                        print(f"    Row {row_idx}: {row}")
