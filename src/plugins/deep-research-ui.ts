import { type Plugin, tool } from "@opencode-ai/plugin";
import { spawn, type ChildProcess } from "child_process";
import { join } from "path";

interface RunState {
  runId: string;
  process: ChildProcess | null;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
}

const activeRuns = new Map<string, RunState>();

export const DeepResearchUIPlugin: Plugin = async (ctx) => {
  await ctx.client.app.log({
    service: "deep-research-ui",
    level: "info",
    message: "Deep Research UI plugin initialized",
  });

  return {
    tool: {
      deep_research_ui: tool({
        description: "Start a deep research run with the specified query and effort level",
        args: {
          query: tool.schema.string().describe("The research query to investigate"),
          effort: tool.schema
            .number()
            .min(1)
            .max(3)
            .default(2)
            .describe("Research effort level: 1=basic, 2=standard, 3=comprehensive"),
        },
        async execute(args, toolCtx) {
          const runId = `run_${Date.now()}_${Math.random().toString(36).substring(7)}`;
          
          await ctx.client.app.log({
            service: "deep-research-ui",
            level: "info",
            message: `Starting research run ${runId}`,
            extra: { query: args.query, effort: args.effort },
          });

          // Initialize run state
          const runState: RunState = {
            runId,
            process: null,
            status: "pending",
          };
          activeRuns.set(runId, runState);

          try {
            // Get the path to the MCP server
            const mcpServerPath = join(ctx.directory, "src", "mcp", "server.py");
            
            // Spawn the MCP server process
            const mcpProcess = spawn("python3", [
              mcpServerPath,
              "--run-id", runId,
              "--query", args.query,
              "--effort", args.effort.toString(),
              "--session-id", toolCtx.sessionId || "unknown",
            ], {
              cwd: ctx.directory,
              stdio: ["ignore", "pipe", "pipe"],
            });

            runState.process = mcpProcess;
            runState.status = "running";

            // Handle stdout
            mcpProcess.stdout?.on("data", async (data) => {
              const message = data.toString().trim();
              await ctx.client.app.log({
                service: "deep-research-ui",
                level: "info",
                message: `[${runId}] ${message}`,
              });
            });

            // Handle stderr
            mcpProcess.stderr?.on("data", async (data) => {
              const message = data.toString().trim();
              await ctx.client.app.log({
                service: "deep-research-ui",
                level: "warn",
                message: `[${runId}] ${message}`,
              });
            });

            // Handle process exit
            mcpProcess.on("close", async (code) => {
              const currentState = activeRuns.get(runId);
              if (currentState) {
                currentState.status = code === 0 ? "completed" : "failed";
                currentState.process = null;
              }
              
              await ctx.client.app.log({
                service: "deep-research-ui",
                level: code === 0 ? "info" : "error",
                message: `Research run ${runId} ${code === 0 ? "completed" : "failed"} with code ${code}`,
              });
            });

            // Handle process errors
            mcpProcess.on("error", async (error) => {
              const currentState = activeRuns.get(runId);
              if (currentState) {
                currentState.status = "failed";
                currentState.process = null;
              }
              
              await ctx.client.app.log({
                service: "deep-research-ui",
                level: "error",
                message: `Research run ${runId} failed with error: ${error.message}`,
              });
            });

            return {
              runId,
              status: "started",
              message: `Research run ${runId} started successfully. The MCP server is processing your query: "${args.query}" with effort level ${args.effort}.`,
            };
          } catch (error) {
            runState.status = "failed";
            
            await ctx.client.app.log({
              service: "deep-research-ui",
              level: "error",
              message: `Failed to start research run ${runId}`,
              extra: { error: error instanceof Error ? error.message : String(error) },
            });

            throw new Error(`Failed to start research run: ${error instanceof Error ? error.message : String(error)}`);
          }
        },
      }),
    },
  };
};

export default DeepResearchUIPlugin;
