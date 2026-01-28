#!/usr/bin/env python3
"""
Comprehensive structural analysis of PCIe 5.0 Base Specification PDF.
This script analyzes the document to inform MCP server design decisions.
"""

import pdfplumber
import PyPDF2
import re
from collections import defaultdict, Counter
from pathlib import Path
import json

PDF_PATH = "SYkDTqhOLhpUTnMx.pdf"
OUTPUT_PATH = "PCIe_doc_summary.md"

def analyze_pdf_structure():
    """Main analysis orchestrator"""
    print("=" * 80)
    print("PCIe 5.0 Specification - Comprehensive Structural Analysis")
    print("=" * 80)

    results = {
        'metadata': {},
        'toc': [],
        'content_types': defaultdict(list),
        'table_samples': [],
        'text_quality': {},
        'section_patterns': {},
        'cross_references': [],
        'key_sections': []
    }

    # Open PDF with both libraries
    with pdfplumber.open(PDF_PATH) as pdf_plumber:
        with open(PDF_PATH, 'rb') as pdf_file:
            pdf_pypdf = PyPDF2.PdfReader(pdf_file)

            # 1. Extract metadata
            print("\n[1/8] Extracting metadata...")
            results['metadata'] = extract_metadata(pdf_plumber, pdf_pypdf)

            # 2. Build Table of Contents
            print("\n[2/8] Building Table of Contents...")
            results['toc'] = extract_toc(pdf_plumber, pdf_pypdf)

            # 3. Identify content types across pages
            print("\n[3/8] Analyzing content types...")
            results['content_types'] = analyze_content_types(pdf_plumber)

            # 4. Sample tables for quality assessment
            print("\n[4/8] Sampling tables for extraction quality...")
            results['table_samples'] = sample_tables(pdf_plumber)

            # 5. Assess text extraction quality by page range
            print("\n[5/8] Assessing text extraction quality...")
            results['text_quality'] = assess_text_quality(pdf_plumber)

            # 6. Identify section formatting patterns
            print("\n[6/8] Identifying section patterns...")
            results['section_patterns'] = identify_patterns(pdf_plumber)

            # 7. Extract cross-reference patterns
            print("\n[7/8] Extracting cross-reference patterns...")
            results['cross_references'] = extract_cross_references(pdf_plumber)

            # 8. Identify key sections for hardware engineers
            print("\n[8/8] Identifying key sections...")
            results['key_sections'] = identify_key_sections(pdf_plumber, results['toc'])

    # Generate markdown report
    print("\n[FINAL] Generating markdown report...")
    generate_report(results)

    print(f"\n✅ Analysis complete! Report written to: {OUTPUT_PATH}")
    return results


def extract_metadata(pdf_plumber, pdf_pypdf):
    """Extract basic PDF metadata"""
    metadata = {
        'total_pages': len(pdf_plumber.pages),
        'pdf_version': pdf_pypdf.metadata.get('/Producer', 'Unknown') if pdf_pypdf.metadata else 'Unknown',
        'creation_date': pdf_pypdf.metadata.get('/CreationDate', 'Unknown') if pdf_pypdf.metadata else 'Unknown',
        'title': pdf_pypdf.metadata.get('/Title', 'Unknown') if pdf_pypdf.metadata else 'Unknown',
    }

    # Get page dimensions from first page
    first_page = pdf_plumber.pages[0]
    metadata['page_width'] = first_page.width
    metadata['page_height'] = first_page.height

    print(f"   Total pages: {metadata['total_pages']}")
    return metadata


def extract_toc(pdf_plumber, pdf_pypdf):
    """Extract Table of Contents with page mappings"""
    toc = []

    # Try to get outlines/bookmarks from PyPDF2
    try:
        outlines = pdf_pypdf.outline if hasattr(pdf_pypdf, 'outline') else []
        toc = parse_outlines(outlines, pdf_pypdf)
        print(f"   Found {len(toc)} TOC entries from PDF bookmarks")
    except Exception as e:
        print(f"   Warning: Could not extract bookmarks: {e}")

    # If no bookmarks, try parsing TOC pages manually
    if not toc:
        print("   Attempting manual TOC extraction from early pages...")
        toc = extract_toc_manual(pdf_plumber)

    return toc


