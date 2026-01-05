"""Contradiction detection across paragraphs in research drafts.

This module provides functionality to detect contradicting claims across
different paragraphs within a research draft.
"""

from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models import Draft, Section, Paragraph, DraftAST, SectionNode, ParagraphNode


class ContradictionSeverity(Enum):
    """Severity levels for contradictions."""

    LOW = "low"  # Possible contradiction, needs review
    MEDIUM = "medium"  # Likely contradiction
    HIGH = "high"  # Clear contradiction


@dataclass
class Contradiction:
    """Represents a detected contradiction between paragraphs."""

    paragraph1_id: str
    paragraph2_id: str
    paragraph1_content: str
    paragraph2_content: str
    reason: str
    severity: ContradictionSeverity
    confidence: float  # 0.0 to 1.0
    section1_title: Optional[str] = None
    section2_title: Optional[str] = None


class ContradictionDetector:
    """Detects contradictions across paragraphs in a draft.

    This implementation provides both heuristic-based detection and
    an extensible interface for LLM-based contradiction detection.
    """

    def __init__(
        self,
        llm_detector: Optional[Callable[[str, str], Tuple[bool, str, float]]] = None,
        min_confidence: float = 0.7,
    ):
        """Initialize contradiction detector.

        Args:
            llm_detector: Optional LLM-based detector that takes two paragraph
                         contents and returns (is_contradiction, reason, confidence).
            min_confidence: Minimum confidence threshold to report contradiction.
        """
        self.llm_detector = llm_detector
        self.min_confidence = min_confidence

        # Common contradiction indicators
        self.negation_words = {
            "not",
            "no",
            "never",
            "neither",
            "none",
            "nothing",
            "nowhere",
            "cannot",
            "can't",
            "won't",
            "don't",
            "doesn't",
            "didn't",
            "isn't",
            "aren't",
            "wasn't",
            "weren't",
        }

        self.opposition_pairs = [
            ("increase", "decrease"),
            ("increas", "decreas"),  # Catch increasing/decreasing
            ("grow", "shrink"),
            ("growth", "decline"),  # Catch growth/decline
            ("rise", "fall"),
            ("improve", "worsen"),
            ("succeed", "fail"),
            ("success", "failure"),
            ("positive", "negative"),
            ("beneficial", "harmful"),
            ("safe", "dangerous"),
            ("effective", "ineffective"),
            ("always", "never"),
            ("all", "none"),
            ("every", "no"),
            ("more", "less"),
            ("higher", "lower"),
            ("better", "worse"),
        ]

    def find_contradictions(self, draft: Draft) -> List[Contradiction]:
        """Find contradictions in a Draft object.

        Args:
            draft: The draft to analyze

        Returns:
            List of detected contradictions
        """
        paragraphs_with_context = []

        # Collect all paragraphs with their section context
        for section in draft.sections:
            self._collect_paragraphs_recursive(section, paragraphs_with_context)

        return self._find_contradictions_in_paragraphs(paragraphs_with_context)

    def find_contradictions_ast(self, draft_ast: DraftAST) -> List[Contradiction]:
        """Find contradictions in a DraftAST object.

        Args:
            draft_ast: The draft AST to analyze

        Returns:
            List of detected contradictions
        """
        paragraphs_with_context = []

        # Collect all paragraphs with their section context
        for section in draft_ast.sections:
            self._collect_paragraphs_ast_recursive(section, paragraphs_with_context)

        return self._find_contradictions_in_paragraphs(paragraphs_with_context)

    def _collect_paragraphs_recursive(
        self, section: Section, result: List[Tuple[str, str, str]]
    ) -> None:
        """Recursively collect paragraphs from Section with context.

        Args:
            section: Section to collect from
            result: List to append (paragraph_id, content, section_title) tuples
        """
        for para in section.paragraphs:
            result.append((para.id, para.content, section.title))

        for subsection in section.subsections:
            self._collect_paragraphs_recursive(subsection, result)

    def _collect_paragraphs_ast_recursive(
        self, section: SectionNode, result: List[Tuple[str, str, str]]
    ) -> None:
        """Recursively collect paragraphs from SectionNode with context.

        Args:
            section: SectionNode to collect from
            result: List to append (paragraph_id, content, section_title) tuples
        """
        for para in section.paragraphs:
            result.append((para.id, para.content, section.title))

        for subsection in section.subsections:
            self._collect_paragraphs_ast_recursive(subsection, result)

    def _find_contradictions_in_paragraphs(
        self, paragraphs: List[Tuple[str, str, str]]
    ) -> List[Contradiction]:
        """Find contradictions among a list of paragraphs.

        Args:
            paragraphs: List of (paragraph_id, content, section_title) tuples

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Compare each pair of paragraphs
        for i in range(len(paragraphs)):
            for j in range(i + 1, len(paragraphs)):
                para1_id, para1_content, section1 = paragraphs[i]
                para2_id, para2_content, section2 = paragraphs[j]

                # Skip if same paragraph or empty content
                if not para1_content.strip() or not para2_content.strip():
                    continue

                # Check for contradiction
                contradiction = self._check_pair(
                    para1_id,
                    para1_content,
                    para2_id,
                    para2_content,
                    section1,
                    section2,
                )

                if contradiction:
                    contradictions.append(contradiction)

        return contradictions

    def _check_pair(
        self,
        para1_id: str,
        para1_content: str,
        para2_id: str,
        para2_content: str,
        section1_title: str,
        section2_title: str,
    ) -> Optional[Contradiction]:
        """Check if two paragraphs contradict each other.

        Args:
            para1_id: ID of first paragraph
            para1_content: Content of first paragraph
            para2_id: ID of second paragraph
            para2_content: Content of second paragraph
            section1_title: Title of section containing first paragraph
            section2_title: Title of section containing second paragraph

        Returns:
            Contradiction object if detected, None otherwise
        """
        # Use LLM detector if available
        if self.llm_detector:
            is_contradiction, reason, confidence = self.llm_detector(
                para1_content, para2_content
            )

            if is_contradiction and confidence >= self.min_confidence:
                severity = self._determine_severity(confidence)
                return Contradiction(
                    paragraph1_id=para1_id,
                    paragraph2_id=para2_id,
                    paragraph1_content=para1_content,
                    paragraph2_content=para2_content,
                    reason=reason,
                    severity=severity,
                    confidence=confidence,
                    section1_title=section1_title,
                    section2_title=section2_title,
                )

        # Fallback: Heuristic-based detection
        heuristic_result = self._heuristic_check(para1_content, para2_content)

        if heuristic_result:
            reason, confidence = heuristic_result
            if confidence >= self.min_confidence:
                severity = self._determine_severity(confidence)
                return Contradiction(
                    paragraph1_id=para1_id,
                    paragraph2_id=para2_id,
                    paragraph1_content=para1_content,
                    paragraph2_content=para2_content,
                    reason=reason,
                    severity=severity,
                    confidence=confidence,
                    section1_title=section1_title,
                    section2_title=section2_title,
                )

        return None

    def _heuristic_check(
        self, content1: str, content2: str
    ) -> Optional[Tuple[str, float]]:
        """Heuristic-based contradiction check.

        Args:
            content1: First paragraph content
            content2: Second paragraph content

        Returns:
            (reason, confidence) tuple if potential contradiction, None otherwise
        """
        content1_lower = content1.lower()
        content2_lower = content2.lower()

        # Tokenize
        words1 = set(content1_lower.split())
        words2 = set(content2_lower.split())

        # Check for opposition pairs
        for word1, word2 in self.opposition_pairs:
            if (word1 in content1_lower and word2 in content2_lower) or (
                word2 in content1_lower and word1 in content2_lower
            ):
                # Check if they're discussing the same topic (keyword overlap)
                overlap = len(words1 & words2)
                if overlap >= 3:  # Sufficient topic overlap
                    return (
                        f"Opposing terms detected: '{word1}' vs '{word2}' with topic overlap",
                        0.75,
                    )

        # Check for negation patterns with similar content
        has_negation1 = any(neg in words1 for neg in self.negation_words)
        has_negation2 = any(neg in words2 for neg in self.negation_words)

        if has_negation1 != has_negation2:  # One has negation, other doesn't
            # Calculate content similarity (ignoring negation words)
            words1_filtered = words1 - self.negation_words
            words2_filtered = words2 - self.negation_words

            if words1_filtered and words2_filtered:
                overlap = len(words1_filtered & words2_filtered)
                similarity = overlap / max(len(words1_filtered), len(words2_filtered))

                if similarity > 0.4:  # High similarity but opposite polarity
                    return (
                        "High content similarity with opposing polarity (negation)",
                        0.7,
                    )

        return None

    def _determine_severity(self, confidence: float) -> ContradictionSeverity:
        """Determine severity based on confidence.

        Args:
            confidence: Confidence score

        Returns:
            ContradictionSeverity level
        """
        if confidence >= 0.9:
            return ContradictionSeverity.HIGH
        elif confidence >= 0.75:
            return ContradictionSeverity.MEDIUM
        else:
            return ContradictionSeverity.LOW

    def get_high_severity_contradictions(
        self, contradictions: List[Contradiction]
    ) -> List[Contradiction]:
        """Filter to only high severity contradictions.

        Args:
            contradictions: All detected contradictions

        Returns:
            List of high severity contradictions
        """
        return [c for c in contradictions if c.severity == ContradictionSeverity.HIGH]
