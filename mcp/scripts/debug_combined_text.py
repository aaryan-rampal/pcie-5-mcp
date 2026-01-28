"""Debug script to check if page footers are being removed properly."""

import pdfplumber
import re
from pathlib import Path

pdf_path = Path(__file__).parent.parent.parent / "SYkDTqhOLhpUTnMx.pdf"

with pdfplumber.open(pdf_path) as pdf:
    # Get pages 686-687 (Command Register area)
    page_texts = []
    for page_num in [685, 686]:  # 0-indexed
        page = pdf.pages[page_num]
        page_texts.append(page.extract_text())

    print("="*80)
    print("BEFORE CLEANING:")
    print("="*80)

    # Show end of page 686
    lines686 = page_texts[0].split('\n')
    print(f"\nPage 686 - Last 10 lines:")
    for i, line in enumerate(lines686[-10:]):
        print(f"  {len(lines686) - 10 + i}: {repr(line)}")

    # Show start of page 687
    lines687 = page_texts[1].split('\n')
    print(f"\nPage 687 - First 10 lines:")
    for i, line in enumerate(lines687[:10]):
        print(f"  {i}: {repr(line)}")

    print("\n" + "="*80)
    print("AFTER CLEANING:")
    print("="*80)

    def clean_text(text):
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            if re.match(r'^Page \d+$', line.strip()):
                print(f"  REMOVED: {repr(line)}")
                continue
            if 'PCI Express' in line and 'Specification' in line:
                print(f"  REMOVED: {repr(line)}")
                continue
            cleaned.append(line)
        return '\n'.join(cleaned)

    cleaned_686 = clean_text(page_texts[0])
    cleaned_687 = clean_text(page_texts[1])

    combined = cleaned_686 + '\n' + cleaned_687

    print(f"\nCombined text around 'Memory Space Enable':")
    # Find Memory Space Enable
    idx = combined.find("1 Memory Space Enable")
    if idx != -1:
        snippet = combined[idx:idx+500]
        print(repr(snippet))
