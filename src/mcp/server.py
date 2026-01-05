"""Async MCP server with search, fetch, extract tools."""

import logging
import os
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

from src.mcp.tools import WebTools
from src.models import Document, Note, SearchResult

logger = logging.getLogger(__name__)


class SearchArgs(BaseModel):
    """Arguments for search tool."""

    query: str
    num_results: int = 10


class FetchArgs(BaseModel):
    """Arguments for fetch tool."""

    url: str


class ExtractArgs(BaseModel):
    """Arguments for extract tool."""

    url: str
    query: str


def create_server() -> Server:
    """Create and configure the Deep Research MCP server.

    Returns:
        Configured MCP server instance
    """
    app = Server("deep-research")

    web_tools = WebTools()

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="search",
                description="Search the web for information using DuckDuckGo",
                inputSchema=SearchArgs.model_json_schema(),
            ),
            Tool(
                name="fetch",
                description="Fetch and parse content from a URL",
                inputSchema=FetchArgs.model_json_schema(),
            ),
            Tool(
                name="extract",
                description="Extract relevant information from a URL using Jina AI reader",
                inputSchema=ExtractArgs.model_json_schema(),
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool response
        """
        try:
            async with web_tools:
                if name == "search":
                    return await _handle_search(arguments)
                elif name == "fetch":
                    return await _handle_fetch(arguments)
                elif name == "extract":
                    return await _handle_extract(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_search(arguments: dict[str, Any]) -> list[TextContent]:
        """Handle search tool call.

        Args:
            arguments: Search arguments

        Returns:
            Search results as text content
        """
        args = SearchArgs(**arguments)
        results = await web_tools.search(args.query, args.num_results)

        output = f"# Search Results: {args.query}\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. **{result.title}**\n"
            output += f"   URL: {result.url}\n"
            output += f"   {result.snippet}\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_fetch(arguments: dict[str, Any]) -> list[TextContent]:
        """Handle fetch tool call.

        Args:
            arguments: Fetch arguments

        Returns:
            Document content as text
        """
        args = FetchArgs(**arguments)
        doc = await web_tools.fetch(args.url)

        output = f"# Document: {doc.title}\n\n"
        output += f"**URL:** {doc.url}\n\n"
        output += f"**Content:**\n\n{doc.content}"

        return [TextContent(type="text", text=output)]

    async def _handle_extract(arguments: dict[str, Any]) -> list[TextContent]:
        """Handle extract tool call.

        Args:
            arguments: Extract arguments

        Returns:
            Extracted notes as text
        """
        args = ExtractArgs(**arguments)
        notes = await web_tools.extract_with_jina(args.url, args.query)

        if not notes:
            return [TextContent(type="text", text="No content extracted")]

        output = f"# Extracted Information from {args.url}\n\n"
        output += f"**Query:** {args.query}\n\n"

        for i, note in enumerate(notes, 1):
            output += f"{i}. {note.content}\n\n"

        return [TextContent(type="text", text=output)]

    logger.info("Deep Research MCP server created")
    return app


async def main():
    """Main entry point for running the MCP server."""
    import mcp.server.stdio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Deep Research MCP server")

    app = create_server()

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
