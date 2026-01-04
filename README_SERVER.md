# OpenCode Deep Research MCP Server

An async MCP server that integrates with the OpenCode server HTTP API for deep research execution.

## Installation

```bash
pip install -e .
```

## Usage

The MCP server connects to an OpenCode server instance and provides tools for:

- **start_deep_research**: Start a deep research job via the `/session/{id}/shell` endpoint
- **get_message**: Get a message from a session via the `/session/{id}/message/{messageID}` endpoint

### Configuration

Set the following environment variables:

- `OPENCODE_SERVER_URL`: URL of the OpenCode server (default: `http://localhost:3535`)
- `SESSION_ID`: Default session ID to use for operations

### Running the Server

As a stdio MCP server:

```bash
opencode-deep-research-mcp
```

### Tools

#### start_deep_research

Start a deep research job by posting to the OpenCode shell endpoint.

Parameters:
- `query` (required): The research query to execute
- `effort` (optional): Effort level 1-5, higher means more thorough research (default: 3)
- `session_id` (optional): OpenCode session ID (defaults to SESSION_ID env var)
- `provider_id` (optional): LLM provider ID (default: openai)
- `model_id` (optional): LLM model ID (default: gpt-4o)
- `directory` (optional): Working directory (default: .)

Example:
```python
{
  "query": "What is the state of AI research in 2025?",
  "effort": 3,
  "session_id": "session-123"
}
```

#### get_message

Get a message from the OpenCode session.

Parameters:
- `message_id` (required): Message ID to retrieve
- `session_id` (optional): OpenCode session ID (defaults to SESSION_ID env var)
- `directory` (optional): Working directory (default: .)

Example:
```python
{
  "message_id": "msg-456",
  "session_id": "session-123"
}
```

## Development

### Running Tests

```bash
pytest
```

## Architecture

The MCP server:

1. Implements the MCP protocol via stdio
2. Provides async tools that call OpenCode server HTTP endpoints
3. Uses `httpx` for async HTTP client functionality
4. Integrates with the OpenCode `/session/{id}/shell` endpoint for command execution
5. Integrates with the OpenCode `/session/{id}/message/{messageID}` endpoint for message retrieval