"""
MCP Tool: Section Search

Section-aware search using TOC structure and chunks.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class SectionSearchTool:
    """Tool for searching spec by section."""

    def __init__(self, toc_path: str, chunks_path: str):
        """
        Initialize section search tool.

        Args:
            toc_path: Path to toc.json
            chunks_path: Path to chunks.json
        """
        self.toc_path = Path(toc_path)
        self.chunks_path = Path(chunks_path)

        self.toc = {}
        self.chunks = []
        self.section_map = {}

        # Load TOC
        if self.toc_path.exists():
            with open(self.toc_path, 'r') as f:
                data = json.load(f)
                self.toc = {e['section_id']: e for e in data.get('entries', [])}

        # Load chunks
        if self.chunks_path.exists():
            with open(self.chunks_path, 'r') as f:
                data = json.load(f)
                self.chunks = data.get('chunks', [])

                # Build section map
                for chunk in self.chunks:
                    section_id = chunk.get('section_id')
                    if section_id:
                        if section_id not in self.section_map:
                            self.section_map[section_id] = []
                        self.section_map[section_id].append(chunk)

    def search(
        self,
        query: str,
        section: Optional[str] = None,
        chapter: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for content in spec.

        Args:
            query: Search query
            section: Filter to specific section (e.g., "4.2.6")
            chapter: Filter to chapter (1-10)
            content_type: Filter by type (narrative, register, ltssm_state, etc.)

        Returns:
            Matching chunks with metadata
        """
        if not self.chunks:
            return {
                'error': 'Chunks not loaded',
                'hint': 'Run chunker first'
            }

        results = []
        query_lower = query.lower()

        for chunk in self.chunks:
            # Apply filters
            if section and not chunk.get('section_id', '').startswith(section):
                continue

            if chapter and chunk.get('chapter') != chapter:
                continue

            if content_type and chunk.get('content_type') != content_type:
                continue

            # Simple keyword search (TODO: upgrade to vector search)
            text_lower = chunk.get('text', '').lower()
            if query_lower in text_lower:
                results.append({
                    'chunk_id': chunk['chunk_id'],
                    'section_id': chunk.get('section_id'),
                    'section_title': chunk.get('section_title'),
                    'chapter': chunk.get('chapter'),
                    'page_start': chunk.get('page_start'),
                    'page_end': chunk.get('page_end'),
                    'content_type': chunk.get('content_type'),
                    'text_preview': chunk['text'][:300] + '...' if len(chunk['text']) > 300 else chunk['text']
                })

        return {
            'query': query,
            'filters': {
                'section': section,
                'chapter': chapter,
                'content_type': content_type
            },
            'total_results': len(results),
            'results': results[:10]  # Return top 10
        }

    def get_section(self, section_id: str) -> Dict[str, Any]:
        """
        Get full content for a specific section.

        Args:
            section_id: Section ID (e.g., "4.2.6.3")

        Returns:
            Section metadata and all chunks
        """
        if section_id not in self.toc:
            return {
                'error': f"Section '{section_id}' not found in TOC"
            }

        toc_entry = self.toc[section_id]
        chunks = self.section_map.get(section_id, [])

        return {
            'section_id': section_id,
            'title': toc_entry['title'],
            'chapter': toc_entry.get('chapter'),
            'page': toc_entry['page'],
            'level': toc_entry['level'],
            'chunks': chunks
        }

    def list_sections(self, chapter: Optional[int] = None) -> Dict[str, Any]:
        """
        List all sections.

        Args:
            chapter: Filter by chapter

        Returns:
            List of sections
        """
        sections = []

        for section_id, entry in self.toc.items():
            if chapter and entry.get('chapter') != chapter:
                continue

            sections.append({
                'section_id': section_id,
                'title': entry['title'],
                'chapter': entry.get('chapter'),
                'page': entry['page'],
                'level': entry['level']
            })

        return {
            'total': len(sections),
            'sections': sections
        }
