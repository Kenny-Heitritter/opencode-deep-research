import { tool } from "@opencode-ai/plugin";
import { randomUUID } from "node:crypto";

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
          const runId = randomUUID();
          return `[DEEP RESEARCH] Starting research run on: "${args.query}" (effort=${args.effort})\n\nResearch run initiated with ID: ${runId}\nStatus: The research plan is being processed and will execute according to the specified effort level.`;
        },
      }),
    },
  };
};

export default deep_research_ui;