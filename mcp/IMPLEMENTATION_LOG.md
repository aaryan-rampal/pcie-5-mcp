# PCIe MCP Server - Implementation Log

## Summary

Built an MCP (Model Context Protocol) server for querying the PCIe 5.0 specification with focus on register definitions, table of contents navigation, and section-aware search.

**Status:** Initial implementation complete with working register parser and MCP server framework.

---

## What Works ✅

### 1. Register Parser (PDF-based)
- **File:** `src/parsers/register_parser_pdf.py`
- **Method:** pdfplumber table extraction from PDF
- **Results:** 36 registers identified, 26 with full bit field data
- **Examples:**
  - Device Control Register: 30 fields
  - Link Control Register: 8 fields
  - Device Capabilities Register: 39 fields

### 2. MCP Server
- **File:** `src/server.py`
- **Tools Exposed:**
  - `lookup_register` - Fast register definition lookup
  - `search_section` - Section-aware spec search (needs chunk data)
  - `get_section` - Retrieve section content (needs TOC data)
  - `list_sections` - Browse TOC (needs TOC data)
  - `list_registers` - List all registers ✅

### 3. Data Structure
- **Registers:** `data/registers/registers.json` - 36 registers with fields ✅
- **TOC:** `data/toc/toc.json` - Empty (parser needs fixing) ⚠️
- **Chunks:** `data/chunks/chunks.json` - Empty (depends on TOC) ⚠️

---

## Debugging Journey 🔍

### Problem 1: Text-Based Parser Failed
**Issue:** `pcie_mcp-c76`
**Symptom:** Regex found 306 register headers but `_parse_fields()` returned empty lists.
**Root Cause:** Extracted text had register tables spread across multiple lines with poor structure.

### Investigation: Text Extraction Format
**Issue:** `pcie_mcp-vnl`
**Discovery:**
- TOC on page 676 shows "7.5.1.1.1 Vendor ID Register (Offset 00h) ..... 685"
- Actual register definitions start on page 685+
- Bit field tables exist but are malformed in text extraction

### Decision: Use pdfplumber
**Issue:** `pcie_mcp-ozy`
**Rationale:**
- User suggested pdfplumber
- `PCIe_doc_summary.md` confirmed tables extract cleanly
- PDF file found at `../SYkDTqhOLhpUTnMx.pdf`

### Problem 2: Merged Table Cells
**Issue:** `pcie_mcp-2z2` → `pcie_mcp-x76`
**Symptom:** pdfplumber found 36 registers but 0 fields
**Root Cause:** PDF table extraction merged all columns into single cells per row
**Example:** `"0 Correctable Error Reporting Enable- Description RW"` all in one string

### Solution: Merged Cell Parser
**Issue:** `pcie_mcp-09n`
**Implementation:** Added `_parse_merged_table()` method
**Regex Pattern:** `^(\d+(?::\d+)?)\s+(.+?)\s+(RW|RO|RWC|...)$`
**Algorithm:**
1. Split merged cell text by newlines
2. Match each line as potential bit field
3. Extract bit number, field name/description, attribute

### Verification
**Issue:** `pcie_mcp-hvr`
**Result:** 26/36 registers have fields, parser working successfully

---

## Technical Decisions

### Why PDF Extraction Over Text?
- Text extraction from `pdfplumber.extract_text()` loses table structure
- Tables are critical for register bit field definitions
- `pdfplumber.extract_tables()` preserves row boundaries even if columns merge

### Why Regex for Merged Cells?
- PDF table extraction often merges columns in complex layouts
- Regex allows parsing of consistent patterns within merged cells
- Pattern `bit_num + description + attribute` is reliable across registers

### Register Parsing Strategy
```python
# Pattern matches: "0 Field Name - Description RW"
pattern = r'^(\d+(?::\d+)?)\s+(.+?)\s+(RW|RO|RWC|RW1C|...)$'

# For each table row:
#   1. Check if it's a register bit field table (header contains "Bit" + "Attribute")
#   2. Extract cell text (usually merged into one cell)
#   3. Split by newlines
#   4. Apply regex to each line
#   5. Create RegisterField objects
```

