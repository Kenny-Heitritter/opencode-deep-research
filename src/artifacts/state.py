"""JSON serialization for research run state and replay mode."""

import json
from pathlib import Path
from typing import Union
import logging

from ..models import ResearchRun


logger = logging.getLogger(__name__)


class StateManager:
    """Manages serialization and deserialization of research run state."""

    def save_state(self, run: ResearchRun, path: Union[str, Path]) -> None:
        """
        Save research run state to JSON file.

        Args:
            run: The research run to save
            path: Path to save the state.json file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        state_dict = run.to_dict()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved state for run {run.run_id} to {path}")

    def load_state(self, path: Union[str, Path]) -> ResearchRun:
        """
        Load research run state from JSON file.

        Args:
            path: Path to the state.json file

        Returns:
            The loaded research run

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
            ValueError: If the state data is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            state_dict = json.load(f)

        try:
            run = ResearchRun.from_dict(state_dict)
            logger.info(f"Loaded state for run {run.run_id} from {path}")
            return run
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid state data in {path}: {e}")

    def save_state_pretty(self, run: ResearchRun, path: Union[str, Path]) -> None:
        """
        Save research run state with extra pretty formatting for debugging.

        Args:
            run: The research run to save
            path: Path to save the state.json file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        state_dict = run.to_dict()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, indent=4, ensure_ascii=False, sort_keys=True)

        logger.info(f"Saved pretty state for run {run.run_id} to {path}")

    def validate_state(self, path: Union[str, Path]) -> bool:
        """
        Validate that a state file can be loaded successfully.

        Args:
            path: Path to the state.json file

        Returns:
            True if valid, False otherwise
        """
        try:
            self.load_state(path)
            return True
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"State validation failed for {path}: {e}")
            return False
