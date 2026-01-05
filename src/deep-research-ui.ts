import { Plugin } from "@opencode-ai/plugin";
import { createDeepResearchTool } from "./tools";

export const DeepResearchUIPlugin: Plugin = async (ctx) => {
  const deepResearchTool = createDeepResearchTool({
    serverUrl: ctx.serverUrl,
  });

  return {
    tool: {
      "deep_research_ui": deepResearchTool,
    },
  };
};

export default DeepResearchUIPlugin;