def parse_outlines(outlines, pdf_reader, level=0):
    """Recursively parse PDF outline structure"""
    toc_items = []

    for item in outlines:
        if isinstance(item, list):
            # Nested items
            toc_items.extend(parse_outlines(item, pdf_reader, level + 1))
        else:
            try:
                # Get title and page number
                title = item.get('/Title', 'Untitled')

                # Try to get destination page
                page_num = None
                if '/Page' in item:
                    page_ref = item['/Page']
                    if hasattr(page_ref, 'idnum'):
                        page_num = pdf_reader.get_page_number(page_ref) + 1

                toc_items.append({
                    'level': level,
                    'title': title,
                    'page': page_num
                })
            except Exception as e:
                print(f"   Warning: Could not parse outline item: {e}")
                continue

    return toc_items


def extract_toc_manual(pdf_plumber):
    """Manually extract TOC by parsing early pages for chapter/section headers"""
    toc = []

    # Look at pages 10-50 for TOC (typical location)
    for page_num in range(min(10, len(pdf_plumber.pages)), min(50, len(pdf_plumber.pages))):
        page = pdf_plumber.pages[page_num]
        text = page.extract_text()

        if not text:
            continue

        # Look for TOC-like patterns: "Chapter X" or "Section X.Y"
        lines = text.split('\n')
        for line in lines:
            # Match patterns like "1.2.3 Introduction ........ 45"
            match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+?)\s+\.{2,}\s*(\d+)$', line.strip())
            if match:
                section_num, title, page_ref = match.groups()
                level = section_num.count('.')
                toc.append({
                    'level': level,
                    'title': f"{section_num} {title.strip()}",
                    'page': int(page_ref)
                })

    if toc:
        print(f"   Manually extracted {len(toc)} TOC entries")

    return toc


def analyze_content_types(pdf_plumber):
    """Analyze different content types across pages"""
    content_types = defaultdict(list)

    # Sample every 50 pages to get distribution
    sample_pages = range(0, len(pdf_plumber.pages), 50)

    for page_num in sample_pages:
        page = pdf_plumber.pages[page_num]

        # Check for tables
        tables = page.extract_tables()
        if tables and len(tables) > 0:
            content_types['tables_found'].append(page_num + 1)

        # Check for figures (look for "Figure" keyword)
        text = page.extract_text()
        if text and 'Figure' in text:
            content_types['figures_found'].append(page_num + 1)

        # Check for code blocks (monospace patterns, hex values)
        if text and re.search(r'0x[0-9A-Fa-f]{2,}', text):
            content_types['hex_values'].append(page_num + 1)

        # Check for register definitions (common pattern)
        if text and re.search(r'(Register|Bit|Field|Offset).*:', text, re.IGNORECASE):
            content_types['register_definitions'].append(page_num + 1)

    print(f"   Pages with tables: {len(content_types['tables_found'])}")
    print(f"   Pages with figures: {len(content_types['figures_found'])}")
    print(f"   Pages with hex values: {len(content_types['hex_values'])}")
    print(f"   Pages with register definitions: {len(content_types['register_definitions'])}")

    return dict(content_types)


def sample_tables(pdf_plumber):
    """Sample tables from different sections to assess extraction quality"""
    samples = []

    # Sample strategy: get tables from early, middle, late sections
    sample_ranges = [
        (50, 150, "Early"),
        (400, 600, "Middle"),
        (900, 1100, "Late")
    ]

    tables_found = 0
    for start, end, label in sample_ranges:
        if tables_found >= 15:
            break

        for page_num in range(start, min(end, len(pdf_plumber.pages))):
            if tables_found >= 15:
                break

            page = pdf_plumber.pages[page_num]
            tables = page.extract_tables()

            if tables:
                for table_idx, table in enumerate(tables):
                    if tables_found >= 15:
                        break

                    samples.append({
                        'page': page_num + 1,
                        'section': label,
                        'table_index': table_idx,
                        'rows': len(table) if table else 0,
                        'cols': len(table[0]) if table and len(table) > 0 else 0,
                        'sample_rows': table[:3] if table else []  # First 3 rows
                    })
                    tables_found += 1

    print(f"   Sampled {len(samples)} tables")
    return samples


