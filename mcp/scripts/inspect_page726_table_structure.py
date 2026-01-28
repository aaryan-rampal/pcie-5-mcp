"""
Deep inspection of page 726 table structure to understand why columns are merged.
"""

import pdfplumber
from pathlib import Path
import json

pdf_path = Path(__file__).parent.parent.parent / "SYkDTqhOLhpUTnMx.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[725]  # Page 726 (0-indexed)

    print("="*80)
    print("DEEP INSPECTION: PAGE 726 TABLE STRUCTURE")
    print("="*80)

    # Check for vertical lines in the table area
    print("\n1. VERTICAL LINES (for column separation):")
    print(f"   Total vertical lines: {len([l for l in page.lines if abs(l['x0'] - l['x1']) < 1])}")

    vertical_lines = [l for l in page.lines if abs(l['x0'] - l['x1']) < 1]
    if vertical_lines:
        print("   Sample vertical lines (first 5):")
        for line in vertical_lines[:5]:
            print(f"     x={line['x0']:.1f}, y={line['y0']:.1f} to y={line['y1']:.1f}")

    # Check for horizontal lines
    print("\n2. HORIZONTAL LINES (for row separation):")
    horizontal_lines = [l for l in page.lines if abs(l['y0'] - l['y1']) < 1]
    print(f"   Total horizontal lines: {len(horizontal_lines)}")
    if horizontal_lines:
        print("   Sample horizontal lines (first 5):")
        for line in horizontal_lines[:5]:
            print(f"     y={line['y0']:.1f}, x={line['x0']:.1f} to x={line['x1']:.1f}")

    # Check table settings with debug
    print("\n3. TABLE FINDER DEBUG:")
    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
    }

    try:
        from pdfplumber.table import TableFinder
        tf = TableFinder(page, settings)
        print(f"   Tables found: {len(tf.tables)}")
        if tf.tables:
            for i, table in enumerate(tf.tables):
                print(f"   Table {i}: {table.bbox}")
                print(f"     Cells: {len(table.cells)} cells")
    except Exception as e:
        print(f"   Error: {e}")

    # Try extracting with different settings
    print("\n4. EXTRACTION WITH DIFFERENT STRATEGIES:")

    strategies = [
        ("default", {}),
        ("lines-strict", {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
        }),
        ("text-based", {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        }),
        ("explicit-3col", {
            "explicit_vertical_lines": [50, 80, 450, 550],
            "horizontal_strategy": "text",
        }),
        ("explicit-4col", {
            "explicit_vertical_lines": [50, 70, 400, 500, 550],
            "horizontal_strategy": "text",
        }),
    ]

    for name, settings in strategies:
        print(f"\n   Strategy: {name}")
        try:
            table = page.extract_table(settings) if settings else page.extract_tables()[0] if page.extract_tables() else None
            if table and len(table) > 0:
                # Find a row with content
                sample_row = None
                for row in table[1:6]:  # Check first few data rows
                    if row and any(cell and len(str(cell)) > 20 for cell in row):
                        sample_row = row
                        break

                if sample_row:
                    print(f"     Columns in sample row: {len(sample_row)}")
                    for i, cell in enumerate(sample_row):
                        if cell:
                            preview = str(cell)[:80]
                            print(f"       Col {i}: {preview}")
                else:
                    print(f"     Table has {len(table)} rows but no substantial content found")
            else:
                print("     No table extracted")
        except Exception as e:
            print(f"     Error: {e}")

    # Check word positions to understand actual layout
    print("\n5. WORD POSITION ANALYSIS:")
    words = page.extract_words()

    # Find words in "Enable Relaxed Ordering" row
    target_words = [w for w in words if 'Enable' in w['text'] or 'Relaxed' in w['text'] or 'Ordering' in w['text']]

    if target_words:
        print(f"   Found {len(target_words)} words matching 'Enable/Relaxed/Ordering'")
        print("   Sample positions:")
        for word in target_words[:5]:
            print(f"     '{word['text']}' at x={word['x0']:.1f}")

        # Check x-position distribution
        x_positions = sorted([w['x0'] for w in words if w['text'].strip()])
        print(f"\n   X-position range: {min(x_positions):.1f} to {max(x_positions):.1f}")

        # Find common x-positions (potential column starts)
        from collections import Counter
        x_counts = Counter([round(w['x0'] / 10) * 10 for w in words])  # Round to nearest 10
        common_x = sorted(x_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        print("   Most common x-positions (potential columns):")
        for x, count in common_x:
            print(f"     x≈{x}: {count} words")

    print("\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    print("Based on the analysis above, we can determine:")
    print("1. Whether the PDF has actual table lines (vertical/horizontal)")
    print("2. If not, we need to infer columns from text positions")
    print("3. Best strategy for extracting this specific table format")
