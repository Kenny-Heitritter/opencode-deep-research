"""Artifact directory layout and management for research runs."""

import os
import json
from pathlib import Path
from typing import Optional
import logging

from ..models import ResearchRun, DraftAST


logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manages artifact directory layout for research runs."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize artifact manager.

        Args:
            project_root: Root directory of the OpenCode project.
                         Defaults to current working directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.artifacts_base = self.project_root / ".opencode" / "deep-research"

    def get_run_dir(self, run_id: str) -> Path:
        """Get the directory path for a research run."""
        return self.artifacts_base / run_id

    def ensure_run_dir(self, run_id: str) -> Path:
        """Ensure the directory for a research run exists."""
        run_dir = self.get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured run directory: {run_dir}")
        return run_dir

    def get_state_path(self, run_id: str) -> Path:
        """Get the path to the state.json file for a run."""
        return self.get_run_dir(run_id) / "state.json"

    def get_report_path(self, run_id: str) -> Path:
        """Get the path to the report.md file for a run."""
        return self.get_run_dir(run_id) / "report.md"

    def get_references_path(self, run_id: str) -> Path:
        """Get the path to the references.json file for a run."""
        return self.get_run_dir(run_id) / "references.json"

    def get_draft_path(self, run_id: str, draft_id: str) -> Path:
        """Get the path to a specific draft file."""
        return self.get_run_dir(run_id) / f"draft_{draft_id}.json"

    def list_runs(self) -> list[str]:
        """List all research run IDs."""
        if not self.artifacts_base.exists():
            return []

        return [
            d.name
            for d in self.artifacts_base.iterdir()
            if d.is_dir() and (d / "state.json").exists()
        ]

    def run_exists(self, run_id: str) -> bool:
        """Check if a research run exists."""
        return self.get_state_path(run_id).exists()

    def delete_run(self, run_id: str) -> bool:
        """Delete all artifacts for a research run."""
        run_dir = self.get_run_dir(run_id)
        if not run_dir.exists():
            return False

        import shutil

        shutil.rmtree(run_dir)
        logger.info(f"Deleted run directory: {run_dir}")
        return True

    def save_state(self, run: ResearchRun) -> Path:
        """
        Save research run state to disk.

        Args:
            run: The research run to save

        Returns:
            Path to the saved state.json file
        """
        from .state import StateManager

        state_manager = StateManager()
        state_path = self.get_state_path(run.run_id)

        self.ensure_run_dir(run.run_id)
        state_manager.save_state(run, state_path)

        logger.info(f"Saved state for run {run.run_id} to {state_path}")
        return state_path

    def load_state(self, run_id: str) -> ResearchRun:
        """
        Load research run state from disk.

        Args:
            run_id: The run ID to load

        Returns:
            The loaded research run

        Raises:
            FileNotFoundError: If the run doesn't exist
        """
        from .state import StateManager

        state_path = self.get_state_path(run_id)
        if not state_path.exists():
            raise FileNotFoundError(f"No state found for run {run_id}")

        state_manager = StateManager()
        run = state_manager.load_state(state_path)

        logger.info(f"Loaded state for run {run_id} from {state_path}")
        return run

    def save_draft_ast(self, run_id: str, draft_ast: DraftAST) -> Path:
        """
        Save a draft AST to disk.

        Args:
            run_id: The run ID
            draft_ast: The draft AST to save

        Returns:
            Path to the saved draft file
        """
        draft_path = self.get_draft_path(run_id, draft_ast.draft_id)
        self.ensure_run_dir(run_id)

        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(draft_ast.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(
            f"Saved draft {draft_ast.draft_id} for run {run_id} to {draft_path}"
        )
        return draft_path

    def load_draft_ast(self, run_id: str, draft_id: str) -> DraftAST:
        """
        Load a draft AST from disk.

        Args:
            run_id: The run ID
            draft_id: The draft ID

        Returns:
            The loaded draft AST

        Raises:
            FileNotFoundError: If the draft doesn't exist
        """
        draft_path = self.get_draft_path(run_id, draft_id)
        if not draft_path.exists():
            raise FileNotFoundError(f"No draft {draft_id} found for run {run_id}")

        with open(draft_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        draft_ast = DraftAST.from_dict(data)
        logger.info(f"Loaded draft {draft_id} for run {run_id} from {draft_path}")
        return draft_ast

    def save_report(self, run_id: str, markdown_content: str) -> Path:
        """
        Save a rendered markdown report to disk.

        Args:
            run_id: The run ID
            markdown_content: The markdown content to save

        Returns:
            Path to the saved report.md file
        """
        report_path = self.get_report_path(run_id)
        self.ensure_run_dir(run_id)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Saved report for run {run_id} to {report_path}")
        return report_path

    def load_report(self, run_id: str) -> str:
        """
        Load a rendered markdown report from disk.

        Args:
            run_id: The run ID

        Returns:
            The markdown content

        Raises:
            FileNotFoundError: If the report doesn't exist
        """
        report_path = self.get_report_path(run_id)
        if not report_path.exists():
            raise FileNotFoundError(f"No report found for run {run_id}")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info(f"Loaded report for run {run_id} from {report_path}")
        return content

    def save_references(self, run_id: str, references: list[dict]) -> Path:
        """
        Save references metadata to disk.

        Args:
            run_id: The run ID
            references: List of reference dictionaries

        Returns:
            Path to the saved references.json file
        """
        refs_path = self.get_references_path(run_id)
        self.ensure_run_dir(run_id)

        with open(refs_path, "w", encoding="utf-8") as f:
            json.dump(references, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved references for run {run_id} to {refs_path}")
        return refs_path

    def load_references(self, run_id: str) -> list[dict]:
        """
        Load references metadata from disk.

        Args:
            run_id: The run ID

        Returns:
            List of reference dictionaries

        Raises:
            FileNotFoundError: If the references file doesn't exist
        """
        refs_path = self.get_references_path(run_id)
        if not refs_path.exists():
            raise FileNotFoundError(f"No references found for run {run_id}")

        with open(refs_path, "r", encoding="utf-8") as f:
            references = json.load(f)

        logger.info(f"Loaded references for run {run_id} from {refs_path}")
        return references
