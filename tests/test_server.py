"""Tests for opencode_deep_research_mcp."""

import pytest
from unittest.mock import AsyncMock, patch, Mock

from opencode_deep_research_mcp.server import (
    call_opencode_shell,
    call_opencode_message,
    app,
)


@pytest.mark.asyncio
async def test_call_opencode_shell():
    """Test calling the OpenCode shell endpoint."""
    mock_response = {
        "id": "msg-123",
        "sessionID": "session-456",
        "role": "assistant",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response_obj = Mock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response_obj

        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await call_opencode_shell(
            session_id="session-456",
            agent="test-agent",
            command="test command",
        )

        assert result == mock_response
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/session/session-456/shell" in call_args[0][0]


@pytest.mark.asyncio
async def test_call_opencode_message():
    """Test calling the OpenCode message endpoint."""
    mock_response = {
        "info": {
            "id": "msg-123",
            "sessionID": "session-456",
            "role": "user",
        },
        "parts": [],
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response_obj = Mock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response_obj

        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await call_opencode_message(
            session_id="session-456",
            message_id="msg-123",
        )

        assert result == mock_response
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/session/session-456/message/msg-123" in call_args[0][0]
