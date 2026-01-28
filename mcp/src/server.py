"""
PCIe MCP Server

MCP server providing tools for PCIe specification queries.

Tools:
- lookup_register: Fast register definition lookup
- search_section: Section-aware spec search
- get_section: Retrieve full section content
- list_sections: Browse TOC
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from tools.register_lookup import RegisterLookupTool
from tools.section_search import SectionSearchTool


# Paths to data files
DATA_DIR = Path(__file__).parent.parent / "data"
REGISTER_DB = DATA_DIR / "registers" / "registers.json"
TOC_FILE = DATA_DIR / "toc" / "toc.json"
CHUNKS_FILE = DATA_DIR / "chunks" / "chunks.json"


# Initialize tools
register_tool = RegisterLookupTool(str(REGISTER_DB))
section_tool = SectionSearchTool(str(TOC_FILE), str(CHUNKS_FILE))


# Create server
server = Server("pcie-spec-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="lookup_register",
            description=(
                "Look up PCIe configuration register definitions. "
                "Search by register name, offset, or specific field. "
                "Returns register structure with all bit fields and attributes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Register name (e.g., 'Device Control')"
                    },
                    "offset": {
                        "type": "string",
                        "description": "Hex offset (e.g., '08h')"
                    },
                    "field": {
                        "type": "string",
                        "description": "Specific bit field name (optional)"
                    }
                }
            }
        ),
        Tool(
            name="search_section",
            description=(
                "Search PCIe specification content with section-aware filtering. "
                "Performs keyword search across spec chunks with filters for "
                "section, chapter, and content type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "section": {
                        "type": "string",
                        "description": "Filter to specific section (e.g., '4.2.6')"
                    },
                    "chapter": {
                        "type": "integer",
                        "description": "Filter to chapter (1-10)"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Filter by content type (narrative, register, ltssm_state, etc.)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_section",
            description=(
                "Retrieve full content for a specific section by section ID. "
                "Returns section metadata and all associated text chunks."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section_id": {
                        "type": "string",
                        "description": "Section ID (e.g., '4.2.6.3')"
                    }
                },
                "required": ["section_id"]
            }
        ),
        Tool(
            name="list_sections",
            description=(
                "List all sections in the PCIe specification TOC. "
                "Optionally filter by chapter."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter": {
                        "type": "integer",
                        "description": "Filter by chapter (1-10)"
                    }
                }
            }
        ),
        Tool(
            name="list_registers",
            description="List all available PCIe configuration registers.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "lookup_register":
            result = register_tool.lookup(
                name=arguments.get("name"),
                offset=arguments.get("offset"),
                field=arguments.get("field")
            )

        elif name == "search_section":
            result = section_tool.search(
                query=arguments["query"],
                section=arguments.get("section"),
                chapter=arguments.get("chapter"),
                content_type=arguments.get("content_type")
            )

        elif name == "get_section":
            result = section_tool.get_section(
                section_id=arguments["section_id"]
            )

        elif name == "list_sections":
            result = section_tool.list_sections(
                chapter=arguments.get("chapter")
            )

        elif name == "list_registers":
            result = register_tool.list_registers()

        else:
            result = {"error": f"Unknown tool: {name}"}

        # Format result as text
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
