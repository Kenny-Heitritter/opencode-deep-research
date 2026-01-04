"""MCP tools for Deep Research server."""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from deep_research_mcp.opencode_client import OpenCodeClient

logger = logging.getLogger(__name__)


async def register_tools(mcp: FastMCP, opencode_client: OpenCodeClient) -> None:
    """Register MCP tools for Deep Research.

    Args:
        mcp: FastMCP server instance
        opencode_client: OpenCode client instance
    """

    @mcp.tool()
    async def execute_research_job(
        session_id: str,
        task: str,
    ) -> list[TextContent]:
        """Execute a research job by sending task to OpenCode server.

        Args:
            session_id: OpenCode session ID for the job
            task: Research task description or prompt

        Returns:
            Response from OpenCode server with job execution result
        """
        logger.info(f"Executing research job for session {session_id}: {task[:100]}...")

        response = await opencode_client.send_session_message(
            session_id=session_id, message=task
        )

        if response.success:
            result = f"Job executed successfully. Response: {response.data}"
            logger.info(f"Research job completed for session {session_id}")
        else:
            result = f"Job execution failed: {response.error}"
            logger.error(
                f"Research job failed for session {session_id}: {response.error}"
            )

        return [TextContent(type="text", text=result)]

    @mcp.tool()
    async def get_session_info(session_id: str) -> list[TextContent]:
        """Get information about an OpenCode session.

        Args:
            session_id: OpenCode session ID

        Returns:
            Session information from OpenCode server
        """
        logger.info(f"Fetching session info for {session_id}")

        response = await opencode_client.get_session_status(session_id=session_id)

        if response.success:
            result = f"Session info: {response.data}"
            logger.info(f"Retrieved session info for {session_id}")
        else:
            result = f"Failed to get session info: {response.error}"
            logger.error(
                f"Failed to get session info for {session_id}: {response.error}"
            )

        return [TextContent(type="text", text=result)]

    @mcp.tool()
    async def health_check() -> list[TextContent]:
        """Check if the MCP server is healthy.

        Returns:
            Health status message
        """
        logger.debug("Health check called")
        return [TextContent(type="text", text="Deep Research MCP server is healthy")]
