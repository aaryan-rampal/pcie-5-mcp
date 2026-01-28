#!/usr/bin/env python3
"""Extract entire PDF to text file for faster grep-based analysis"""

import pdfplumber

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"
OUTPUT_PATH = "pcie_spec_full_text.txt"

print(f"Extracting {PDF_PATH} to {OUTPUT_PATH}...")

with pdfplumber.open(PDF_PATH) as pdf:
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as out:
        for page_num, page in enumerate(pdf.pages):
            # Write page marker
            out.write(f"\n{'='*80}\n")
            out.write(f"PAGE {page_num + 1}\n")
            out.write(f"{'='*80}\n\n")

            # Extract text
            text = page.extract_text()
            if text:
                out.write(text)
            else:
                out.write("[NO TEXT EXTRACTED]\n")

            if (page_num + 1) % 100 == 0:
                print(f"  Processed {page_num + 1}/{len(pdf.pages)} pages...")

print(f"✅ Done! Extracted {len(pdf.pages)} pages to {OUTPUT_PATH}")
