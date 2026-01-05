
import type { Plugin } from "@opencode-ai/plugin";

const PermissionsPlugin: Plugin = async () => {
  console.log("[swarm-permissions] Allowing all filesystem access (isolated container)");
  return {
    "permission.ask": async (info: any, output: any) => {
      // Allow all permission requests - we're in an isolated container
      output.status = "allow";
      console.log(`[swarm-permissions] Auto-allowed: ${info.type} ${JSON.stringify(info.pattern || info.command || '')}`);
    }
  };
};

export default PermissionsPlugin;
