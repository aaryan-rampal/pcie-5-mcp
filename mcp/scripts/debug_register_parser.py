#!/usr/bin/env python3
"""
Debug script to understand what's going wrong with register parsing.
Let's extract a single page and see what the parser is doing.
"""

import sys
from pathlib import Path
import pdfplumber
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsers.register_parser_pdf import PDFRegisterParser

# Test page 686 (where Device ID Register should be)
pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"
test_page = 686

print(f"=== Debugging Register Parser ===")
print(f"PDF: {pdf_path}")
print(f"Test page: {test_page}\n")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[test_page - 1]  # 0-indexed

    print("=== PAGE TEXT (first 2000 chars) ===")
    text = page.extract_text()
    print(text[:2000])
    print("\n")

    print("=== SEARCHING FOR REGISTER HEADERS ===")
    REGISTER_HEADER_PATTERN = re.compile(
        r'(\d+(?:\.\d+)*)\s+(.+?)\s*\(Offset\s+([0-9A-Fa-f]+h)\)',
        re.IGNORECASE
    )

    matches = list(REGISTER_HEADER_PATTERN.finditer(text))
    print(f"Found {len(matches)} register headers:\n")
    for i, match in enumerate(matches):
        section = match.group(1)
        name = match.group(2).strip()
        offset = match.group(3)
        print(f"{i+1}. Section: {section}")
        print(f"   Name: {name}")
        print(f"   Offset: {offset}")
        print()

    print("\n=== TABLES ON PAGE ===")
    tables = page.extract_tables()
    print(f"Found {len(tables)} tables\n")

    for i, table in enumerate(tables):
        print(f"--- Table {i+1} ---")
        if not table:
            print("Empty table")
            continue

        print(f"Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")

        # Print header
        if table:
            print("Header:", table[0])

        # Print first 3 data rows
        print("Sample rows:")
        for row in table[1:4]:
            print(f"  {row}")

        print()
