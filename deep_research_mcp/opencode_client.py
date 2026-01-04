"""OpenCode client for interacting with OpenCode server API."""

import httpx
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class OpenCodeMessage(BaseModel):
    """Message to send to OpenCode server."""

    session_id: str = Field(description="Session ID for the message")
    message: str = Field(description="Message content")


class OpenCodeResponse(BaseModel):
    """Response from OpenCode server."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class OpenCodeClient:
    """Client for interacting with OpenCode server HTTP API."""

    def __init__(self, base_url: str = "http://localhost:4242", timeout: float = 30.0):
        """Initialize OpenCode client.

        Args:
            base_url: Base URL of the OpenCode server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Enter context manager."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._client:
            await self._client.aclose()

    async def send_session_message(
        self, session_id: str, message: str
    ) -> OpenCodeResponse:
        """Send message to OpenCode server /session/:id/message endpoint.

        Args:
            session_id: Session ID
            message: Message to send

        Returns:
            OpenCodeResponse with server response or error
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        url = f"{self.base_url}/session/{session_id}/message"

        try:
            response = await self._client.post(
                url,
                json={"message": message},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            return OpenCodeResponse(success=True, data=response.json())
        except httpx.HTTPStatusError as e:
            return OpenCodeResponse(
                success=False, error=f"HTTP error {e.response.status_code}: {str(e)}"
            )
        except httpx.RequestError as e:
            return OpenCodeResponse(success=False, error=f"Request error: {str(e)}")
        except Exception as e:
            return OpenCodeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def get_session_status(self, session_id: str) -> OpenCodeResponse:
        """Get session status from OpenCode server.

        Args:
            session_id: Session ID

        Returns:
            OpenCodeResponse with session status or error
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        url = f"{self.base_url}/session/{session_id}"

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            return OpenCodeResponse(success=True, data=response.json())
        except httpx.HTTPStatusError as e:
            return OpenCodeResponse(
                success=False, error=f"HTTP error {e.response.status_code}: {str(e)}"
            )
        except httpx.RequestError as e:
            return OpenCodeResponse(success=False, error=f"Request error: {str(e)}")
        except Exception as e:
            return OpenCodeResponse(success=False, error=f"Unexpected error: {str(e)}")
