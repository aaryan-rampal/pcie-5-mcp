#!/usr/bin/env python3
"""Test 4: Find LTSSM content specifically"""

import pdfplumber
import re

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"

print("=" * 80)
print("Test 4: Finding LTSSM Content")
print("=" * 80)

ltssm_pages = []

with pdfplumber.open(PDF_PATH) as pdf:
    # Search through all pages for LTSSM
    print("Searching all pages for LTSSM mentions...")

    for page_num in range(len(pdf.pages)):
        page = pdf.pages[page_num]
        text = page.extract_text()

        if text and 'LTSSM' in text.upper():
            ltssm_pages.append(page_num + 1)

            if len(ltssm_pages) <= 10:  # Show detail for first 10
                print(f"\n--- Page {page_num + 1} ---")
                lines = text.split('\n')

                # Find lines with LTSSM
                ltssm_lines = [line for line in lines if 'LTSSM' in line.upper()]
                for line in ltssm_lines[:5]:
                    print(f"  {line[:100]}")

print(f"\n{'=' * 80}")
print(f"Found LTSSM on {len(ltssm_pages)} pages")
print(f"Page range: {ltssm_pages[:20]}")

# Now look at one LTSSM page in detail
if ltssm_pages:
    target_page = ltssm_pages[5] - 1  # Pick the 6th one (likely middle of content)

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[target_page]
        text = page.extract_text()

        print(f"\n{'=' * 80}")
        print(f"DETAILED LOOK AT PAGE {target_page + 1}")
        print('=' * 80)

        lines = text.split('\n')
        print(f"Total lines: {len(lines)}")

        print("\nFull page content:")
        for i, line in enumerate(lines[:40], 1):
            print(f"{i:3}: {line}")

        # Check for tables
        tables = page.extract_tables()
        print(f"\nTables found: {len(tables)}")
        if tables:
            for idx, table in enumerate(tables[:2], 1):
                print(f"\nTable {idx}:")
                print(f"  Rows: {len(table)}, Cols: {len(table[0]) if table else 0}")
                if table:
                    for row in table[:5]:
                        print(f"    {row}")
