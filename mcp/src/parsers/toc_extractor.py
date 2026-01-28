"""
Table of Contents Extractor for PCIe Specification

Extracts hierarchical TOC structure from spec text to enable:
- Section-aware chunking
- Context preservation
- Navigation and lookup

Based on PCIe_doc_summary.md analysis:
- TOC has up to 5 levels deep (X.Y.Z.W.V)
- Page numbers right-aligned
- Hierarchical section numbering
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict


@dataclass
class TOCEntry:
    """Single entry in the table of contents."""
    section_id: str  # e.g., "4.2.6.3.1"
    title: str
    page: int
    level: int  # Depth in hierarchy (1-5)
    parent: Optional[str] = None  # Parent section ID
    chapter: Optional[int] = None
    chapter_title: Optional[str] = None

    @property
    def full_title(self) -> str:
        """Get full section title with number."""
        return f"{self.section_id} {self.title}"


class TOCExtractor:
    """Extract table of contents from PCIe spec text."""

    # Pattern: Section number + title + page
    # Example: "1.2.3 Some Title.............................123"
    # Or: "1.2.3 Some Title 123"
    TOC_PATTERN = re.compile(
        r'^(\d+(?:\.\d+)*)\s+(.+?)\s*\.{3,}\s*(\d+)$|'  # With dots
        r'^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)$',  # Without dots
        re.MULTILINE
    )

    # Chapter titles (to extract chapter info)
    CHAPTER_PATTERN = re.compile(
        r'^(\d+)\.\s+(.+?)\s*\.{3,}\s*(\d+)$|'
        r'^(\d+)\.\s+(.+?)\s+(\d+)$',
        re.MULTILINE
    )

    def __init__(self, spec_text_path: str):
        """
        Initialize TOC extractor.

        Args:
            spec_text_path: Path to extracted spec text
        """
        self.spec_text_path = Path(spec_text_path)
        self.entries: List[TOCEntry] = []
        self.section_map: Dict[str, TOCEntry] = {}

    def extract(self) -> List[TOCEntry]:
        """
        Extract TOC from spec text.

        Returns:
            List of TOC entries in document order
        """
        if not self.spec_text_path.exists():
            raise FileNotFoundError(f"Spec text not found: {self.spec_text_path}")

        with open(self.spec_text_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Find TOC section - usually near the beginning
        # Look for "Table of Contents" or "Contents"
        toc_start = text.find("Table of Contents")
        if toc_start == -1:
            toc_start = text.find("Contents\n")
        if toc_start == -1:
            toc_start = 0

        # TOC typically ends before "1. Introduction" content starts
        # Look for a reasonable endpoint (e.g., first chapter content)
        toc_end = text.find("1.1 ", toc_start + 100)  # Skip the TOC entry itself
        if toc_end == -1:
            toc_end = min(toc_start + 50000, len(text))  # ~800 lines

        toc_text = text[toc_start:toc_end]

        # Extract all TOC entries
        chapter_titles = {}  # Map chapter number to title

        for match in self.TOC_PATTERN.finditer(toc_text):
            # Handle both pattern groups
            if match.group(1):  # With dots
                section_id = match.group(1)
                title = match.group(2).strip()
                page = int(match.group(3))
            else:  # Without dots
                section_id = match.group(4)
                title = match.group(5).strip()
                page = int(match.group(6))

            # Calculate level (depth)
            level = section_id.count('.') + 1

            # Determine chapter
            chapter_num = int(section_id.split('.')[0])

            # Track chapter titles
            if level == 1:
                chapter_titles[chapter_num] = title

            # Determine parent section
            parent = self._get_parent_section(section_id)

            # Get chapter title
            chapter_title = chapter_titles.get(chapter_num)

            entry = TOCEntry(
                section_id=section_id,
                title=title,
                page=page,
                level=level,
                parent=parent,
                chapter=chapter_num,
                chapter_title=chapter_title
            )

            self.entries.append(entry)
            self.section_map[section_id] = entry

        return self.entries

    def _get_parent_section(self, section_id: str) -> Optional[str]:
        """
        Get parent section ID.

        Example: "4.2.6.3.1" -> "4.2.6.3"
        """
        parts = section_id.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])

    def get_section(self, section_id: str) -> Optional[TOCEntry]:
        """Look up section by ID."""
        return self.section_map.get(section_id)

    def get_children(self, section_id: str) -> List[TOCEntry]:
        """Get immediate children of a section."""
        return [
            entry for entry in self.entries
            if entry.parent == section_id
        ]

    def get_siblings(self, section_id: str) -> List[TOCEntry]:
        """Get sibling sections (same parent, same level)."""
        entry = self.section_map.get(section_id)
        if not entry:
            return []

        return [
            e for e in self.entries
            if e.parent == entry.parent and e.section_id != section_id
        ]

    def get_section_range(self, section_id: str) -> tuple[int, int]:
        """
        Get page range for a section.

        Returns:
            (start_page, end_page) tuple
        """
        entry = self.section_map.get(section_id)
        if not entry:
            return (0, 0)

        start_page = entry.page

        # Find end page by looking at next sibling or parent's next sibling
        # This is approximate
        next_entry = self._get_next_entry(entry)
        if next_entry:
            end_page = next_entry.page - 1
        else:
            end_page = start_page + 10  # Default estimate

        return (start_page, end_page)

    def _get_next_entry(self, entry: TOCEntry) -> Optional[TOCEntry]:
        """Get the next entry in document order."""
        try:
            idx = self.entries.index(entry)
            if idx + 1 < len(self.entries):
                return self.entries[idx + 1]
        except ValueError:
            pass
        return None

    def get_chapter_sections(self, chapter: int) -> List[TOCEntry]:
        """Get all sections in a chapter."""
        return [
            entry for entry in self.entries
            if entry.chapter == chapter
        ]

    def save_to_json(self, output_path: str):
        """
        Save TOC to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'entries': [asdict(entry) for entry in self.entries],
            'total_sections': len(self.entries),
            'chapters': list(set(e.chapter for e in self.entries if e.chapter))
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved {len(self.entries)} TOC entries to {output_path}")

    def print_tree(self, max_level: int = 3):
        """Print TOC as a tree (for debugging)."""
        for entry in self.entries:
            if entry.level <= max_level:
                indent = "  " * (entry.level - 1)
                print(f"{indent}{entry.section_id} {entry.title} (p. {entry.page})")


def main():
    """CLI entry point for TOC extractor."""
    import sys

    # Default paths
    spec_text_path = Path(__file__).parent.parent.parent.parent / "pcie_spec_full_text.txt"
    output_path = Path(__file__).parent.parent.parent / "data" / "toc" / "toc.json"

    # Allow override from command line
    if len(sys.argv) > 1:
        spec_text_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    print(f"Extracting TOC from: {spec_text_path}")

    extractor = TOCExtractor(str(spec_text_path))
    entries = extractor.extract()

    print(f"Found {len(entries)} TOC entries")

    # Print sample
    print("\nChapter structure:")
    for entry in entries[:15]:  # First 15 entries
        indent = "  " * (entry.level - 1)
        print(f"{indent}{entry.section_id} {entry.title} (p. {entry.page})")

    # Save to JSON
    extractor.save_to_json(str(output_path))


if __name__ == "__main__":
    main()
