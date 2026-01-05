"""Main MCP server for OpenCode Deep Research."""

import asyncio
import logging
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server

from deep_research_mcp.opencode_client import OpenCodeClient
from deep_research_mcp.tools import register_tools

logger = logging.getLogger(__name__)


def create_server(opencode_base_url: str | None = None) -> FastMCP:
    """Create and configure the Deep Research MCP server.

    Args:
        opencode_base_url: Base URL for OpenCode server (defaults to env var or localhost)

    Returns:
        Configured FastMCP server instance
    """
    base_url = opencode_base_url or os.getenv(
        "OPENCODE_BASE_URL", "http://localhost:4242"
    )

    mcp = FastMCP(
        name="deep-research",
        description="OpenCode Deep Research MCP server",
        version="0.1.0",
    )

    opencode_client = OpenCodeClient(base_url=base_url)

    asyncio.create_task(register_tools(mcp, opencode_client))

    logger.info(f"Deep Research MCP server created with OpenCode base URL: {base_url}")

    return mcp


async def main() -> None:
    """Main entry point for running the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Deep Research MCP server")

    mcp = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
