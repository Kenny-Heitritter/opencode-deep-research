"""Verification module for Deep Research quality assurance.

This module provides tools for:
- Support checking: Verify claims are supported by evidence
- Contradiction detection: Find conflicting information across paragraphs
- Critique generation: Generate targeted follow-up queries
- Uncertainty tracking: Track and report uncertainties and contradictions
"""

from .support_check import SupportChecker, SupportCheckResult
from .contradiction import (
    ContradictionDetector,
    Contradiction,
    ContradictionSeverity,
)
from .critique import CritiqueAgent, FollowUpQuery
from .uncertainty import (
    UncertaintyTracker,
    Uncertainty,
    UncertaintyType,
)

__all__ = [
    # Support checking
    "SupportChecker",
    "SupportCheckResult",
    # Contradiction detection
    "ContradictionDetector",
    "Contradiction",
    "ContradictionSeverity",
    # Critique
    "CritiqueAgent",
    "FollowUpQuery",
    # Uncertainty tracking
    "UncertaintyTracker",
    "Uncertainty",
    "UncertaintyType",
]
