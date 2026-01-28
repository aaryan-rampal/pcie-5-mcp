#!/usr/bin/env python3
"""Test 2: Extract Table of Contents from pages 3-20"""

import pdfplumber
import re

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"

print("=" * 80)
print("Test 2: TOC Extraction from Early Pages")
print("=" * 80)

toc_entries = []

with pdfplumber.open(PDF_PATH) as pdf:
    # Look at pages 3-30 for TOC (it's usually in the beginning)
    for page_num in range(2, min(30, len(pdf.pages))):  # 0-indexed, so page 3 is index 2
        page = pdf.pages[page_num]
        text = page.extract_text()

        if not text:
            continue

        print(f"\n--- Checking Page {page_num + 1} ---")

        lines = text.split('\n')
        for line in lines[:10]:  # Show first 10 lines
            print(f"  {line[:120]}")

        # Look for TOC patterns: "X.Y.Z Title ... PageNum"
        # Common patterns:
        # "1.2.3 Some Title.........................................45"
        # "4.5 Another Title ....................................... 123"

        for line in lines:
            # Pattern 1: Section number, title, dots, page number
            match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+\.{2,}\s*(\d+)\s*$', line.strip())
            if match:
                section_num, title, page_ref = match.groups()
                toc_entries.append({
                    'section': section_num,
                    'title': title.strip(),
                    'page': int(page_ref),
                    'found_on_page': page_num + 1
                })

            # Pattern 2: Section number, title, page number (no dots)
            match2 = re.match(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)\s*$', line.strip())
            if match2 and not match:  # Only if pattern 1 didn't match
                section_num, title, page_ref = match2.groups()
                # Check if it looks like a real page number (not too big)
                if page_ref.isdigit() and int(page_ref) < 2000:
                    toc_entries.append({
                        'section': section_num,
                        'title': title.strip(),
                        'page': int(page_ref),
                        'found_on_page': page_num + 1
                    })

print(f"\n{'=' * 80}")
print(f"Found {len(toc_entries)} TOC entries")
print("=" * 80)

# Show first 30
for entry in toc_entries[:30]:
    print(f"{entry['section']:15} {entry['title']:60} pg.{entry['page']}")

# Show distribution
if toc_entries:
    print(f"\nTOC entry page range: {min(e['page'] for e in toc_entries)} - {max(e['page'] for e in toc_entries)}")
