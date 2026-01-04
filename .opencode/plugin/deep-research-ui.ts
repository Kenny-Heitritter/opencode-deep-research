import type { Plugin } from "@opencode-ai/plugin";
import { tool, type ToolContext } from "@opencode-ai/plugin";
import crypto from "node:crypto";

export const deep_research_ui: Plugin = async () => {
  return {
    tool: {
      "deep_research_ui.start_run": tool({
        description: "Start a deep research run with structured parameters",
        args: {
          query: tool.schema
            .string()
            .describe("The research query/question to investigate"),
          effort: tool.schema
            .number()
            .min(1)
            .max(5)
            .default(3)
            .describe("Research effort level (1-5, higher is more thorough)"),
          clarifying_questions: tool.schema
            .array(tool.schema.string())
            .optional()
            .describe("Optional clarifying questions to resolve first"),
          plan_approval: tool.schema
            .boolean()
            .default(true)
            .describe("Whether to require user approval before execution"),
          timeout_minutes: tool.schema
            .number()
            .min(1)
            .max(60)
            .default(30)
            .describe("Timeout in minutes for the research run"),
        },
        async execute(args: any, context: ToolContext) {
          const runId = crypto.randomUUID();
          const now = new Date().toISOString();
          
          let message: string;
          let status: string;
          
          if (args.clarifying_questions && args.clarifying_questions.length > 0) {
            status = "awaiting_clarification";
            message = 
              `Research run ${runId} created. Please resolve ${args.clarifying_questions.length} clarifying questions before proceeding.`;
          } else if (args.plan_approval) {
            status = "awaiting_approval";
            message = 
              `Research run ${runId} initialized at ${now}. Plan approval required before execution.`;
          } else {
            status = "ready_to_execute";
            message = 
              `Research run ${runId} ready to execute at ${now} with effort level ${args.effort}.`;
          }
          
          const researchState = {
            run_id: runId,
            status: status,
            message: message,
            query: args.query,
            effort: args.effort,
            clarifying_questions: args.clarifying_questions || [],
            plan_approval: args.plan_approval,
            timeout_minutes: args.timeout_minutes,
            created_at: now,
            session_id: context.sessionID,
            message_id: context.messageID,
          };

          return JSON.stringify(researchState, null, 2);
        },
      }),
    },
  };
};

export default deep_research_ui;