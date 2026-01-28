"""Check if bit 1 description continues on next page."""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

with pdfplumber.open(pdf_path) as pdf:
    # Page 686 and 687
    for page_num in [685, 686]:
        page = pdf.pages[page_num]
        text = page.extract_text()
        lines = text.split('\n')

        print(f"\n{'='*80}")
        print(f"PAGE {page_num + 1}:")
        print('='*80)

        # Look for Memory Space Enable continuation
        for i, line in enumerate(lines):
            if 'Memory Space Enable' in line or \
               'memory space' in line.lower() or \
               (page_num == 686 and i < 20):  # First 20 lines of page 687
                print(f"{i:4d}: {repr(line)}")
