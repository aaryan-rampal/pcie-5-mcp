#!/usr/bin/env python3
"""Test 1: Basic PDF info and first few pages"""

import pdfplumber
import PyPDF2

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"

print("=" * 80)
print("Test 1: Basic PDF Information")
print("=" * 80)

# Test with pdfplumber
with pdfplumber.open(PDF_PATH) as pdf:
    print(f"\nTotal pages: {len(pdf.pages)}")
    print(f"First page dimensions: {pdf.pages[0].width} x {pdf.pages[0].height}")

    # Look at first 5 pages
    for i in range(min(5, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text()

        print(f"\n--- Page {i+1} ---")
        if text:
            lines = text.split('\n')
            print(f"Lines: {len(lines)}")
            print(f"First 5 lines:")
            for line in lines[:5]:
                print(f"  {line[:100]}")  # First 100 chars
        else:
            print("  [No text extracted]")

# Test PyPDF2 metadata
with open(PDF_PATH, 'rb') as f:
    pdf_reader = PyPDF2.PdfReader(f)
    print(f"\n--- Metadata ---")
    if pdf_reader.metadata:
        for key, value in pdf_reader.metadata.items():
            print(f"{key}: {value}")

    # Check if we can get outlines/bookmarks
    if hasattr(pdf_reader, 'outline'):
        print(f"\nOutline/Bookmarks found: {len(pdf_reader.outline) if pdf_reader.outline else 0}")
