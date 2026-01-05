import { DeepResearchUIPlugin } from "../../src/deep-research-ui";
import { ToolContext } from "@opencode-ai/plugin";

function createMockContext(sessionID: string = "test-session"): ToolContext {
  return {
    sessionID,
    messageID: "test-message",
    agent: "test-agent",
    abort: new AbortController().signal,
  };
}

async function testPluginRegistration() {
  console.log("Testing plugin registration...");

  const mockPluginInput = {
    client: {} as any,
    project: {} as any,
    directory: "/test/dir",
    worktree: "/test/worktree",
    serverUrl: new URL("http://localhost:4242"),
    $: {} as any,
  };

  const hooks = await DeepResearchUIPlugin(mockPluginInput);

  if (!hooks.tool || !hooks.tool["deep_research_ui"]) {
    throw new Error("Plugin failed to register deep_research_ui tool");
  }

  console.log("✓ Plugin successfully registered deep_research_ui tool");
  console.log("✓ Tool description:", hooks.tool["deep_research_ui"].description);
}

async function testToolExecution() {
  console.log("\nTesting tool execution...");

  const mockPluginInput = {
    client: {} as any,
    project: {} as any,
    directory: "/test/dir",
    worktree: "/test/worktree",
    serverUrl: new URL("http://localhost:4242"),
    $: {} as any,
  };

  const hooks = await DeepResearchUIPlugin(mockPluginInput);
  const tool = hooks.tool!["deep_research_ui"];

  const mockContext = createMockContext("test-session-123");

  const result = await tool.execute(
    {
      plan: "Research the impact of AI on software development",
      effort: 3,
    },
    mockContext
  );

  const parsed = JSON.parse(result);

  if (!parsed.run_id || typeof parsed.run_id !== "string") {
    throw new Error("Tool did not return a valid run_id");
  }

  if (parsed.plan !== "Research the impact of AI on software development") {
    throw new Error("Tool did not return the correct plan");
  }

  if (parsed.effort !== 3) {
    throw new Error("Tool did not return the correct effort level");
  }

  if (parsed.status !== "initialized") {
    throw new Error("Tool did not return the correct status");
  }

  console.log("✓ Tool execute returned valid run_id:", parsed.run_id);
  console.log("✓ Tool correctly returned plan:", parsed.plan);
  console.log("✓ Tool correctly returned effort level:", parsed.effort);
  console.log("✓ Tool correctly returned status:", parsed.status);
}

async function testToolValidation() {
  console.log("\nTesting tool argument validation...");

  const mockPluginInput = {
    client: {} as any,
    project: {} as any,
    directory: "/test/dir",
    worktree: "/test/worktree",
    serverUrl: new URL("http://localhost:4242"),
    $: {} as any,
  };

  const hooks = await DeepResearchUIPlugin(mockPluginInput);
  const tool = hooks.tool!["deep_research_ui"];

  const argsDefinition = tool.args;

  if (!argsDefinition.plan) {
    throw new Error("Tool is missing 'plan' argument definition");
  }

  if (!argsDefinition.effort) {
    throw new Error("Tool is missing 'effort' argument definition");
  }

  console.log("✓ Tool has 'plan' argument definition");
  console.log("✓ Tool has 'effort' argument definition");
}

async function runTests() {
  console.log("Running Deep Research UI Plugin Integration Tests\n");
  console.log("=".repeat(50));

  try {
    await testPluginRegistration();
    await testToolValidation();
    await testToolExecution();

    console.log("\n" + "=".repeat(50));
    console.log("✓ All integration tests passed!");
  } catch (error) {
    console.error("\n✗ Test failed:", error);
    process.exit(1);
  }
}

runTests();