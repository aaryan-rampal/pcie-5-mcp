"""Debug script to see exactly what text is extracted for Command Register."""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent / "SYkDTqhOLhpUTnMx.pdf"

print(f"Opening PDF: {pdf_path}")

with pdfplumber.open(pdf_path) as pdf:
    # Command Register is on page 686 (0-indexed: 685)
    page = pdf.pages[685]

    print("\n" + "="*80)
    print("FULL PAGE TEXT (page 686):")
    print("="*80)
    text = page.extract_text()

    # Find Command Register section
    lines = text.split('\n')

    in_command_register = False
    for i, line in enumerate(lines):
        if 'Command Register' in line and 'Offset 04h' in line:
            in_command_register = True
            print(f"\nSTARTING AT LINE {i}:")

        if in_command_register:
            print(f"{i:4d}: {repr(line)}")

            # Stop at next register or after ~50 lines
            if i > 100 and ('Offset' in line and 'Command Register' not in line):
                break
            if i > 200:  # Safety limit
                break

    print("\n" + "="*80)
    print("TABLE EXTRACTION:")
    print("="*80)
    tables = page.extract_tables()
    for i, table in enumerate(tables):
        print(f"\nTable {i}:")
        for j, row in enumerate(table[:10]):  # First 10 rows
            print(f"  Row {j}: {row}")
