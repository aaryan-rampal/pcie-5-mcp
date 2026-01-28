#!/bin/bash
# Run all data preparation scripts in sequence

set -e  # Exit on error

echo "=== PCIe MCP Data Preparation ==="
echo ""

# Check if spec text exists
SPEC_TEXT="../pcie_spec_full_text.txt"
if [ ! -f "$SPEC_TEXT" ]; then
    echo "Error: $SPEC_TEXT not found"
    echo "Please ensure the PCIe spec text file is in the parent directory"
    exit 1
fi

echo "Step 1: Parsing registers..."
python -m src.parsers.register_parser "$SPEC_TEXT" data/registers/registers.json
echo ""

echo "Step 2: Extracting TOC..."
python -m src.parsers.toc_extractor "$SPEC_TEXT" data/toc/toc.json
echo ""

echo "Step 3: Chunking spec..."
python -m src.embeddings.chunker "$SPEC_TEXT" data/toc/toc.json data/chunks/chunks.json
echo ""

echo "=== Data preparation complete! ==="
echo ""
echo "Generated files:"
echo "  - data/registers/registers.json"
echo "  - data/toc/toc.json"
echo "  - data/chunks/chunks.json"
echo ""
echo "You can now run the MCP server with:"
echo "  python -m src.server"
