"""
Compare table extraction approaches for Device Control Register Bit 4.

Test Case: Enable Relaxed Ordering (Bit 4)
- Currently truncated at: "...ordering (seeSection"
- Should include: "(see Section 2.2.6.4 and Section 2.4)."
- Page: 725 (based on user verification)
"""

import pdfplumber
from pathlib import Path

pdf_path = Path(__file__).parent.parent.parent / "SYkDTqhOLhpUTnMx.pdf"

print("="*80)
print("TABLE EXTRACTION COMPARISON TEST")
print("="*80)
print(f"\nTest Case: Device Control Register, Bit 4 - Enable Relaxed Ordering")
print(f"Page: 725 (0-indexed: 724)")
print(f"Expected: Description should include '(see Section 2.2.6.4 and Section 2.4).'")
print()

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[724]  # Page 725 (0-indexed)

    # STEP 1: Inspect PDF structure
    print("="*80)
    print("STEP 1: INSPECT TABLE STRUCTURE")
    print("="*80)

    print(f"\nLines in page: {len(page.lines)}")
    if page.lines:
        print(f"Sample lines (first 5):")
        for i, line in enumerate(page.lines[:5]):
            print(f"  Line {i}: x0={line['x0']:.1f}, y0={line['y0']:.1f}, "
                  f"x1={line['x1']:.1f}, y1={line['y1']:.1f}")

    print(f"\nRects in page: {len(page.rects)}")
    if page.rects:
        print(f"Sample rects (first 3):")
        for i, rect in enumerate(page.rects[:3]):
            print(f"  Rect {i}: x0={rect['x0']:.1f}, y0={rect['y0']:.1f}, "
                  f"x1={rect['x1']:.1f}, y1={rect['y1']:.1f}")

    # STEP 2: Try vanilla table extraction
    print("\n" + "="*80)
    print("STEP 2: VANILLA TABLE EXTRACTION (extract_tables())")
    print("="*80)

    tables = page.extract_tables()
    print(f"\nFound {len(tables)} tables")

    # Find the table with bit field data
    for i, table in enumerate(tables):
        if not table or len(table) < 2:
            continue

        # Check if this has our bit 4
        for row_idx, row in enumerate(table):
            row_text = ' '.join([str(cell) if cell else '' for cell in row])
            if 'Enable Relaxed Ordering' in row_text and '4' in row_text:
                print(f"\n✓ Found Bit 4 in table {i}, row {row_idx}")
                print(f"Row has {len(row)} columns:")
                for col_idx, cell in enumerate(row):
                    if cell:
                        preview = str(cell)[:200]
                        print(f"  Column {col_idx}: {preview}")

                # Check if section reference is included
                full_text = ' '.join([str(cell) if cell else '' for cell in row])
                has_section_ref = '2.2.6.4' in full_text
                print(f"\n✓ Contains '2.2.6.4': {has_section_ref}")

    # STEP 3: Try table extraction with explicit settings
    print("\n" + "="*80)
    print("STEP 3: TABLE EXTRACTION WITH EXPLICIT SETTINGS")
    print("="*80)

    # Try different strategies
    strategies = [
        {
            "name": "Lines-based",
            "settings": {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
            }
        },
        {
            "name": "Text-based",
            "settings": {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            }
        },
        {
            "name": "Explicit columns (manual)",
            "settings": {
                "explicit_vertical_lines": [0, 80, 450, 550],  # Rough guess at column boundaries
            }
        }
    ]

    for strategy in strategies:
        print(f"\n--- Strategy: {strategy['name']} ---")
        try:
            table = page.extract_table(strategy['settings'])
            if table:
                print(f"Extracted {len(table)} rows")
                # Find bit 4
                for row_idx, row in enumerate(table):
                    if row:
                        row_text = ' '.join([str(cell) if cell else '' for cell in row])
                        if 'Enable Relaxed Ordering' in row_text and '4' in row_text:
                            print(f"✓ Found Bit 4 at row {row_idx}")
                            print(f"  Columns: {len(row)}")
                            has_section = '2.2.6.4' in row_text
                            print(f"  Contains '2.2.6.4': {has_section}")

                            # Show description column
                            if len(row) > 1:
                                desc = str(row[1]) if row[1] else ""
                                print(f"  Description length: {len(desc)} chars")
                                print(f"  Last 100 chars: ...{desc[-100:]}")
            else:
                print("  No table extracted")
        except Exception as e:
            print(f"  Error: {e}")

    # STEP 4: Current text-based approach
    print("\n" + "="*80)
    print("STEP 4: CURRENT TEXT-BASED APPROACH (FOR COMPARISON)")
    print("="*80)

    text = page.extract_text()
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if 'Enable Relaxed Ordering' in line and '4 ' in line:
            print(f"\nFound at line {i}: {repr(line)}")
            print(f"\nContext (next 5 lines):")
            for j in range(i, min(i+6, len(lines))):
                print(f"  {j}: {repr(lines[j])}")

            # Check if we can get the full description
            full_desc = line
            for j in range(i+1, min(i+10, len(lines))):
                if lines[j].strip() and not lines[j].strip()[0].isdigit():
                    full_desc += " " + lines[j]
                else:
                    break

            has_section = '2.2.6.4' in full_desc
            print(f"\n✓ Contains '2.2.6.4' in full description: {has_section}")
            print(f"Full description length: {len(full_desc)} chars")

    # STEP 5: Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nConclusion: [To be determined after running]")
