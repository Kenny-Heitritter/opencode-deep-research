# Gates for opencode-deep-research Plugin

This document defines the gates that must pass before merging changes to the integration branch.

## Pre-requisites

Before running any gates, ensure dependencies are installed:

```bash
npm install
```

## Gates

### Build Gate

Verify that the TypeScript code compiles successfully:

```bash
npm run build
```

**Expected behavior:** Clean build with no TypeScript errors or warnings.

**What it checks:**
- All TypeScript files compile to JavaScript
- Type definitions are generated
- No syntax or type errors

### Integration Tests Gate

Verify that the plugin works correctly in a mocked environment:

```bash
npm run test:integration
```

**Expected behavior:** All tests pass with output showing:
- ✓ Plugin registration successful
- ✓ Tool definitions present and correct
- ✓ Tool execution returns valid results

**What it checks:**
- Plugin loads and registers the `deep_research_ui` tool
- Tool accepts `plan` and `effort` arguments with correct types
- Tool execution returns structured JSON with `run_id`, `plan`, `effort`, and `status`

## Gate Execution Order

Run gates in this order:
1. `npm install` (if not already done)
2. `npm run build`
3. `npm run test:integration`

All gates must pass before marking a task complete.

## Troubleshooting

### Build fails with "Cannot find module '@opencode-ai/plugin'"
Run `npm install` to install dependencies.

### Build fails with "File '@tsconfig/node22/tsconfig.json' not found"
Run `npm install` to install devDependencies.

### Integration tests fail with "ECONNREFUSED"
This is expected behavior - the test attempts to post to a mock server which doesn't exist. The test handles this error gracefully and continues. The actual assertions should still pass.