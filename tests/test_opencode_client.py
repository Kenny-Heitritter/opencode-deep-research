"""Tests for OpenCode client."""

import pytest
import pytest_asyncio

from deep_research_mcp.opencode_client import (
    OpenCodeClient,
    OpenCodeMessage,
    OpenCodeResponse,
)


@pytest_asyncio.fixture
async def client():
    """Create a test client."""
    async with OpenCodeClient(base_url="http://test.local:4242") as c:
        yield c


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    async with OpenCodeClient() as client:
        assert client.base_url == "http://localhost:4242"
        assert client.timeout == 30.0


@pytest.mark.asyncio
async def test_send_session_message():
    """Test sending session message."""
    async with OpenCodeClient() as client:
        response = await client.send_session_message("test-session", "test message")

        assert isinstance(response, OpenCodeResponse)
        assert isinstance(response.success, bool)


@pytest.mark.asyncio
async def opencode_message_validation():
    """Test OpenCodeMessage validation."""
    msg = OpenCodeMessage(session_id="test-session", message="test")
    assert msg.session_id == "test-session"
    assert msg.message == "test"
