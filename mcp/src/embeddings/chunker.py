"""
Spec Chunking and Embedding Generation

Section-aware chunking strategy based on TOC structure.
Generates embeddings for semantic search (RAG).

Based on PCIe_doc_summary.md recommendations:
- Chunk by section using TOC structure (500-800 tokens)
- Overlap: 100 tokens for context preservation
- Include metadata: section_id, chapter, page, content_type
- Quality assessment per chunk
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class Chunk:
    """A chunk of spec text with metadata."""
    chunk_id: str
    text: str
    section_id: Optional[str]
    section_title: Optional[str]
    chapter: Optional[int]
    chapter_title: Optional[str]
    page_start: Optional[int]
    page_end: Optional[int]
    content_type: str  # narrative, register, ltssm_state, table, diagram
    quality: str  # clean, garbled, mixed
    has_diagrams: bool = False
    has_tables: bool = False
    keywords: List[str] = None
    token_count: Optional[int] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class SpecChunker:
    """Chunk PCIe specification text using TOC-based strategy."""

    # Content type detection patterns
    LTSSM_KEYWORDS = {'ltssm', 'link training', 'detect', 'polling', 'configuration', 'recovery'}
    REGISTER_KEYWORDS = {'register', 'offset', 'bit', 'field', 'attribute', 'rw', 'ro'}
    ERROR_KEYWORDS = {'error', 'correctable', 'uncorrectable', 'fatal', 'non-fatal'}

    # Quality indicators
    GARBLED_INDICATORS = ['tib', 'redro', 'etyB', 'PLT']  # Common garbled patterns

    def __init__(self, spec_text_path: str, toc_path: str):
        """
        Initialize chunker.

        Args:
            spec_text_path: Path to extracted spec text
            toc_path: Path to TOC JSON
        """
        self.spec_text_path = Path(spec_text_path)
        self.toc_path = Path(toc_path)
        self.chunks: List[Chunk] = []
        self.toc_data = None

        # Load TOC
        if self.toc_path.exists():
            with open(self.toc_path, 'r') as f:
                self.toc_data = json.load(f)

    def chunk(self, target_tokens: int = 600, overlap_tokens: int = 100) -> List[Chunk]:
        """
        Chunk spec text using section-aware strategy.

        Args:
            target_tokens: Target chunk size in tokens (~600)
            overlap_tokens: Overlap between chunks (~100)

        Returns:
            List of chunks with metadata
        """
        if not self.spec_text_path.exists():
            raise FileNotFoundError(f"Spec text not found: {self.spec_text_path}")

        with open(self.spec_text_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # If we have TOC, use section-aware chunking
        if self.toc_data:
            chunks = self._chunk_by_sections(text, target_tokens, overlap_tokens)
        else:
            # Fallback: simple sliding window
            chunks = self._chunk_sliding_window(text, target_tokens, overlap_tokens)

        self.chunks = chunks
        return chunks

    def _chunk_by_sections(self, text: str, target_tokens: int, overlap: int) -> List[Chunk]:
        """Chunk using TOC section boundaries."""
        chunks = []

        entries = self.toc_data.get('entries', [])

        for i, entry in enumerate(entries):
            section_id = entry['section_id']
            section_title = entry['title']
            page_start = entry['page']
            chapter = entry.get('chapter')
            chapter_title = entry.get('chapter_title')

            # Determine page end (next section's start)
            if i + 1 < len(entries):
                page_end = entries[i + 1]['page'] - 1
            else:
                page_end = page_start + 10  # Estimate

            # Extract section text
            section_text = self._extract_section_text(text, section_id, section_title)

            if not section_text or len(section_text) < 100:
                continue

            # Estimate tokens (rough: 1 token ~= 4 chars)
            estimated_tokens = len(section_text) // 4

            # If section is small enough, make it one chunk
            if estimated_tokens <= target_tokens:
                chunk = self._create_chunk(
                    text=section_text,
                    section_id=section_id,
                    section_title=section_title,
                    chapter=chapter,
                    chapter_title=chapter_title,
                    page_start=page_start,
                    page_end=page_end,
                    chunk_num=0
                )
                chunks.append(chunk)
            else:
                # Split large section into sub-chunks
                sub_chunks = self._split_text(
                    section_text,
                    target_tokens * 4,  # Convert to chars
                    overlap * 4
                )

                for j, sub_text in enumerate(sub_chunks):
                    chunk = self._create_chunk(
                        text=sub_text,
                        section_id=section_id,
                        section_title=section_title,
                        chapter=chapter,
                        chapter_title=chapter_title,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_num=j
                    )
                    chunks.append(chunk)

        return chunks

    def _extract_section_text(self, text: str, section_id: str, title: str) -> str:
        """
        Extract text for a specific section.

        Looks for section header and extracts until next section.
        """
        # Pattern: section number + title
        # Example: "4.2.6.3.1 Detect.Quiet"
        pattern = re.escape(section_id) + r'\s+' + re.escape(title[:30])  # First 30 chars
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            return ""

        start = match.start()

        # Find next section (same or higher level)
        # This is approximate - look for next numbered section
        next_section_pattern = r'\n\d+(?:\.\d+)*\s+[A-Z]'
        next_match = re.search(next_section_pattern, text[start + 50:])

        if next_match:
            end = start + 50 + next_match.start()
        else:
            end = min(start + 5000, len(text))  # Max 5000 chars

        return text[start:end].strip()

    def _split_text(self, text: str, target_size: int, overlap: int) -> List[str]:
        """Split text into chunks with overlap."""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + target_size, len(text))

            # Try to break at paragraph or sentence boundary
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + target_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = text.rfind('. ', start, end)
                    if sent_break > start + target_size // 2:
                        end = sent_break + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)

            start = end - overlap

        return chunks

    def _create_chunk(
        self,
        text: str,
        section_id: str,
        section_title: str,
        chapter: int,
        chapter_title: str,
        page_start: int,
        page_end: int,
        chunk_num: int
    ) -> Chunk:
        """Create a chunk with metadata."""
        chunk_id = f"{section_id}-{chunk_num}"

        # Detect content type
        content_type = self._detect_content_type(text)

        # Assess quality
        quality = self._assess_quality(text)

        # Detect features
        has_diagrams = self._has_diagrams(text)
        has_tables = self._has_tables(text)

        # Extract keywords
        keywords = self._extract_keywords(text)

        # Estimate tokens
        token_count = len(text) // 4

        return Chunk(
            chunk_id=chunk_id,
            text=text,
            section_id=section_id,
            section_title=section_title,
            chapter=chapter,
            chapter_title=chapter_title,
            page_start=page_start,
            page_end=page_end,
            content_type=content_type,
            quality=quality,
            has_diagrams=has_diagrams,
            has_tables=has_tables,
            keywords=keywords,
            token_count=token_count
        )

    def _detect_content_type(self, text: str) -> str:
        """Detect type of content in chunk."""
        text_lower = text.lower()

        # Check for LTSSM content
        if any(kw in text_lower for kw in self.LTSSM_KEYWORDS):
            return "ltssm_state"

        # Check for register content
        if any(kw in text_lower for kw in self.REGISTER_KEYWORDS):
            if 'offset' in text_lower and ('bit' in text_lower or 'field' in text_lower):
                return "register"

        # Check for error handling
        if any(kw in text_lower for kw in self.ERROR_KEYWORDS):
            return "error_handling"

        # Check for tables
        if self._has_tables(text):
            return "table"

        return "narrative"

    def _assess_quality(self, text: str) -> str:
        """Assess text quality (clean vs garbled)."""
        # Check for garbled indicators
        garbled_count = sum(1 for indicator in self.GARBLED_INDICATORS if indicator in text)

        if garbled_count >= 3:
            return "garbled"
        elif garbled_count > 0:
            return "mixed"
        else:
            return "clean"

    def _has_diagrams(self, text: str) -> bool:
        """Check if chunk likely contains diagrams."""
        # Diagrams often have ASCII art patterns
        lines = text.split('\n')
        ascii_art_lines = sum(1 for line in lines if re.search(r'[│├└┌┐┘─┬┴┼]', line))
        return ascii_art_lines > 2

    def _has_tables(self, text: str) -> bool:
        """Check if chunk contains tables."""
        # Tables often have aligned columns with multiple spaces
        lines = text.split('\n')
        table_lines = sum(1 for line in lines if re.search(r'\s{4,}', line))
        return table_lines > 3

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from chunk."""
        keywords = []

        # Check for common important terms
        important_terms = [
            'ltssm', 'register', 'error', 'timeout', 'retry',
            'configuration', 'capability', 'flow control', 'ordered set'
        ]

        text_lower = text.lower()
        for term in important_terms:
            if term in text_lower:
                keywords.append(term)

        return keywords[:5]  # Limit to top 5

    def _chunk_sliding_window(self, text: str, target_tokens: int, overlap: int) -> List[Chunk]:
        """Fallback: simple sliding window chunking."""
        chunks = []
        target_size = target_tokens * 4  # Chars
        overlap_size = overlap * 4

        sub_chunks = self._split_text(text, target_size, overlap_size)

        for i, chunk_text in enumerate(sub_chunks):
            chunk = Chunk(
                chunk_id=f"chunk-{i}",
                text=chunk_text,
                section_id=None,
                section_title=None,
                chapter=None,
                chapter_title=None,
                page_start=None,
                page_end=None,
                content_type=self._detect_content_type(chunk_text),
                quality=self._assess_quality(chunk_text),
                token_count=len(chunk_text) // 4
            )
            chunks.append(chunk)

        return chunks

    def save_chunks(self, output_path: str):
        """Save chunks to JSON."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'chunks': [asdict(chunk) for chunk in self.chunks],
            'total_chunks': len(self.chunks),
            'stats': self._get_stats()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved {len(self.chunks)} chunks to {output_path}")

    def _get_stats(self) -> Dict:
        """Get chunking statistics."""
        content_types = {}
        for chunk in self.chunks:
            content_types[chunk.content_type] = content_types.get(chunk.content_type, 0) + 1

        return {
            'total_chunks': len(self.chunks),
            'content_types': content_types,
            'avg_tokens': sum(c.token_count for c in self.chunks if c.token_count) // len(self.chunks) if self.chunks else 0
        }


def main():
    """CLI entry point for chunker."""
    import sys

    # Default paths
    spec_text_path = Path(__file__).parent.parent.parent.parent / "pcie_spec_full_text.txt"
    toc_path = Path(__file__).parent.parent.parent / "data" / "toc" / "toc.json"
    output_path = Path(__file__).parent.parent.parent / "data" / "chunks" / "chunks.json"

    # Allow override
    if len(sys.argv) > 1:
        spec_text_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        toc_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])

    print(f"Chunking spec from: {spec_text_path}")
    print(f"Using TOC from: {toc_path}")

    chunker = SpecChunker(str(spec_text_path), str(toc_path))
    chunks = chunker.chunk(target_tokens=600, overlap_tokens=100)

    print(f"Created {len(chunks)} chunks")
    print(f"\nStats: {chunker._get_stats()}")

    # Save chunks
    chunker.save_chunks(str(output_path))


if __name__ == "__main__":
    main()
