# PCIe MCP Server

MCP (Model Context Protocol) server for PCIe 5.0 specification queries and firmware intelligence.

## Structure

```
mcp/
├── src/
│   ├── parsers/         # PDF parsing and register extraction
│   ├── embeddings/      # Chunking and vector embedding generation
│   ├── tools/           # MCP tool implementations
│   └── server.py        # Main MCP server
├── data/
│   ├── registers/       # Parsed register database
│   ├── chunks/          # Spec chunks for RAG
│   └── toc/             # Table of contents index
├── tests/               # Unit tests
└── requirements.txt     # Python dependencies
```

## Features

### Phase 1: Core Data Preparation
- **Register Parsing**: Extract all PCIe register definitions from spec PDF
- **Spec Chunking**: Split spec into semantic chunks using TOC structure
- **Vector Embeddings**: Generate embeddings for semantic search
- **TOC Extraction**: Build hierarchical section index

### Phase 2: MCP Tools
- `lookup_register`: Fast register definition lookup
- `query_ltssm`: LTSSM state machine queries
- `search_section`: Section-aware semantic search
- `get_error_info`: Error handling information
- `get_cross_references`: Section dependency graph

## Usage

### Setup
```bash
cd mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run data preparation
```bash
# Parse registers from spec
python -m src.parsers.register_parser

# Generate embeddings
python -m src.embeddings.chunker

# Extract TOC
python -m src.parsers.toc_extractor
```

### Run MCP server
```bash
python -m src.server
```

## Development

Run tests:
```bash
pytest tests/
```

## Architecture

Based on the analysis in `PCIe_doc_summary.md`:
- Multi-strategy retrieval: structured (registers) + vector (narrative) + hybrid (state machines)
- Section-aware chunking using TOC structure
- Quality metadata per chunk
- Cross-reference indexing
