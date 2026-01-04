import { tool } from "@opencode-ai/plugin";

const deep_research_ui = async () => {
  return {
    tool: {
      start_run: tool({
        description: "Start a deep research run on the specified query",
        args: {
          query: tool.schema.string().describe("The research query to investigate"),
          effort: tool.schema.number().optional().default(3).describe("Research effort level (1-5), higher means more comprehensive"),
        },
        async execute(args, context) {
          return `[DEEP RESEARCH] Starting research run on: "${args.query}" (effort=${args.effort})\n\nNote: Deep Research execution is not yet implemented. This is a placeholder for the future integration with the MCP research server.`;
        },
      }),
    },
  };
};

export default deep_research_ui;