def assess_text_quality(pdf_plumber):
    """Assess text extraction quality across page ranges"""
    quality_zones = {}

    # Sample pages across the document
    page_ranges = [
        (0, 100, "Pages 1-100"),
        (100, 300, "Pages 101-300"),
        (300, 600, "Pages 301-600"),
        (600, 900, "Pages 601-900"),
        (900, len(pdf_plumber.pages), f"Pages 901-{len(pdf_plumber.pages)}")
    ]

    for start, end, label in page_ranges:
        sample_pages = range(start, min(end, len(pdf_plumber.pages)), 20)

        clean_count = 0
        garbled_count = 0
        empty_count = 0

        for page_num in sample_pages:
            page = pdf_plumber.pages[page_num]
            text = page.extract_text()

            if not text or len(text.strip()) < 50:
                empty_count += 1
            elif has_garbled_text(text):
                garbled_count += 1
            else:
                clean_count += 1

        total = clean_count + garbled_count + empty_count
        quality_zones[label] = {
            'clean': clean_count,
            'garbled': garbled_count,
            'empty': empty_count,
            'clean_percentage': round(clean_count / total * 100, 1) if total > 0 else 0
        }

    print(f"   Analyzed {len(page_ranges)} page ranges")
    return quality_zones


def has_garbled_text(text):
    """Detect garbled text patterns"""
    # High concentration of special characters
    special_char_ratio = len(re.findall(r'[^\w\s\.,;:\-\(\)]', text)) / max(len(text), 1)
    if special_char_ratio > 0.15:
        return True

    # Lots of single characters separated by spaces
    single_char_words = len(re.findall(r'\b\w\b', text))
    total_words = len(text.split())
    if total_words > 0 and single_char_words / total_words > 0.3:
        return True

    return False


def identify_patterns(pdf_plumber):
    """Identify consistent formatting patterns in the document"""
    patterns = {
        'section_headers': [],
        'register_tables': [],
        'state_machines': [],
        'timing_diagrams': []
    }

    # Sample pages to find patterns
    sample_pages = range(0, len(pdf_plumber.pages), 100)

    for page_num in sample_pages:
        page = pdf_plumber.pages[page_num]
        text = page.extract_text()

        if not text:
            continue

        # Look for section header patterns
        section_matches = re.findall(r'^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z\s]+)$', text, re.MULTILINE)
        if section_matches:
            patterns['section_headers'].extend([(page_num + 1, match) for match in section_matches[:2]])

        # Look for register table patterns
        if re.search(r'Bit\s+\d+', text, re.IGNORECASE) and re.search(r'Field|Description', text, re.IGNORECASE):
            patterns['register_tables'].append(page_num + 1)

        # Look for state machine descriptions
        if re.search(r'State\s+Machine', text, re.IGNORECASE) or re.search(r'L0|L1|L2|Recovery|Detect', text):
            patterns['state_machines'].append(page_num + 1)

        # Look for timing references
        if re.search(r'\d+\s*(ns|us|ms|μs)', text):
            patterns['timing_diagrams'].append(page_num + 1)

    print(f"   Found {len(patterns['section_headers'])} section header patterns")
    print(f"   Found {len(patterns['register_tables'])} pages with register tables")
    print(f"   Found {len(patterns['state_machines'])} pages with state machines")
    print(f"   Found {len(patterns['timing_diagrams'])} pages with timing info")

    return patterns


