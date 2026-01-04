# Deep Research UI Plugin

A TypeScript/Bun plugin for OpenCode that provides deep research UI tools.

## Installation

```bash
npm install
```

## Building

```bash
npm run build
npm run typecheck
```

## Tools

### `deep_research_ui`

Start a deep research run with basic parameters.

**Parameters:**
- `query` (string, required): The research query/question to investigate
- `effort` (number, 1-5, default: 3): Research effort level (higher is more thorough)
- `clarifying_questions` (string[], optional): Optional clarifying questions to resolve first
- `plan_approval` (boolean, default: true): Whether to require user approval before execution

**Returns:**
JSON object with run ID and initialization status.

### `deep_research_ui.start_run`

Start a deep research run with structured parameters.

**Parameters:**
- `query` (string, required): The research query/question to investigate
- `effort` (number, 1-5, default: 3): Research effort level (higher is more thorough)
- `clarifying_questions` (string[], optional): Optional clarifying questions to resolve first
- `plan_approval` (boolean, default: true): Whether to require user approval before execution
- `timeout_minutes` (number, 1-60, default: 30): Timeout in minutes for the research run

**Returns:**
JSON object with run ID, status, and initialization details.

## Usage

The plugin is designed to be used with the OpenCode plugin system. Export the `DeepResearchUIPlugin` function and register it with your OpenCode instance.

## States

A research run can be in the following states:
- `initialized`: Run created, awaiting clarification or approval
- `awaiting_clarification`: Run waiting for user to answer clarifying questions
- `awaiting_approval`: Run waiting for user to approve the execution plan
- `ready_to_execute`: Run ready to be executed
- `started`: Run has been initiated