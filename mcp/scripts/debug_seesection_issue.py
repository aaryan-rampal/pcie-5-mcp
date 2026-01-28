"""Debug why descriptions ending with 'seeSection' are truncated."""

import pdfplumber
import re
from pathlib import Path

pdf_path = Path(__file__).parent.parent.parent / "SYkDTqhOLhpUTnMx.pdf"

def combine_page_texts(page_texts):
    """Same cleaning as parser."""
    cleaned_texts = []
    for text in page_texts:
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line_stripped = line.strip()
            if re.match(r'^Page \d+$', line_stripped):
                continue
            if 'PCI Express' in line and 'Specification' in line:
                continue
            if line_stripped == 'BitLocation Register Description Attributes':
                continue
            if line_stripped == 'Bit Location Register Description Attributes':
                continue
            cleaned_lines.append(line)
        cleaned_texts.append('\n'.join(cleaned_lines))
    return '\n'.join(cleaned_texts)

with pdfplumber.open(pdf_path) as pdf:
    # Get pages around Device Control Register (page 723 reported, probably 720-726)
    page_texts = []
    for page_num in range(720, 726):
        page = pdf.pages[page_num]
        page_texts.append(page.extract_text())

    combined = combine_page_texts(page_texts)

    # Find "Enable Relaxed Ordering"
    idx = combined.find("Enable Relaxed Ordering")
    if idx != -1:
        print("Found 'Enable Relaxed Ordering' at position", idx)
        snippet = combined[idx:idx+500]
        print("\nContext (500 chars):")
        print(repr(snippet))
        print("\n" + "="*80)
        print("Looking for '(seeSection' pattern:")
        see_idx = snippet.find("(seeSection")
        if see_idx != -1:
            print(f"Found at position {see_idx} in snippet")
            print("Next 100 chars after '(seeSection':")
            print(repr(snippet[see_idx:see_idx+100]))
