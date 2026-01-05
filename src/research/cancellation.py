"""Research pipeline with cancellation support."""

import logging
import uuid
from threading import Event
from typing import Optional

from src.models import (
    Document,
    DraftSection,
    Note,
    ResearchRun,
    SearchResult,
    PartialRun,
)
from src.mcp.tools import WebTools

logger = logging.getLogger(__name__)


class RunController:
    """Controller for managing research runs with cancellation support."""

    def __init__(self):
        """Initialize run controller."""
        self.active_runs: dict[str, Event] = {}
        self.run_data: dict[str, ResearchRun] = {}

    def create_run(self, plan: str, effort: int, query: Optional[str] = None) -> str:
        """Create a new research run.

        Args:
            plan: Research plan
            effort: Effort level
            query: Optional search query

        Returns:
            Run ID
        """
        run_id = str(uuid.uuid4())

        run = ResearchRun(
            run_id=run_id,
            plan=plan,
            effort=effort,
            status="initialized",
            query=query or plan,
            search_results=[],
            documents=[],
            notes=[],
            errors=[],
        )

        self.run_data[run_id] = run
        self.active_runs[run_id] = Event()

        logger.info(f"Created run {run_id}")
        return run_id

    def cancel(self, run_id: str) -> PartialRun:
        """Cancel a running research run and return partial artifacts.

        Args:
            run_id: Run ID to cancel

        Returns:
            Partial run with completed artifacts
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Run {run_id} not found")

        cancel_event = self.active_runs[run_id]
        cancel_event.set()

        run = self.run_data.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} data not found")

        run.status = "cancelled"
        logger.info(f"Cancelled run {run_id}")

        partial_run = PartialRun(
            run_id=run_id,
            status="cancelled",
            completed_sections=[],
            citations_collected=[],
            notes=run.notes,
        )

        if run.documents:
            partial_run.completed_sections.append(
                DraftSection(
                    title="Partial Research",
                    content=f"Research was cancelled. Collected {len(run.notes)} notes from {len(run.documents)} documents.",
                )
            )

            for i, doc in enumerate(run.documents, 1):
                partial_run.citations_collected.append((i, doc.url, doc.title))

        return partial_run

    def is_cancelled(self, run_id: str) -> bool:
        """Check if a run has been cancelled.

        Args:
            run_id: Run ID to check

        Returns:
            True if cancelled
        """
        if run_id not in self.active_runs:
            return False

        return self.active_runs[run_id].is_set()

    def cleanup(self, run_id: str):
        """Clean up a completed run.

        Args:
            run_id: Run ID to clean up
        """
        if run_id in self.active_runs:
            del self.active_runs[run_id]

        if run_id in self.run_data:
            del self.run_data[run_id]

        logger.info(f"Cleaned up run {run_id}")
