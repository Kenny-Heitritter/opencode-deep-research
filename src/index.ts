import { Plugin, tool } from "@opencode-ai/plugin";

const deepResearchTool = tool({
  description: "Deep Research UI for planning and executing research tasks",
  args: {
    query: tool.schema
      .string()
      .describe("The research query or question to investigate"),
    effort: tool.schema
      .number()
      .min(1)
      .max(5)
      .default(3)
      .describe("Research effort level (1-5), higher means more thorough"),
  },
  async execute(args, context) {
    const runId = crypto.randomUUID();

    return JSON.stringify({
      status: "initialized",
      run_id: runId,
      query: args.query,
      effort: args.effort,
      message: "Research run initialized. In future iterations, this will launch the full Deep Research workflow via the MCP server.",
    });
  },
});

export const DeepResearchPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      "deep-research-ui": deepResearchTool,
    },
  };
};

export default DeepResearchPlugin;