# OpenCode Deep Research MCP Server

Python async MCP (Model Context Protocol) server for OpenCode Deep Research workflow.

## Purpose

This MCP server provides job execution capabilities for the Deep Research workflow by:
- Exposing MCP tools for research job execution
- Communicating with OpenCode server via HTTP API
- Serving as the async job runner for research tasks

## Installation

```bash
pip install -e .
```

Or with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Running the Server

```bash
python -m deep_research_mcp
```

### Configuration

Set `OPENCODE_BASE_URL` environment variable to point to your OpenCode server:

```bash
export OPENCODE_BASE_URL="http://localhost:4242"
python -m deep_research_mcp
```

## MCP Tools

### `execute_research_job`

Execute a research job by sending a task to the OpenCode server.

**Parameters:**
- `session_id` (string): OpenCode session ID
- `task` (string): Research task description

**Returns:** Response from OpenCode server with job execution result

### `get_session_info`

Get information about an OpenCode session.

**Parameters:**
- `session_id` (string): OpenCode session ID

**Returns:** Session information from OpenCode server

### `health_check`

Check if the MCP server is healthy.

**Returns:** Health status message

## Architecture

```
deep_research_mcp/
├── __init__.py       # Package initialization
├── __main__.py       # CLI entry point
├── server.py         # MCP server creation and configuration
├── opencode_client.py # HTTP client for OpenCode server
└── tools.py          # MCP tool implementations
```

## Development

### Running Tests

```bash
pytest
```

### Running with LSP/SSE Transport

The server can be configured to run with different transports:

```python
from deep_research_mcp.server import create_server

mcp = create_server(opencode_base_url="http://localhost:4242")

# Use stdio transport (default)
async with stdio_server() as (read_stream, write_stream):
    await mcp.run(read_stream, write_stream)

# Or use SSE transport
from mcp.server.sse import SseServerTransport
transport = SseServerTransport("/messages")
```

## API Integration

The server integrates with OpenCode server via HTTP:

- **POST** `/session/:id/message` - Send message to session
- **GET** `/session/:id` - Get session status

## License

See LICENSE file in repository root.