def extract_cross_references(pdf_plumber):
    """Extract cross-reference patterns in the document"""
    cross_refs = []

    # Sample pages
    sample_pages = range(0, len(pdf_plumber.pages), 50)

    for page_num in sample_pages:
        page = pdf_plumber.pages[page_num]
        text = page.extract_text()

        if not text:
            continue

        # Look for common cross-reference patterns
        refs = re.findall(r'(?:see|See|refer to|Refer to)\s+(Section|Chapter|Table|Figure)\s+([\d\.]+)', text)
        if refs:
            cross_refs.extend([(page_num + 1, ref) for ref in refs[:3]])

    print(f"   Found {len(cross_refs)} cross-reference examples")
    return cross_refs[:50]  # Limit to 50 examples


def identify_key_sections(pdf_plumber, toc):
    """Identify sections most important for hardware engineers"""
    key_sections = []

    # Keywords that indicate important sections for hardware engineers
    important_keywords = [
        'register', 'ltssm', 'link training', 'state machine',
        'timing', 'configuration space', 'capability', 'completion timeout',
        'flow control', 'transaction layer', 'data link layer', 'physical layer',
        'error', 'retry', 'ordered set'
    ]

    for toc_entry in toc:
        title_lower = toc_entry['title'].lower()

        # Check if title contains important keywords
        for keyword in important_keywords:
            if keyword in title_lower:
                key_sections.append({
                    'title': toc_entry['title'],
                    'page': toc_entry['page'],
                    'keyword': keyword,
                    'level': toc_entry['level']
                })
                break

    print(f"   Identified {len(key_sections)} key sections")
    return key_sections


