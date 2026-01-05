# Deep Research MCP Server

This directory contains the MCP (Model Context Protocol) server implementation for the Deep Research feature.

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Components

### server.py

The main MCP server that handles research runs. It:
- Receives research queries with effort levels
- Processes the research in phases
- Communicates status and results back to OpenCode via HTTP

### client.py

HTTP client for communicating with the OpenCode server. It:
- Sends messages to the `/session/:id/message` endpoint
- Supports both async (aiohttp) and sync (requests) modes
- Handles status updates and error reporting

## Usage

The server is spawned automatically by the deep-research-ui plugin when a research run is initiated:

```bash
python3 server.py \
  --run-id <run_id> \
  --query "Your research query" \
  --effort 2 \
  --session-id <opencode_session_id>
```

## Environment Variables

- `OPENCODE_SERVER_URL`: Base URL of the OpenCode server (default: `http://localhost:3000`)

## Testing

Test the client connectivity:

```bash
python3 client.py
```

Test the full server flow:

```bash
python3 server.py \
  --run-id test_run_123 \
  --query "Test query" \
  --effort 2 \
  --session-id test_session \
  --debug
```
