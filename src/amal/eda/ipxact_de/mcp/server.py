"""IP-XACT validation MCP server using the official MCP library.

This server provides IP-XACT XML validation capabilities through the Model Context Protocol (MCP).
It uses the official MCP Python library to handle the protocol implementation.
"""

import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import Any

from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

from amal.eda.ipxact_de.xml_validation import ValidationResult, validate_ipxact_xml

# Initialize the MCP server
app = Server("pyipxact-de-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for IP-XACT validation.

    Returns:
        List of available tools.
    """
    return [
        Tool(
            name="validate_xml",
            description="Validate an IP-XACT XML file against its Accellera XSD schema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative filesystem path to XML file."
                    }
                },
                "required": ["path"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls for IP-XACT validation.

    Args:
        name: Name of the tool to call.
        arguments: Tool arguments.

    Returns:
        Tool call result.

    Raises:
        ValueError: If the tool name is unknown.
    """
    if name == "validate_xml":
        return await _validate_xml_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _validate_xml_tool(arguments: dict[str, Any]) -> CallToolResult:
    """Handle the validate_xml tool call.

    Args:
        arguments: Tool arguments; must contain "path".

    Returns:
        Tool call result with validation information.

    Raises:
        ValueError: If path parameter is missing or invalid.
    """
    path_value = arguments.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("Parameter 'path' must be a non-empty string.")

    xml_path = Path(path_value)
    if not xml_path.exists():
        result = {
            "ok": False,
            "issues": [
                {
                    "message": f"File does not exist: {xml_path}",
                }
            ],
            "schema_path": None,
            "version": None,
            "standard": None,
            "root_element": None,
            "summary": "File not found",
        }
    else:
        logger.info("Validating IP-XACT XML: {}", xml_path)
        validation_result: ValidationResult = validate_ipxact_xml(xml_path)
        result = asdict(validation_result)
        result["summary"] = (
            "XML document is valid against the selected IP-XACT schema."
            if validation_result.ok
            else "XML document failed IP-XACT schema validation."
        )

    issues_list = result.get("issues", [])
    if not isinstance(issues_list, list):
        issues_list = []
    issues_count = len(issues_list)
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Validation result: {result['summary']}\n"
                     f"Standard: {result.get('standard', 'N/A')}\n"
                     f"Version: {result.get('version', 'N/A')}\n"
                     f"Root Element: {result.get('root_element', 'N/A')}\n"
                     f"Valid: {result['ok']}\n"
                     f"Issues: {issues_count} found"
            )
        ]
    )


def main() -> None:
    """Run the MCP server with stdio transport."""
    logger.info("Starting IP-XACT validation MCP server...")

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            from mcp.server.models import InitializationOptions, ServerCapabilities
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pyipxact-de-mcp",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools={}
                    )
                )
            )

    asyncio.run(run_server())