---

## What Needs Fixing ⚠️

### 1. TOC Extractor
**File:** `src/parsers/toc_extractor.py`
**Status:** Returns 0 entries
**Issue:** Regex patterns don't match actual TOC format in extracted text
**Example Format:**
```
1. Introduction.......89
  1.1 A Third Generation I/O Interconnect....89
  1.2 PCI Express Link.....90
```

**Fix Needed:** Debug regex patterns against actual text format

### 2. Chunker
**File:** `src/embeddings/chunker.py`
**Status:** Returns 0 chunks
**Dependency:** Requires working TOC extractor
**Strategy:** Section-aware chunking using TOC boundaries

### 3. Section Search
**Tool:** `search_section`
**Status:** Tool implemented but has no data
**Dependency:** Requires chunks to be generated

---

## Usage

### Setup
```bash
cd mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Data Preparation
```bash
./run_parsers.sh
```

**Current Output:**
- ✅ Registers: 36 found, 26 with fields
- ⚠️ TOC: 0 entries (needs fixing)
- ⚠️ Chunks: 0 created (depends on TOC)

### Test Tools
```bash
python test_tools.py
```

**Working:**
- Register lookup by name ✅
- Register lookup by offset ✅
- List all registers ✅

**Not Working (no data):**
- Section search ⚠️
- Get section ⚠️
- List sections ⚠️

---

## Files Created

### Parsers
- `src/parsers/register_parser_pdf.py` - PDF-based register parser ✅
- `src/parsers/toc_extractor.py` - TOC extraction (needs fixing) ⚠️
- `src/parsers/register_parser.py` - **REMOVED** (obsolete text-based approach)

### Tools
- `src/tools/register_lookup.py` - Register lookup tool ✅
- `src/tools/section_search.py` - Section search tool (no data) ⚠️

### Server
- `src/server.py` - Main MCP server ✅

### Scripts
- `run_parsers.sh` - Data preparation pipeline
- `test_tools.py` - CLI testing without MCP server

### Data
- `data/registers/registers.json` - 36 registers ✅
- `data/toc/toc.json` - Empty ⚠️
- `data/chunks/chunks.json` - Empty ⚠️

---

## Next Steps

1. **Fix TOC Extractor** - Debug regex patterns for actual text format
2. **Verify Chunker** - Once TOC works, test chunking strategy
3. **Test Full Pipeline** - Ensure all 3 steps produce data
4. **Test MCP Server** - Run with Claude Code or MCP inspector
5. **Add Vector Search** - Implement embeddings for semantic search
6. **Optimize Register Parser** - Parse more registers, improve field extraction accuracy

---

## Beads Issue Tracking

All work tracked in `.beads/` with full dependency chains:

```
pcie_mcp-c76 (Text parser failed)
    ↓
pcie_mcp-vnl (Investigated format)
    ↓
pcie_mcp-ozy (Decided on pdfplumber)
    ↓
pcie_mcp-2z2 (Implemented PDF parser)
    ↓
pcie_mcp-x76 (Debugged merged cells)
    ↓
pcie_mcp-09n (Implemented regex solution)
    ↓
pcie_mcp-hvr (Verified success)
```

Use `bd list --status closed` to see full history.

---

## Key Learnings

1. **PDF table extraction is non-trivial** - Even with pdfplumber, tables may have merged cells
2. **Text extraction loses structure** - Tables become unreadable in plain text
3. **Regex can parse merged cells** - Consistent patterns allow post-processing of merged data
4. **PCIe spec has 306 registers** - But only ~36 have full table definitions in Chapter 7 pages we scanned
5. **pdfplumber is powerful but quirky** - Need to handle both structured and merged table formats

---

**Date:** 2026-01-28
**Status:** MVP register parser complete, TOC/chunking pending
