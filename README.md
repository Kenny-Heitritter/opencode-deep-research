# OpenCode Deep Research

Implementation of a prompt-gated, agent-initiated Deep Research workflow in OpenCode that produces Gemini/ChatGPT-class research reports with citations.

## Quick Start

See [SPEC.md](SPEC.md) for the full specification and architecture overview.

## Project Structure

- `.opencode/`: OpenCode plugin and agent configurations
  - `plugin/`: TS/Bun plugins (e.g., deep_research_ui)
  - `command/`: Command templates
- `src/`: Python MCP server implementation
- `tests/`: Unit and integration tests

## Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- Bun (for TypeScript plugins)

### Setup

Install Python dependencies:
```bash
pip install -e .
```

Install Node dependencies:
```bash
cd .opencode
bun install
```

### Running Tests

Python tests:
```bash
pytest
```

## MCP Server

The MCP server is located in `src/opencode_deep_research_mcp/server.py`. See [README_SERVER.md](README_SERVER.md) for detailed usage information.