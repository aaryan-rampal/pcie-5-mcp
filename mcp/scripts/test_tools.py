#!/usr/bin/env python3
"""
Simple test script for MCP tools (without full MCP server).

Tests the underlying tool implementations directly.
"""

from pathlib import Path
from src.tools.register_lookup import RegisterLookupTool
from src.tools.section_search import SectionSearchTool
import json


def test_register_lookup():
    """Test register lookup tool."""
    print("=" * 60)
    print("Testing Register Lookup Tool")
    print("=" * 60)

    tool = RegisterLookupTool("data/registers/registers.json")

    # Test 1: Lookup by name
    print("\n1. Lookup 'Device Control' register:")
    result = tool.lookup(name="Device Control")
    print(json.dumps(result, indent=2))

    # Test 2: Lookup specific field
    print("\n2. Lookup 'Max Payload Size' field:")
    result = tool.lookup(name="Device Control", field="Max_Payload_Size")
    print(json.dumps(result, indent=2))

    # Test 3: List all registers
    print("\n3. List all registers:")
    result = tool.list_registers()
    print(f"Total registers: {result['total']}")
    if result['registers']:
        print(f"First 5 registers:")
        for reg in result['registers'][:5]:
            print(f"  - {reg['name']} (Offset {reg['offset']})")


def test_section_search():
    """Test section search tool."""
    print("\n" + "=" * 60)
    print("Testing Section Search Tool")
    print("=" * 60)

    tool = SectionSearchTool("data/toc/toc.json", "data/chunks/chunks.json")

    # Test 1: Search for LTSSM
    print("\n1. Search for 'LTSSM':")
    result = tool.search(query="LTSSM", chapter=4)
    print(f"Found {result['total_results']} results")
    if result['results']:
        print(f"First result:")
        print(f"  Section: {result['results'][0]['section_id']} - {result['results'][0]['section_title']}")
        print(f"  Page: {result['results'][0]['page_start']}")

    # Test 2: Get specific section
    print("\n2. Get section 4.2.6 (if exists):")
    result = tool.get_section(section_id="4.2.6")
    if 'error' not in result:
        print(f"  Title: {result['title']}")
        print(f"  Page: {result['page']}")
        print(f"  Chunks: {len(result['chunks'])}")
    else:
        print(f"  {result['error']}")

    # Test 3: List chapter 4 sections
    print("\n3. List Chapter 4 sections:")
    result = tool.list_sections(chapter=4)
    print(f"Total sections in Chapter 4: {result['total']}")
    if result['sections']:
        print(f"First 5 sections:")
        for section in result['sections'][:5]:
            indent = "  " * (section['level'] - 1)
            print(f"  {indent}{section['section_id']} {section['title']}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PCIe MCP Tools Test Suite")
    print("=" * 60)

    # Check if data files exist
    data_dir = Path("data")
    if not data_dir.exists():
        print("\nError: data/ directory not found")
        print("Run run_parsers.sh first to generate data files")
        return

    try:
        test_register_lookup()
        test_section_search()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
