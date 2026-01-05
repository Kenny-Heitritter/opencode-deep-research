"""World model for Deep Research competition."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

from src.models import ResearchRun, SearchResult, Note

logger = logging.getLogger(__name__)


@dataclass
class WorldState:
    """World state for the research competition."""

    run_id: str
    plan: str
    effort: int
    phase: str = "initialize"
    search_results: list[SearchResult] = field(default_factory=list)
    documents: list[Any] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    outlines: list[Any] = field(default_factory=list)
    selected_outline: Optional[Any] = None
    query_results: dict[str, list[Any]] = field(default_factory=dict)
    drafts: list[Any] = field(default_factory=list)
    selected_draft: Optional[Any] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(self, updates: dict[str, Any]) -> None:
        """Update world state with new data.

        Args:
            updates: Dictionary of fields to update
        """
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()


@dataclass
class ResearchWorld:
    """World model for research competition with llm-reasoners interface."""

    def initialize(self, plan: str, effort: int) -> WorldState:
        """Initialize a new research world.

        Args:
            plan: Research plan or topic
            effort: Research effort level (1-5)

        Returns:
            Initial WorldState
        """
        import uuid

        run_id = str(uuid.uuid4())
        state = WorldState(
            run_id=run_id,
            plan=plan,
            effort=max(1, min(5, effort)),
            phase="initialize",
        )
        logger.info(f"Initialized ResearchWorld with run_id={run_id}, effort={effort}")
        return state

    def get_state(self, run_id: str) -> Optional[WorldState]:
        """Get current world state for a run.

        Args:
            run_id: Research run ID

        Returns:
            Current WorldState or None if not found
        """
        state = self._load_state(run_id)
        if state:
            logger.debug(f"Retrieved state for run_id={run_id}")
        return state

    def save_state(self, state: WorldState) -> None:
        """Save world state.

        Args:
            state: WorldState to save
        """
        self._save_state(state)
        logger.debug(f"Saved state for run_id={state.run_id}")

    def update_state(self, state: WorldState, phase: str, **kwargs) -> WorldState:
        """Update world state with new phase and data.

        Args:
            state: Current WorldState
            phase: New phase name
            **kwargs: Additional fields to update

        Returns:
            Updated WorldState
        """
        updates = {"phase": phase, **kwargs}
        state.update(updates)
        self.save_state(state)
        return state

    def _load_state(self, run_id: str) -> Optional[WorldState]:
        """Load state from storage (placeholder for actual storage).

        Args:
            run_id: Research run ID

        Returns:
            Loaded WorldState or None
        """
        return None

    def _save_state(self, state: WorldState) -> None:
        """Save state to storage (placeholder for actual storage).

        Args:
            state: WorldState to save
        """
        pass
