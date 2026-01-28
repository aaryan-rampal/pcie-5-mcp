#!/bin/bash
# Run all data preparation scripts in sequence

set -e  # Exit on error

# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "=== PCIe MCP Data Preparation ==="
echo ""

# Check if spec text exists
SPEC_TEXT="../analysis_scripts/pcie_spec_full_text.txt"
if [ ! -f "$SPEC_TEXT" ]; then
    echo "Error: $SPEC_TEXT not found"
    echo "Please ensure the PCIe spec text file exists"
    exit 1
fi

echo "Step 1: Parsing registers from PDF..."
python3 -m src.parsers.register_parser_pdf "../SYkDTqhOLhpUTnMx.pdf" data/registers/registers.json
echo ""

echo "Step 2: Extracting TOC..."
python3 -m src.parsers.toc_extractor "$SPEC_TEXT" data/toc/toc.json
echo ""

echo "Step 3: Chunking spec..."
python3 -m src.embeddings.chunker "$SPEC_TEXT" data/toc/toc.json data/chunks/chunks.json
echo ""

echo "Step 4: Extracting Linux kernel header constants..."
python3 -m src.parsers.linux_header_parser data/linux_headers/pci_constants.json
echo ""

echo "=== Data preparation complete! ==="
echo ""
echo "Generated files:"
echo "  - data/registers/registers.json"
echo "  - data/toc/toc.json"
echo "  - data/chunks/chunks.json"
echo "  - data/linux_headers/pci_constants.json"
echo ""
echo "You can now run the MCP server with:"
echo "  python -m src.server"
