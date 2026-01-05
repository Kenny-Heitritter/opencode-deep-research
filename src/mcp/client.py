#!/usr/bin/env python3
"""
HTTP Client for OpenCode Server Communication

This client handles communication from the MCP server back to the OpenCode server
via the /session/:id/message endpoint.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

try:
    import aiohttp
except ImportError:
    # Fallback to synchronous requests if aiohttp is not available
    import requests

    aiohttp = None


class OpenCodeClient:
    """HTTP client for communicating with the OpenCode server"""

    def __init__(self, session_id: str, base_url: Optional[str] = None):
        """
        Initialize the OpenCode client.

        Args:
            session_id: The OpenCode session ID
            base_url: Base URL of the OpenCode server (defaults to env var or localhost)
        """
        self.session_id = session_id
        self.base_url = base_url or os.getenv(
            "OPENCODE_SERVER_URL", "http://localhost:3000"
        )
        self.logger = logging.getLogger(f"opencode-client-{session_id}")
        self.use_async = aiohttp is not None

        if not self.use_async:
            self.logger.warning(
                "aiohttp not available, falling back to synchronous requests"
            )

    async def send_message(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the OpenCode server session.

        Args:
            message: The message content to send
            metadata: Optional metadata to include with the message

        Returns:
            Response from the server

        Raises:
            Exception: If the request fails
        """
        if self.use_async:
            return await self._send_message_async(message, metadata)
        else:
            return self._send_message_sync(message, metadata)

    async def _send_message_async(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message using async aiohttp"""
        url = urljoin(self.base_url, f"/session/{self.session_id}/message")

        payload = {
            "message": message,
            "source": "mcp-server",
            "timestamp": asyncio.get_event_loop().time(),
        }

        if metadata:
            payload["metadata"] = metadata

        self.logger.debug(f"Sending message to {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    self.logger.debug(f"Message sent successfully: {result}")
                    return result
        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to send message: {e}")
            raise Exception(f"Failed to communicate with OpenCode server: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {e}")
            raise

    def _send_message_sync(
        self, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message using synchronous requests"""
        url = urljoin(self.base_url, f"/session/{self.session_id}/message")

        payload = {
            "message": message,
            "source": "mcp-server",
            "timestamp": asyncio.get_event_loop().time()
            if hasattr(asyncio, "get_event_loop")
            else 0,
        }

        if metadata:
            payload["metadata"] = metadata

        self.logger.debug(f"Sending message to {url}")

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            self.logger.debug(f"Message sent successfully: {result}")
            return result
        except requests.RequestException as e:
            self.logger.error(f"Failed to send message: {e}")
            raise Exception(f"Failed to communicate with OpenCode server: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {e}")
            raise

    async def send_status(
        self, status: str, details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a status update to the OpenCode server.

        Args:
            status: Status message
            details: Optional additional details

        Returns:
            Response from the server
        """
        metadata = {"type": "status", "details": details or {}}
        return await self.send_message(status, metadata)

    async def send_error(
        self, error: str, details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an error message to the OpenCode server.

        Args:
            error: Error message
            details: Optional error details

        Returns:
            Response from the server
        """
        metadata = {"type": "error", "details": details or {}}
        return await self.send_message(f"ERROR: {error}", metadata)


async def test_client():
    """Test the client connectivity"""
    client = OpenCodeClient("test-session-123")

    try:
        result = await client.send_message("Test message from MCP client")
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run basic connectivity test
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_client())
