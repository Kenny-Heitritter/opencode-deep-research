# OpenCode Deep Research Plugin

OpenCode plugin for Deep Research UI tool.

## Installation

This plugin is published as `@opencode-deep-research/plugin`.

## Usage

The plugin provides the `deep_research_ui` tool for planning and executing research tasks.

### Tool: deep_research_ui

**Description:** Deep Research UI tool for planning and executing research tasks. Use this tool to start a deep research run with a plan and effort level.

**Arguments:**
- `plan` (string, required): The research plan or question to investigate
- `effort` (number, optional, default: 3): Research effort level (1-5), higher means more thorough

**Returns:**
```json
{
  "run_id": "uuid-string",
  "plan": "the research plan",
  "effort": 3,
  "status": "initialized"
}
```

### Example

```typescript
import { DeepResearchUIPlugin } from "@opencode-deep-research/plugin";

const plugin = DeepResearchUIPlugin;
```

## Development

### Building

```bash
npm run build
```

### Running Integration Tests

```bash
npm run test:integration
```

## Implementation Details

The plugin registers a tool that:
1. Accepts a research plan and effort level
2. Generates a unique run ID
3. Posts formatted output to the OpenCode session via HTTP API
4. Returns a structured result with run ID and status

The tool uses the OpenCode server's `/session/:id/message` endpoint to post formatted research output.

## License

See LICENSE file in repository root.