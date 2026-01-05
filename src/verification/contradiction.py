"""Contradiction detection across research notes."""

from __future__ import annotations

import logging

from src.models import Note, Conflict

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Detect contradictions between research notes."""

    def find_conflicts(self, notes: list[Note]) -> list[Conflict]:
        """Find conflicts between notes.

        Args:
            notes: List of research notes

        Returns:
            List of detected conflicts
        """
        conflicts = []
        n = len(notes)

        for i in range(n):
            for j in range(i + 1, n):
                conflict = self._check_for_conflict(notes[i], notes[j])
                if conflict:
                    conflicts.append(conflict)

        logger.info(f"Found {len(conflicts)} conflicts in {n} notes")
        return conflicts

    def _check_for_conflict(self, note1: Note, note2: Note) -> Conflict | None:
        """Check if two notes contradict each other.

        Args:
            note1: First note
            note2: Second note

        Returns:
            Conflict if found, None otherwise
        """
        conflict_keywords = [
            "however",
            "but",
            "although",
            "contrary",
            "opposite",
            "disagree",
        ]
        negation_keywords = ["not", "no", "never", "none", "neither"]

        content1_lower = note1.content.lower()
        content2_lower = note2.content.lower()

        has_negation_1 = any(neg in content1_lower for neg in negation_keywords)
        has_negation_2 = any(neg in content2_lower for neg in negation_keywords)

        if has_negation_1 and has_negation_2:
            return None

        has_conflict_keyword = any(
            kw in content1_lower or kw in content2_lower for kw in conflict_keywords
        )

        if has_conflict_keyword:
            return Conflict(
                description=f"Potential contradiction between notes from {note1.source_url} and {note2.source_url}",
                conflicting_notes=[note1, note2],
                severity="medium",
            )

        return None
