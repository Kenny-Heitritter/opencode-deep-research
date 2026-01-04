"""OpenCode Deep Research MCP Server.

An async MCP server that integrates with the OpenCode server HTTP API
for deep research execution.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

OPENCODE_SERVER_URL = os.getenv("OPENCODE_SERVER_URL", "http://localhost:3535")
SESSION_ID = os.getenv("SESSION_ID", "")

app = Server("opencode-deep-research-mcp")


async def call_opencode_shell(
    session_id: str,
    agent: str,
    command: str,
    provider_id: str = "openai",
    model_id: str = "gpt-4o",
    directory: str = ".",
) -> dict[str, Any]:
    """Call the OpenCode server shell endpoint."""
    async with httpx.AsyncClient() as client:
        url = f"{OPENCODE_SERVER_URL}/session/{session_id}/shell"
        if directory:
            url += f"?directory={directory}"

        response = await client.post(
            url,
            json={
                "agent": agent,
                "model": {
                    "providerID": provider_id,
                    "modelID": model_id,
                },
                "command": command,
            },
        )
        response.raise_for_status()
        return response.json()


async def call_opencode_message(
    session_id: str,
    message_id: str,
    directory: str = ".",
) -> dict[str, Any]:
    """Call the OpenCode server message endpoint."""
    async with httpx.AsyncClient() as client:
        url = f"{OPENCODE_SERVER_URL}/session/{session_id}/message/{message_id}"
        if directory:
            url += f"?directory={directory}"

        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="start_deep_research",
            description="Start a deep research job by posting to the OpenCode shell endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The research query to execute",
                    },
                    "effort": {
                        "type": "integer",
                        "description": "Effort level (1-5), higher means more thorough research",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 3,
                    },
                    "session_id": {
                        "type": "string",
                        "description": "OpenCode session ID (defaults to SESSION_ID env var)",
                    },
                    "provider_id": {
                        "type": "string",
                        "description": "LLM provider ID (default: openai)",
                        "default": "openai",
                    },
                    "model_id": {
                        "type": "string",
                        "description": "LLM model ID (default: gpt-4o)",
                        "default": "gpt-4o",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Working directory (default: .)",
                        "default": ".",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_message",
            description="Get a message from the OpenCode session",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "Message ID to retrieve",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "OpenCode session ID (defaults to SESSION_ID env var)",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Working directory (default: .)",
                        "default": ".",
                    },
                },
                "required": ["message_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    if name == "start_deep_research":
        session_id = arguments.get("session_id", SESSION_ID)
        if not session_id:
            raise ValueError(
                "session_id must be provided either as argument or SESSION_ID env var"
            )

        query = arguments["query"]
        effort = arguments.get("effort", 3)
        provider_id = arguments.get("provider_id", "openai")
        model_id = arguments.get("model_id", "gpt-4o")
        directory = arguments.get("directory", ".")

        command = f'/deep-research "{query}" --effort {effort}'

        result = await call_opencode_shell(
            session_id=session_id,
            agent="deep-research-intake",
            command=command,
            provider_id=provider_id,
            model_id=model_id,
            directory=directory,
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    elif name == "get_message":
        session_id = arguments.get("session_id", SESSION_ID)
        if not session_id:
            raise ValueError(
                "session_id must be provided either as argument or SESSION_ID env var"
            )

        message_id = arguments["message_id"]
        directory = arguments.get("directory", ".")

        result = await call_opencode_message(
            session_id=session_id,
            message_id=message_id,
            directory=directory,
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="opencode-deep-research-mcp",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
