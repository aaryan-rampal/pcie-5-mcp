"""Debug script to understand the table structure for Command Register."""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

print(f"Opening PDF: {pdf_path}")

with pdfplumber.open(pdf_path) as pdf:
    # Command Register is on page 686 (0-indexed: 685)
    page = pdf.pages[685]

    print("\n" + "="*80)
    print("TABLE EXTRACTION - Detailed:")
    print("="*80)
    tables = page.extract_tables()

    # Table 2 looks like the register bit fields
    if len(tables) > 2:
        table = tables[2]
        print(f"\nTable 2 (the bit fields table):")
        print(f"Total rows: {len(table)}")
        print(f"Total columns in row 0: {len(table[0]) if table else 0}")

        for i, row in enumerate(table):
            print(f"\nRow {i} - {len(row)} cells:")
            for j, cell in enumerate(row):
                if cell:
                    cell_preview = cell[:200] if len(cell) > 200 else cell
                    print(f"  Cell [{i}][{j}]: {repr(cell_preview)}")

    print("\n" + "="*80)
    print("Let's check how lines map to the table:")
    print("="*80)

    text = page.extract_text()
    lines = text.split('\n')

    # Find the table start
    for i, line in enumerate(lines):
        if 'BitLocation Register Description Attributes' in line:
            print(f"Table header at line {i}: {repr(line)}")
            print("\nNext 20 lines:")
            for j in range(i+1, min(i+21, len(lines))):
                print(f"  {j}: {repr(lines[j])}")
            break
