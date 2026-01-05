"""Uncertainty tracking for research reports.

This module tracks uncertainties and contradictions discovered during research,
to be included in the final report as a dedicated section.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .contradiction import Contradiction


class UncertaintyType(Enum):
    """Types of uncertainties."""

    CONTRADICTION = "contradiction"  # Conflicting information found
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # Not enough evidence
    CONFLICTING_SOURCES = "conflicting_sources"  # Sources disagree
    UNCERTAIN_CLAIM = "uncertain_claim"  # Claim made with low confidence
    UNRESOLVED_QUESTION = "unresolved_question"  # Question without answer


@dataclass
class Uncertainty:
    """Represents an uncertainty or unresolved issue in research."""

    id: str
    type: UncertaintyType
    claim: str
    reason: str
    related_paragraph_ids: List[str] = field(default_factory=list)
    related_section_titles: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)  # URLs or citations
    confidence: float = 0.5  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "claim": self.claim,
            "reason": self.reason,
            "related_paragraph_ids": self.related_paragraph_ids,
            "related_section_titles": self.related_section_titles,
            "sources": self.sources,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Uncertainty":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=UncertaintyType(data["type"]),
            claim=data["claim"],
            reason=data["reason"],
            related_paragraph_ids=data.get("related_paragraph_ids", []),
            related_section_titles=data.get("related_section_titles", []),
            sources=data.get("sources", []),
            confidence=data.get("confidence", 0.5),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class UncertaintyTracker:
    """Tracks uncertainties and contradictions throughout research.

    This tracker maintains a collection of uncertainties that can be
    included in the final report as a dedicated section.
    """

    def __init__(self):
        """Initialize uncertainty tracker."""
        self.uncertainties: List[Uncertainty] = []
        self._id_counter = 0

    def add_uncertainty(
        self,
        claim: str,
        reason: str,
        uncertainty_type: UncertaintyType = UncertaintyType.UNCERTAIN_CLAIM,
        related_paragraph_ids: Optional[List[str]] = None,
        related_section_titles: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        confidence: float = 0.5,
    ) -> Uncertainty:
        """Add a new uncertainty.

        Args:
            claim: The uncertain claim or topic
            reason: Explanation of why this is uncertain
            uncertainty_type: Type of uncertainty
            related_paragraph_ids: IDs of related paragraphs
            related_section_titles: Titles of related sections
            sources: Source URLs or citations
            confidence: Confidence level (0.0-1.0)

        Returns:
            The created Uncertainty object
        """
        self._id_counter += 1
        uncertainty = Uncertainty(
            id=f"uncertainty-{self._id_counter}",
            type=uncertainty_type,
            claim=claim,
            reason=reason,
            related_paragraph_ids=related_paragraph_ids or [],
            related_section_titles=related_section_titles or [],
            sources=sources or [],
            confidence=confidence,
        )

        self.uncertainties.append(uncertainty)
        return uncertainty

    def add_contradiction_as_uncertainty(
        self, contradiction: Contradiction
    ) -> Uncertainty:
        """Add a contradiction as an uncertainty.

        Args:
            contradiction: Contradiction to add

        Returns:
            The created Uncertainty object
        """
        claim = f"Conflicting information found"
        reason = (
            f"{contradiction.reason}\n\n"
            f"Claim 1: {contradiction.paragraph1_content[:200]}...\n\n"
            f"Claim 2: {contradiction.paragraph2_content[:200]}..."
        )

        return self.add_uncertainty(
            claim=claim,
            reason=reason,
            uncertainty_type=UncertaintyType.CONTRADICTION,
            related_paragraph_ids=[
                contradiction.paragraph1_id,
                contradiction.paragraph2_id,
            ],
            related_section_titles=[
                t
                for t in [
                    contradiction.section1_title,
                    contradiction.section2_title,
                ]
                if t
            ],
            confidence=contradiction.confidence,
        )

    def get_all_uncertainties(self) -> List[Uncertainty]:
        """Get all tracked uncertainties.

        Returns:
            List of all uncertainties
        """
        return self.uncertainties.copy()

    def get_by_type(self, uncertainty_type: UncertaintyType) -> List[Uncertainty]:
        """Get uncertainties of a specific type.

        Args:
            uncertainty_type: Type to filter by

        Returns:
            List of uncertainties of that type
        """
        return [u for u in self.uncertainties if u.type == uncertainty_type]

    def get_high_priority(
        self, min_confidence_threshold: float = 0.7
    ) -> List[Uncertainty]:
        """Get high-priority uncertainties.

        High-priority uncertainties are those with confidence below threshold,
        indicating they are more uncertain and need attention.

        Args:
            min_confidence_threshold: Maximum confidence to be considered high priority

        Returns:
            List of high-priority uncertainties
        """
        return [
            u for u in self.uncertainties if u.confidence < min_confidence_threshold
        ]

    def clear(self) -> None:
        """Clear all uncertainties."""
        self.uncertainties.clear()
        self._id_counter = 0

    def to_markdown(self) -> str:
        """Generate markdown section for uncertainties and contradictions.

        Returns:
            Markdown formatted section
        """
        if not self.uncertainties:
            return ""

        lines = ["## Uncertainties and Contradictions", ""]
        lines.append(
            "The following uncertainties and contradictions were identified during research:"
        )
        lines.append("")

        # Group by type
        by_type: Dict[UncertaintyType, List[Uncertainty]] = {}
        for uncertainty in self.uncertainties:
            if uncertainty.type not in by_type:
                by_type[uncertainty.type] = []
            by_type[uncertainty.type].append(uncertainty)

        # Render each type
        type_titles = {
            UncertaintyType.CONTRADICTION: "### Contradictory Information",
            UncertaintyType.CONFLICTING_SOURCES: "### Conflicting Sources",
            UncertaintyType.INSUFFICIENT_EVIDENCE: "### Insufficient Evidence",
            UncertaintyType.UNCERTAIN_CLAIM: "### Uncertain Claims",
            UncertaintyType.UNRESOLVED_QUESTION: "### Unresolved Questions",
        }

        for unc_type, title in type_titles.items():
            if unc_type in by_type:
                lines.append(title)
                lines.append("")

                for uncertainty in by_type[unc_type]:
                    lines.append(f"**{uncertainty.claim}**")
                    lines.append("")
                    lines.append(uncertainty.reason)
                    lines.append("")

                    if uncertainty.sources:
                        lines.append("*Sources:*")
                        for source in uncertainty.sources:
                            lines.append(f"- {source}")
                        lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker state to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "uncertainties": [u.to_dict() for u in self.uncertainties],
            "id_counter": self._id_counter,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UncertaintyTracker":
        """Create tracker from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            UncertaintyTracker instance
        """
        tracker = cls()
        tracker.uncertainties = [
            Uncertainty.from_dict(u) for u in data.get("uncertainties", [])
        ]
        tracker._id_counter = data.get("id_counter", 0)
        return tracker
