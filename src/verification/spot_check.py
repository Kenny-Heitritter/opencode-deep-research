"""Spot checking for paragraph-level claim verification."""

import logging
import re
from typing import Optional

from src.models import Note, Claim, Document

logger = logging.getLogger(__name__)


class SpotChecker:
    """Verify claims against citation evidence."""

    def __init__(self, documents: list[Document]):
        """Initialize spot checker with documents.

        Args:
            documents: Fetched documents for evidence lookup
        """
        self.documents = {doc.url: doc for doc in documents}

    def verify(self, claims: list[Claim], notes: list[Note]) -> list[Claim]:
        """Verify claims using citation evidence.

        Args:
            claims: Claims to verify
            notes: Extracted notes with citation spans

        Returns:
            Verified claims with updated strength scores
        """
        verified_claims = []

        for claim in claims:
            if not claim.citation_indices:
                claim.strength_score = 0.1
                claim.needs_verification = True
                verified_claims.append(claim)
                continue

            total_strength = 0.0
            for note_index in claim.citation_indices:
                if note_index < len(notes):
                    strength = self._verify_against_note(claim, notes[note_index])
                    total_strength += strength

            claim.strength_score = total_strength / len(claim.citation_indices)
            claim.needs_verification = claim.strength_score < 0.5
            verified_claims.append(claim)

        logger.info(
            f"Verified {len(verified_claims)} claims, "
            f"{sum(1 for c in verified_claims if c.needs_verification)} need verification"
        )

        return verified_claims

    def _verify_against_note(self, claim: Claim, note: Note) -> float:
        """Verify a claim against a single note.

        Args:
            claim: Claim to verify
            note: Note with evidence

        Returns:
            Strength score (0.0 to 1.0)
        """
        doc = self.documents.get(note.source_url)
        if not doc:
            return 0.1

        if note.span_start is not None and note.span_end is not None:
            evidence = doc.content[note.span_start : note.span_end]
        else:
            evidence = doc.content

        strength = self._calculate_support(claim.text, evidence, note.content)
        return strength

    def _calculate_support(self, claim: str, evidence: str, note_content: str) -> float:
        """Calculate support score between claim and evidence.

        Args:
            claim: Claim text
            evidence: Document evidence
            note_content: Extracted note content

        Returns:
            Support score (0.0 to 1.0)
        """
        claim_lower = claim.lower()
        note_lower = note_content.lower()
        evidence_lower = evidence.lower()

        claim_words = set(re.findall(r"\b\w+\b", claim_lower))
        note_words = set(re.findall(r"\b\w+\b", note_lower))

        if not claim_words:
            return 0.5

        overlap = len(claim_words & note_words)
        coverage = overlap / len(claim_words)

        direct_evidence = 0.0
        if any(word in evidence_lower for word in claim_words):
            direct_evidence = 0.3

        strength = min(1.0, coverage * 0.7 + direct_evidence)

        return strength
