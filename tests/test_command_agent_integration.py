"""Integration tests for deep-research command and agent."""

import pytest
import yaml
from pathlib import Path


class TestDeepResearchCommand:
    """Test deep-research command configuration."""

    def test_command_file_exists(self):
        """Test that the deep-research command file exists."""
        command_path = Path(".opencode/commands/deep-research.md")
        assert command_path.exists(), (
            "Command file should exist at .opencode/commands/deep-research.md"
        )

    def test_command_has_arguments_placeholder(self):
        """Test that the command template includes $ARGUMENTS placeholder."""
        command_path = Path(".opencode/commands/deep-research.md")
        content = command_path.read_text()
        assert "$ARGUMENTS" in content, (
            "Command template should include $ARGUMENTS placeholder"
        )

    def test_command_yaml_metadata(self):
        """Test that the command file has proper YAML frontmatter."""
        command_path = Path(".opencode/commands/deep-research.md")
        content = command_path.read_text()

        # Check it starts with ---
        assert content.startswith("---"), (
            "Command file should start with YAML frontmatter delimiter"
        )

        # Find the end of frontmatter
        lines = content.split("\n")
        end_index = next(
            (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None
        )
        assert end_index is not None, "Command file should have proper YAML frontmatter"

        # Parse the frontmatter
        frontmatter = "\n".join(lines[1:end_index])
        import re

        metadata = {}
        for match in re.finditer(r"(\w+):\s*(.+)", frontmatter):
            key = match.group(1)
            value = match.group(2).strip()
            metadata[key] = value

        # Check required fields
        assert "description" in metadata, "Command should have a description"
        assert "agent" in metadata, "Command should specify an agent"
        assert metadata["agent"] == "deep-research-intake", (
            "Command should use deep-research-intake agent"
        )

    def test_command_resolution_instructions(self):
        """Test that the command provides clear resolution instructions."""
        command_path = Path(".opencode/commands/deep-research.md")
        content = command_path.read_text()

        # Check for key responsibilities
        assert "Clarify" in content or "clarify" in content.lower(), (
            "Command should include clarification responsibilities"
        )
        assert "plan" in content.lower() or "Plan" in content, (
            "Command should include planning responsibilities"
        )
        assert "approval" in content.lower() or "approve" in content.lower(), (
            "Command should include approval process"
        )


class TestDeepResearchAgent:
    """Test deep-research-intake agent configuration."""

    def test_agent_yaml_exists(self):
        """Test that the agent YAML file exists."""
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")
        assert agent_path.exists(), (
            "Agent config should exist at .opencode/agents/deep-research-intake/agent.yaml"
        )

    def test_agent_yaml_parseable(self):
        """Test that the agent YAML file is valid YAML."""
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")
        with open(agent_path, "r") as f:
            config = yaml.safe_load(f)

        assert isinstance(config, dict), (
            "Agent config should be a valid YAML dictionary"
        )

    def test_agent_required_fields(self):
        """Test that the agent config has all required fields."""
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")
        with open(agent_path, "r") as f:
            config = yaml.safe_load(f)

        required_fields = ["name", "description", "tools"]
        for field in required_fields:
            assert field in config, f"Agent config should have '{field}' field"

    def test_agent_name(self):
        """Test that the agent has the correct name."""
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")
        with open(agent_path, "r") as f:
            config = yaml.safe_load(f)

        assert config["name"] == "deep-research-intake", (
            "Agent name should be 'deep-research-intake'"
        )

    def test_agent_tools_configuration(self):
        """Test that the agent has correct tools configured."""
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")
        with open(agent_path, "r") as f:
            config = yaml.safe_load(f)

        assert "tools" in config, "Agent should have tools configuration"
        assert isinstance(config["tools"], list), "Tools should be a list"
        assert "deep-research-ui" in config["tools"], (
            "Agent should have deep-research-ui tool"
        )

    def test_agent_system_prompt(self):
        """Test that the agent has a system prompt."""
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")
        with open(agent_path, "r") as f:
            config = yaml.safe_load(f)

        assert "system_prompt" in config, "Agent should have a system_prompt field"
        assert isinstance(config["system_prompt"], str), (
            "System prompt should be a string"
        )
        assert len(config["system_prompt"]) > 0, "System prompt should not be empty"


class TestCommandAgentIntegration:
    """Test integration between command and agent."""

    def test_command_matches_agent(self):
        """Test that the command references the correct agent."""
        command_path = Path(".opencode/commands/deep-research.md")
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")

        # Get agent name from command
        command_content = command_path.read_text()
        import re

        match = re.search(r"agent:\s*(.+)", command_content.split("---")[1])
        assert match is not None, "Command should have agent in frontmatter"
        command_agent = match.group(1).strip()

        # Get agent name from config
        with open(agent_path, "r") as f:
            agent_config = yaml.safe_load(f)

        assert command_agent == agent_config["name"], (
            "Command should reference the correct agent"
        )

    def test_command_tools_compatibility(self):
        """Test that the agent tools are compatible with command requirements."""
        command_path = Path(".opencode/commands/deep-research.md")
        agent_path = Path(".opencode/agents/deep-research-intake/agent.yaml")

        command_content = command_path.read_text()

        # Check that command mentions deep-research-ui tool
        assert "deep-research-ui" in command_content.lower(), (
            "Command should reference deep-research-ui tool"
        )

        # Verify agent has the tool configured
        with open(agent_path, "r") as f:
            agent_config = yaml.safe_load(f)

        assert "deep-research-ui" in agent_config.get("tools", []), (
            "Agent should have deep-research-ui tool configured"
        )
