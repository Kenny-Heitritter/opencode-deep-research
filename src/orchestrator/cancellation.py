"""Cancellation support for research runs.

This module provides functionality to cancel a research run mid-execution
and return partial artifacts representing the work completed so far.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..models import ResearchRun, Draft, Section, Paragraph, ResearchPhase
from ..artifacts import Renderer


class CancellationStatus(Enum):
    """Status after cancellation."""

    CANCELLED_PLANNING = "cancelled_planning"
    CANCELLED_GATHERING = "cancelled_gathering"
    CANCELLED_ANALYSIS = "cancelled_analysis"
    CANCELLED_DRAFTING = "cancelled_drafting"
    COMPLETED = "completed"  # Not actually cancelled


@dataclass
class PartialArtifact:
    """Represents partial results from a cancelled research run."""

    run_id: str
    original_query: str
    cancellation_status: CancellationStatus
    phase_at_cancellation: ResearchPhase
    sections_completed: List[Section]
    current_draft: Optional[Draft] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancelled_at: datetime = field(default_factory=datetime.utcnow)

    def to_markdown(self) -> str:
        """Convert partial artifact to markdown report.

        Returns:
            Markdown formatted report of partial results
        """
        lines = []

        # Header
        lines.append("# Research Report (Incomplete)")
        lines.append("")
        lines.append(f"**Query:** {self.original_query}")
        lines.append("")
        lines.append(
            f"**Status:** Research was cancelled during the {self.phase_at_cancellation.value} phase"
        )
        lines.append(f"**Cancelled at:** {self.cancelled_at.isoformat()}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Phase-specific content
        if self.phase_at_cancellation == ResearchPhase.PLANNING:
            lines.append("## Status")
            lines.append("")
            lines.append(
                "Research was cancelled during the planning phase. "
                "No outline or content has been generated yet."
            )
            lines.append("")

            if self.metadata.get("clarifying_questions"):
                lines.append("### Clarifying Questions Generated")
                lines.append("")
                for q in self.metadata["clarifying_questions"]:
                    lines.append(f"- {q}")
                lines.append("")

            if self.metadata.get("proposed_plans"):
                lines.append("### Proposed Research Plans")
                lines.append("")
                for i, plan in enumerate(self.metadata["proposed_plans"], 1):
                    lines.append(f"**Plan {i}:** {plan}")
                    lines.append("")

        elif self.phase_at_cancellation == ResearchPhase.GATHERING:
            lines.append("## Status")
            lines.append("")
            lines.append(
                "Research was cancelled during the evidence gathering phase. "
                "Partial evidence has been collected."
            )
            lines.append("")

            if self.metadata.get("outline"):
                lines.append("### Planned Outline")
                lines.append("")
                lines.append(self.metadata["outline"])
                lines.append("")

            if self.metadata.get("queries_completed"):
                lines.append("### Search Queries Completed")
                lines.append("")
                for q in self.metadata["queries_completed"]:
                    lines.append(f"- {q}")
                lines.append("")

            if self.metadata.get("sources_gathered"):
                lines.append("### Sources Gathered")
                lines.append("")
                for source in self.metadata["sources_gathered"]:
                    lines.append(f"- {source}")
                lines.append("")

        elif self.phase_at_cancellation == ResearchPhase.ANALYSIS:
            lines.append("## Status")
            lines.append("")
            lines.append(
                "Research was cancelled during the analysis phase. "
                "Evidence has been gathered but analysis is incomplete."
            )
            lines.append("")

            if self.metadata.get("outline"):
                lines.append("### Outline")
                lines.append("")
                lines.append(self.metadata["outline"])
                lines.append("")

            if self.metadata.get("evidence_count"):
                lines.append(
                    f"### Evidence Collected: {self.metadata['evidence_count']} items"
                )
                lines.append("")

        elif self.phase_at_cancellation == ResearchPhase.DRAFTING:
            lines.append("## Partial Report")
            lines.append("")
            lines.append(
                "*Note: This report is incomplete. Research was cancelled during drafting.*"
            )
            lines.append("")

            # Render completed sections
            if self.sections_completed:
                for section in self.sections_completed:
                    lines.extend(self._render_section(section))
                    lines.append("")

            # Note about incomplete sections
            if self.metadata.get("sections_remaining"):
                lines.append("### Sections Not Completed")
                lines.append("")
                for title in self.metadata["sections_remaining"]:
                    lines.append(f"- {title}")
                lines.append("")

        else:  # COMPLETE or FAILED
            lines.append("## Status")
            lines.append("")
            lines.append(
                f"Research ended with status: {self.phase_at_cancellation.value}"
            )
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(
            "*This is a partial artifact from a cancelled research run. "
            "To get a complete report, please run the research again.*"
        )

        return "\n".join(lines)

    def _render_section(self, section: Section, level: int = 1) -> List[str]:
        """Render a section to markdown lines.

        Args:
            section: Section to render
            level: Heading level (1-6)

        Returns:
            List of markdown lines
        """
        lines = []
        heading = "#" * level

        lines.append(f"{heading} {section.title}")
        lines.append("")

        # Render paragraphs
        for para in section.paragraphs:
            lines.append(para.content)
            lines.append("")

        # Render subsections
        for subsection in section.subsections:
            lines.extend(self._render_section(subsection, level + 1))

        return lines

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "original_query": self.original_query,
            "cancellation_status": self.cancellation_status.value,
            "phase_at_cancellation": self.phase_at_cancellation.value,
            "sections_completed": [s.to_dict() for s in self.sections_completed],
            "current_draft": self.current_draft.to_dict()
            if self.current_draft
            else None,
            "metadata": self.metadata,
            "cancelled_at": self.cancelled_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartialArtifact":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            original_query=data["original_query"],
            cancellation_status=CancellationStatus(data["cancellation_status"]),
            phase_at_cancellation=ResearchPhase(data["phase_at_cancellation"]),
            sections_completed=[
                Section.from_dict(s) for s in data.get("sections_completed", [])
            ],
            current_draft=Draft.from_dict(data["current_draft"])
            if data.get("current_draft")
            else None,
            metadata=data.get("metadata", {}),
            cancelled_at=datetime.fromisoformat(data["cancelled_at"]),
        )


class Cancellation:
    """Handles cancellation of research runs.

    This class manages the cancellation process, ensuring that partial
    artifacts are properly saved and returned to the user.
    """

    def __init__(self):
        """Initialize cancellation handler."""
        self._cancelled_runs: Dict[str, PartialArtifact] = {}

    def cancel_run(self, run: ResearchRun) -> PartialArtifact:
        """Cancel a research run and return partial artifacts.

        Args:
            run: The research run to cancel

        Returns:
            PartialArtifact containing work completed so far
        """
        # Determine cancellation status based on phase
        status_map = {
            ResearchPhase.PLANNING: CancellationStatus.CANCELLED_PLANNING,
            ResearchPhase.GATHERING: CancellationStatus.CANCELLED_GATHERING,
            ResearchPhase.ANALYSIS: CancellationStatus.CANCELLED_ANALYSIS,
            ResearchPhase.DRAFTING: CancellationStatus.CANCELLED_DRAFTING,
            ResearchPhase.COMPLETE: CancellationStatus.COMPLETED,
            ResearchPhase.FAILED: CancellationStatus.COMPLETED,  # Use COMPLETED for failed
        }

        cancellation_status = status_map.get(
            run.phase, CancellationStatus.CANCELLED_PLANNING
        )

        # Extract completed sections from current draft
        sections_completed = []
        current_draft = run.get_current_draft()

        if current_draft:
            sections_completed = current_draft.sections

        # Create partial artifact
        artifact = PartialArtifact(
            run_id=run.run_id,
            original_query=run.query,
            cancellation_status=cancellation_status,
            phase_at_cancellation=run.phase,
            sections_completed=sections_completed,
            current_draft=current_draft,
            metadata=run.metadata.copy(),
        )

        # Store for retrieval
        self._cancelled_runs[run.run_id] = artifact

        return artifact

    def get_partial_artifact(self, run_id: str) -> Optional[PartialArtifact]:
        """Retrieve a partial artifact for a cancelled run.

        Args:
            run_id: ID of the cancelled run

        Returns:
            PartialArtifact if found, None otherwise
        """
        return self._cancelled_runs.get(run_id)

    def is_cancelled(self, run_id: str) -> bool:
        """Check if a run has been cancelled.

        Args:
            run_id: ID of the run to check

        Returns:
            True if run was cancelled
        """
        return run_id in self._cancelled_runs

    def clear_cancelled_run(self, run_id: str) -> None:
        """Clear a cancelled run from storage.

        Args:
            run_id: ID of the run to clear
        """
        if run_id in self._cancelled_runs:
            del self._cancelled_runs[run_id]
