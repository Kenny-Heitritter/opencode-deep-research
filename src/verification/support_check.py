"""Support checking for paragraph claims against evidence.

This module provides functionality to verify that claims made in paragraphs
are properly supported by the evidence (notes) they reference.
"""

from typing import List, Optional, Callable
from dataclasses import dataclass

from ..models import DraftNote, ParagraphNode, EvidenceNote


@dataclass
class SupportCheckResult:
    """Result of checking paragraph support."""

    paragraph_id: str
    is_supported: bool
    confidence: float  # 0.0 to 1.0
    issues: List[str]  # List of specific issues found
    checked_note_ids: List[str]


class SupportChecker:
    """Checks if paragraph claims are supported by their evidence notes.

    This implementation provides both a simple keyword-based checker and
    an extensible interface for LLM-based verification.
    """

    def __init__(
        self,
        llm_checker: Optional[Callable[[str, List[DraftNote]], bool]] = None,
        min_confidence: float = 0.6,
    ):
        """Initialize support checker.

        Args:
            llm_checker: Optional LLM-based checker function that takes
                        (paragraph_content, notes) and returns bool.
            min_confidence: Minimum confidence threshold for support (0.0-1.0).
        """
        self.llm_checker = llm_checker
        self.min_confidence = min_confidence

    def check_paragraph(
        self, paragraph: ParagraphNode, notes: List[DraftNote]
    ) -> SupportCheckResult:
        """Check if a paragraph is supported by its notes.

        Args:
            paragraph: The paragraph to check
            notes: List of notes that should support the paragraph

        Returns:
            SupportCheckResult with details about the check
        """
        issues = []
        checked_note_ids = [note.id for note in notes]

        # Check 1: Does paragraph have any notes?
        if not notes:
            issues.append("Paragraph has no supporting notes")
            return SupportCheckResult(
                paragraph_id=paragraph.id,
                is_supported=False,
                confidence=0.0,
                issues=issues,
                checked_note_ids=checked_note_ids,
            )

        # Check 2: Are the notes referenced in the paragraph?
        note_ids_set = set(note.id for note in notes)
        para_note_ids_set = set(paragraph.note_ids)

        missing_notes = para_note_ids_set - note_ids_set
        if missing_notes:
            issues.append(f"Paragraph references notes not provided: {missing_notes}")

        # Check 3: Do notes have content?
        empty_notes = [note.id for note in notes if not note.content.strip()]
        if empty_notes:
            issues.append(f"Empty notes found: {empty_notes}")

        # Check 4: Confidence check on notes
        low_confidence_notes = [
            note.id for note in notes if note.confidence < self.min_confidence
        ]
        if low_confidence_notes:
            issues.append(
                f"Low confidence notes (<{self.min_confidence}): {low_confidence_notes}"
            )

        # Check 5: Use LLM checker if available
        if self.llm_checker:
            llm_supported = self.llm_checker(paragraph.content, notes)
            if not llm_supported:
                issues.append("LLM checker determined claims are not supported")
        else:
            # Fallback: Simple keyword overlap check
            keyword_support = self._check_keyword_overlap(paragraph.content, notes)
            if not keyword_support:
                issues.append(
                    "Low keyword overlap between paragraph and supporting notes"
                )

        # Calculate overall confidence
        confidence = self._calculate_confidence(paragraph, notes, issues)

        # Determine if supported
        is_supported = len(issues) == 0 and confidence >= self.min_confidence

        return SupportCheckResult(
            paragraph_id=paragraph.id,
            is_supported=is_supported,
            confidence=confidence,
            issues=issues,
            checked_note_ids=checked_note_ids,
        )

    def _check_keyword_overlap(
        self, paragraph_content: str, notes: List[DraftNote]
    ) -> bool:
        """Simple keyword overlap check between paragraph and notes.

        Args:
            paragraph_content: Content of the paragraph
            notes: Supporting notes

        Returns:
            True if sufficient keyword overlap exists
        """
        # Tokenize and normalize
        para_words = set(
            word.lower().strip(".,!?;:")
            for word in paragraph_content.split()
            if len(word) > 3  # Ignore short words
        )

        note_words = set()
        for note in notes:
            note_words.update(
                word.lower().strip(".,!?;:")
                for word in note.content.split()
                if len(word) > 3
            )

        # Calculate overlap
        if not para_words:
            return False

        overlap = para_words & note_words
        overlap_ratio = len(overlap) / len(para_words)

        # Require at least 20% keyword overlap
        return overlap_ratio >= 0.2

    def _calculate_confidence(
        self, paragraph: ParagraphNode, notes: List[DraftNote], issues: List[str]
    ) -> float:
        """Calculate confidence score for support.

        Args:
            paragraph: The paragraph being checked
            notes: Supporting notes
            issues: List of issues found

        Returns:
            Confidence score from 0.0 to 1.0
        """
        if not notes:
            return 0.0

        # Start with average note confidence
        avg_note_confidence = sum(note.confidence for note in notes) / len(notes)

        # Penalize for issues (each issue reduces confidence)
        issue_penalty = min(len(issues) * 0.15, 0.6)  # Max 60% penalty

        confidence = max(0.0, avg_note_confidence - issue_penalty)

        return confidence

    def check_all_paragraphs(
        self, paragraphs: List[ParagraphNode], all_notes: List[DraftNote]
    ) -> List[SupportCheckResult]:
        """Check support for multiple paragraphs.

        Args:
            paragraphs: List of paragraphs to check
            all_notes: All available notes

        Returns:
            List of SupportCheckResult for each paragraph
        """
        # Build note lookup
        notes_by_id = {note.id: note for note in all_notes}

        results = []
        for para in paragraphs:
            # Get notes referenced by this paragraph
            para_notes = [
                notes_by_id[note_id]
                for note_id in para.note_ids
                if note_id in notes_by_id
            ]

            result = self.check_paragraph(para, para_notes)
            results.append(result)

        return results

    def get_unsupported_paragraphs(
        self, paragraphs: List[ParagraphNode], all_notes: List[DraftNote]
    ) -> List[SupportCheckResult]:
        """Get only the paragraphs that are not properly supported.

        Args:
            paragraphs: List of paragraphs to check
            all_notes: All available notes

        Returns:
            List of SupportCheckResult for unsupported paragraphs
        """
        all_results = self.check_all_paragraphs(paragraphs, all_notes)
        return [result for result in all_results if not result.is_supported]
