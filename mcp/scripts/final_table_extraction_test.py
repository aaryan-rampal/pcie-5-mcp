"""
Final test: Use x-position analysis to extract table properly.

Finding: PDF has NO table lines - it's positioned text.
Strategy: Use explicit vertical lines based on word position analysis.
"""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent.parent / "SYkDTqhOLhpUTnMx.pdf"

print("="*80)
print("FINAL TEST: POSITION-BASED TABLE EXTRACTION")
print("="*80)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[725]  # Page 726

    # Based on word position analysis:
    # x≈110: Bit Location column
    # x≈170-400: Description column (main content)
    # x≈500+: Attributes column (RW, RO, etc.)

    # Try extraction with carefully tuned column boundaries
    settings = {
        "explicit_vertical_lines": [50, 105, 490, 550],  # Start, Bit|Desc, Desc|Attr, End
        "horizontal_strategy": "text",
        "snap_tolerance": 5,
    }

    print("\nExtracting with settings:")
    print(f"  Columns: [50, 105, 490, 550]")
    print(f"           [   Bit  |     Description     | Attr ]")
    print()

    table = page.extract_table(settings)

    if table:
        print(f"Extracted {len(table)} rows\n")

        # Find bit 4
        for row_idx, row in enumerate(table):
            if row and len(row) >= 2:
                row_text = ' '.join([str(c) if c else '' for c in row])

                if '4' in str(row[0]) and 'Enable Relaxed Ordering' in row_text:
                    print(f"✓ FOUND BIT 4 at row {row_idx}\n")
                    print(f"Row has {len(row)} columns:")

                    for col_idx, cell in enumerate(row):
                        col_name = ['Bit', 'Description', 'Attributes'][col_idx] if col_idx < 3 else f'Col{col_idx}'
                        print(f"\n  {col_name}:")
                        if cell:
                            print(f"    {str(cell)[:200]}")
                            if col_idx == 1:  # Description
                                print(f"    ... (total {len(str(cell))} chars)")

                    # Check for section reference
                    desc = str(row[1]) if len(row) > 1 and row[1] else ""
                    has_section = '2.2.6.4' in desc

                    print(f"\n  ✓ Description contains '2.2.6.4': {has_section}")

                    if not has_section:
                        print("\n  ⚠️  Section reference missing!")
                        print(f"  Description ends with: ...{desc[-60:]}")

                    break
    else:
        print("No table extracted!")

    print("\n" + "="*80)
    print("COMPARISON WITH CURRENT TEXT-BASED PARSER")
    print("="*80)

    # Show what current parser gets
    text = page.extract_text()
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if '4 Enable Relaxed Ordering' in line:
            print(f"\nCurrent parser sees (line {i}):")
            print(f"  {repr(line)}")
            print(f"\nNext 3 lines:")
            for j in range(i+1, min(i+4, len(lines))):
                print(f"  {repr(lines[j])}")

            # Current parser would stop at line with section number
            print(f"\n  Current parser STOPS at line {i+2}: '2.2.6.4andSection2.4).'")
            print(f"  Because it matches r'^\\d+\\.\\d+\\.\\d+' pattern (thinks it's a new register)")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print()
    print("Q: Does better table extraction solve the problem?")
    print("A: [To be determined from results above]")
    print()
    print("If table extraction CANNOT get the full description either,")
    print("then the problem is fundamental to how the PDF is structured,")
    print("not fixable by better extraction settings.")