def generate_report(results):
    """Generate comprehensive markdown report"""

    with open(OUTPUT_PATH, 'w') as f:
        f.write("# PCIe 5.0 Base Specification - Structural Analysis Report\n\n")
        f.write("*Generated for MCP Server Design*\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"This report analyzes the {results['metadata']['total_pages']}-page PCIe 5.0 Base Specification ")
        f.write("to inform the design of an MCP server that will provide intelligent querying capabilities ")
        f.write("for hardware engineers.\n\n")

        f.write("**Key Findings:**\n\n")
        f.write(f"- **Total Pages:** {results['metadata']['total_pages']}\n")
        f.write(f"- **TOC Entries:** {len(results['toc'])}\n")
        f.write(f"- **Tables Sampled:** {len(results['table_samples'])}\n")
        f.write(f"- **Key Sections Identified:** {len(results['key_sections'])}\n")
        f.write(f"- **Cross-references Found:** {len(results['cross_references'])}\n\n")

        # Metadata
        f.write("---\n\n")
        f.write("## 1. Document Metadata\n\n")
        f.write("```json\n")
        f.write(json.dumps(results['metadata'], indent=2))
        f.write("\n```\n\n")

        # Table of Contents
        f.write("---\n\n")
        f.write("## 2. Table of Contents Structure\n\n")

        if results['toc']:
            f.write(f"Extracted {len(results['toc'])} TOC entries. Hierarchical structure:\n\n")
            f.write("```\n")
            for entry in results['toc'][:100]:  # Limit to first 100
                indent = "  " * entry['level']
                page_str = f"pg.{entry['page']}" if entry['page'] else "pg.?"
                f.write(f"{indent}{entry['title']} ... {page_str}\n")
            if len(results['toc']) > 100:
                f.write(f"\n... ({len(results['toc']) - 100} more entries)\n")
            f.write("```\n\n")
        else:
            f.write("⚠️ Could not extract structured TOC from PDF bookmarks.\n")
            f.write("Manual parsing may be required.\n\n")

        # Content Types
        f.write("---\n\n")
        f.write("## 3. Content Type Distribution\n\n")

        for content_type, pages in results['content_types'].items():
            f.write(f"### {content_type.replace('_', ' ').title()}\n\n")
            f.write(f"Found on {len(pages)} sampled pages:\n")
            f.write(f"```\n{pages[:20]}\n```\n\n")

        # Table Samples
        f.write("---\n\n")
        f.write("## 4. Table Extraction Quality Assessment\n\n")
        f.write(f"Sampled {len(results['table_samples'])} tables from different sections:\n\n")

        for idx, sample in enumerate(results['table_samples'][:10], 1):
            f.write(f"### Sample {idx}: Page {sample['page']} ({sample['section']} section)\n\n")
            f.write(f"- **Dimensions:** {sample['rows']} rows × {sample['cols']} columns\n")
            f.write(f"- **Sample rows:**\n\n")
            f.write("```\n")
            for row in sample['sample_rows']:
                f.write(f"{row}\n")
            f.write("```\n\n")

        # Text Quality
        f.write("---\n\n")
        f.write("## 5. Text Extraction Quality by Page Range\n\n")

        for zone, quality in results['text_quality'].items():
            f.write(f"### {zone}\n\n")
            f.write(f"- **Clean text:** {quality['clean']} pages ({quality['clean_percentage']}%)\n")
            f.write(f"- **Garbled text:** {quality['garbled']} pages\n")
            f.write(f"- **Empty/unreadable:** {quality['empty']} pages\n\n")

        # Section Patterns
        f.write("---\n\n")
        f.write("## 6. Formatting Patterns Identified\n\n")

        f.write("### Section Headers\n\n")
        if results['section_patterns']['section_headers']:
            f.write("```\n")
            for page, match in results['section_patterns']['section_headers'][:10]:
                f.write(f"Page {page}: {match}\n")
            f.write("```\n\n")

        f.write("### Register Table Pages\n\n")
        f.write(f"Found register table patterns on pages: {results['section_patterns']['register_tables'][:20]}\n\n")

        f.write("### State Machine References\n\n")
        f.write(f"Found state machine content on pages: {results['section_patterns']['state_machines'][:20]}\n\n")

        f.write("### Timing Information\n\n")
        f.write(f"Found timing specifications on pages: {results['section_patterns']['timing_diagrams'][:20]}\n\n")

        # Cross-references
        f.write("---\n\n")
        f.write("## 7. Cross-Reference Patterns\n\n")
        f.write("Examples of how the spec references other sections:\n\n")
        f.write("```\n")
        for page, ref in results['cross_references'][:20]:
            f.write(f"Page {page}: {ref[0]} {ref[1]}\n")
        f.write("```\n\n")

        # Key Sections
        f.write("---\n\n")
        f.write("## 8. Key Sections for Hardware Engineers\n\n")
        f.write("Sections identified as high-priority for hardware engineering queries:\n\n")

        # Group by keyword
        keyword_groups = defaultdict(list)
        for section in results['key_sections']:
            keyword_groups[section['keyword']].append(section)

        for keyword, sections in sorted(keyword_groups.items()):
            f.write(f"### {keyword.title()}\n\n")
            for section in sections[:5]:
                page_str = f"pg.{section['page']}" if section['page'] else "pg.?"
                f.write(f"- {section['title']} ({page_str})\n")
            f.write("\n")

        # Recommendations
        f.write("---\n\n")
        f.write("## 9. MCP Server Design Recommendations\n\n")

        f.write("Based on this structural analysis:\n\n")

        f.write("### Recommendation 1: Multi-Strategy Retrieval\n\n")
        f.write("The document has diverse content types requiring different retrieval strategies:\n\n")
        f.write("- **Structured register lookups:** Use existing parsed register database (deterministic)\n")
        f.write("- **Narrative sections:** Vector embeddings for semantic search (RAG)\n")
        f.write("- **Tables:** Store table metadata separately, pre-process problematic tables\n")
        f.write("- **State machines:** Create structured graph representations\n\n")

        f.write("### Recommendation 2: TOC-Based Navigation\n\n")
        if results['toc']:
            f.write(f"With {len(results['toc'])} TOC entries extracted, we can:\n\n")
            f.write("- Implement section-aware search (\"find X in Chapter 7\")\n")
            f.write("- Build hierarchical context for better retrieval\n")
            f.write("- Create section summaries for quick navigation\n\n")
        else:
            f.write("⚠️ TOC extraction needs improvement. Consider:\n\n")
            f.write("- Manual TOC creation from spec\n")
            f.write("- Using heading detection heuristics\n")
            f.write("- Building TOC from section number patterns\n\n")

        f.write("### Recommendation 3: Text Quality Mitigation\n\n")
        f.write("Text extraction quality varies. Strategies:\n\n")
        f.write("- Pre-process and clean text during ingestion\n")
        f.write("- Store both raw and cleaned versions\n")
        f.write("- Flag low-quality pages for manual review\n")
        f.write("- Use OCR fallback for garbled sections\n\n")

        f.write("### Recommendation 4: Table Handling Strategy\n\n")
        f.write(f"With {len(results['table_samples'])} tables sampled:\n\n")
        f.write("- Many tables extract poorly (merged cells, alignment issues)\n")
        f.write("- Consider hybrid approach: store both extracted data and page images\n")
        f.write("- For critical register tables, use existing parsed database\n")
        f.write("- Return table images to users when extraction is unreliable\n\n")

        f.write("### Recommendation 5: Cross-Reference Graph\n\n")
        f.write(f"With {len(results['cross_references'])} cross-references found:\n\n")
        f.write("- Build a section dependency graph\n")
        f.write("- Enable \"deep dive\" queries that follow references\n")
        f.write("- Surface related sections automatically\n\n")

        f.write("### Recommendation 6: Section-Specific Tools\n\n")
        f.write(f"Identified {len(results['key_sections'])} high-priority sections. Create specialized MCP tools:\n\n")
        f.write("- `query_ltssm` - LTSSM state machine queries\n")
        f.write("- `lookup_register` - Register bit definitions (already have backend)\n")
        f.write("- `get_timing` - Timing requirements\n")
        f.write("- `search_section` - Semantic search within specific sections\n\n")

        # Implementation Notes
        f.write("---\n\n")
        f.write("## 10. Implementation Notes\n\n")

        f.write("### Text Extraction Issues Observed\n\n")
        f.write("- **Diagrams:** Completely garbled when extracted as text\n")
        f.write("- **Tables:** Cells merge, alignment breaks, headers get mangled\n")
        f.write("- **Equations:** Mathematical notation becomes unreadable\n")
        f.write("- **Multi-column layouts:** Text order gets scrambled\n\n")

        f.write("### Chunking Strategy\n\n")
        f.write("For vector database ingestion:\n\n")
        f.write("- **Chunk by section** - Use TOC structure for logical boundaries\n")
        f.write("- **Chunk size:** 500-1000 tokens (balance context vs. precision)\n")
        f.write("- **Overlap:** 100 tokens between chunks\n")
        f.write("- **Metadata:** Include section title, page number, content type\n\n")

        f.write("### Metadata to Track\n\n")
        f.write("For each chunk in vector DB:\n\n")
        f.write("```python\n")
        f.write("{\n")
        f.write("  'section': 'Section 4.2.6.3 - LTSSM',\n")
        f.write("  'page': 234,\n")
        f.write("  'content_type': 'narrative|table|register|state_machine',\n")
        f.write("  'keywords': ['LTSSM', 'L0', 'link training'],\n")
        f.write("  'has_tables': True,\n")
        f.write("  'has_diagrams': False,\n")
        f.write("  'quality': 'clean|garbled|empty'\n")
        f.write("}\n")
        f.write("```\n\n")

        # Conclusion
        f.write("---\n\n")
        f.write("## Conclusion\n\n")
        f.write("The PCIe 5.0 specification is a complex, multi-format document that requires ")
        f.write("a sophisticated multi-strategy retrieval approach. The MCP server should:\n\n")
        f.write("1. **Leverage existing structured data** (register database) for deterministic lookups\n")
        f.write("2. **Use vector search** for narrative sections and conceptual queries\n")
        f.write("3. **Handle table extraction carefully** with fallback to images when needed\n")
        f.write("4. **Exploit TOC structure** for section-aware navigation\n")
        f.write("5. **Build specialized tools** for high-frequency query types (LTSSM, registers, timing)\n\n")
        f.write("This analysis provides the foundation for designing effective MCP tools that solve ")
        f.write("the spec lookup friction (Pain Point A) identified in the design document.\n\n")


if __name__ == "__main__":
    results = analyze_pdf_structure()
