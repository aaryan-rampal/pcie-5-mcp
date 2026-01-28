#!/usr/bin/env python3
"""Test 3: Sample actual content pages to understand structure"""

import pdfplumber
import re

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"

print("=" * 80)
print("Test 3: Sample Content Pages")
print("=" * 80)

# Sample pages from different sections
sample_pages = [60, 100, 200, 400, 600, 800, 1000, 1200]

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num in sample_pages:
        if page_num >= len(pdf.pages):
            continue

        page = pdf.pages[page_num]
        text = page.extract_text()

        print(f"\n{'=' * 80}")
        print(f"PAGE {page_num + 1}")
        print('=' * 80)

        if not text:
            print("[No text extracted]")
            continue

        lines = text.split('\n')
        print(f"Total lines: {len(lines)}\n")

        # Show first 15 lines
        print("First 15 lines:")
        for i, line in enumerate(lines[:15], 1):
            print(f"{i:3}: {line[:100]}")

        # Check for section headers (look for patterns like "4.2.6.3 Title")
        print("\nSection headers found:")
        for line in lines[:30]:
            if re.match(r'^\d+(\.\d+)+ .+', line.strip()):
                print(f"  -> {line.strip()[:80]}")

        # Check for register/table content
        has_register = any(re.search(r'\b(Bit|Field|Offset|Register)\b', line, re.IGNORECASE) for line in lines[:30])
        has_table = any(re.search(r'\b(Table \d+)', line) for line in lines[:30])

        print(f"\nContent markers:")
        print(f"  Has register-like content: {has_register}")
        print(f"  Has table references: {has_table}")

        # Check for LTSSM or state machine content
        if any('ltssm' in line.lower() or 'state machine' in line.lower() for line in lines):
            print(f"  ⭐ Contains LTSSM/State Machine content!")
