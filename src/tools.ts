import { tool, ToolContext } from "@opencode-ai/plugin";

export type RunId = string;

export interface StartRunOptions {
  serverUrl: URL;
}

export interface StartRunArgs {
  plan: string;
  effort: number;
}

export interface StartRunResult {
  run_id: RunId;
  plan: string;
  effort: number;
  status: "initialized";
}

class OpenCodeApiClient {
  private serverUrl: URL;

  constructor(serverUrl: string | URL) {
    this.serverUrl = typeof serverUrl === "string" ? new URL(serverUrl) : serverUrl;
  }

  async postToSession(sessionID: string, message: string): Promise<void> {
    const url = `${this.serverUrl.origin}/session/${sessionID}/message`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`Failed to post to session: ${response.status} ${response.statusText}`);
    }
  }
}

export const createDeepResearchTool = (options: StartRunOptions) => {
  const client = new OpenCodeApiClient(options.serverUrl);

  return tool({
    description: "Deep Research UI tool for planning and executing research tasks. Use this tool to start a deep research run with a plan and effort level.",
    args: {
      plan: tool.schema
        .string()
        .describe("The research plan or question to investigate"),
      effort: tool.schema
        .number()
        .min(1)
        .max(5)
        .default(3)
        .describe("Research effort level (1-5), higher means more thorough"),
    },
    async execute(args: StartRunArgs, context: ToolContext): Promise<string> {
      const runId = crypto.randomUUID() as RunId;
      const result: StartRunResult = {
        run_id: runId,
        plan: args.plan,
        effort: args.effort,
        status: "initialized",
      };

      const output = JSON.stringify(result, null, 2);

      try {
        await client.postToSession(context.sessionID, `Deep Research Run Started\n\n${output}`);
      } catch (error) {
        console.error("Failed to post to session:", error);
      }

      return output;
    },
  });
};