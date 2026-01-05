"""Effort configuration knob scaling competition parameters."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EffortConfig:
    """Configuration parameters for a given effort level."""

    level: int
    num_outline_candidates: int
    outline_beam_width: int
    num_query_candidates_per_section: int
    query_beam_width: int
    num_draft_candidates: int
    draft_beam_width: int
    search_depth: int
    max_documents: int


def effort_map(effort_level: int) -> EffortConfig:
    """Map effort level to competition parameters.

    Args:
        effort_level: Research effort level (1-5)

    Returns:
        EffortConfig with all competition parameters

    Raises:
        ValueError: If effort_level not in 1-5
    """
    if not 1 <= effort_level <= 5:
        raise ValueError(f"Effort level must be 1-5, got {effort_level}")

    level = max(1, min(5, effort_level))

    if level == 1:
        config = EffortConfig(
            level=level,
            num_outline_candidates=3,
            outline_beam_width=1,
            num_query_candidates_per_section=2,
            query_beam_width=1,
            num_draft_candidates=2,
            draft_beam_width=1,
            search_depth=8,
            max_documents=3,
        )
    elif level == 2:
        config = EffortConfig(
            level=level,
            num_outline_candidates=5,
            outline_beam_width=2,
            num_query_candidates_per_section=3,
            query_beam_width=2,
            num_draft_candidates=3,
            draft_beam_width=1,
            search_depth=11,
            max_documents=4,
        )
    elif level == 3:
        config = EffortConfig(
            level=level,
            num_outline_candidates=7,
            outline_beam_width=3,
            num_query_candidates_per_section=4,
            query_beam_width=2,
            num_draft_candidates=4,
            draft_beam_width=2,
            search_depth=14,
            max_documents=5,
        )
    elif level == 4:
        config = EffortConfig(
            level=level,
            num_outline_candidates=10,
            outline_beam_width=3,
            num_query_candidates_per_section=5,
            query_beam_width=3,
            num_draft_candidates=5,
            draft_beam_width=2,
            search_depth=17,
            max_documents=6,
        )
    else:
        config = EffortConfig(
            level=level,
            num_outline_candidates=15,
            outline_beam_width=5,
            num_query_candidates_per_section=6,
            query_beam_width=3,
            num_draft_candidates=6,
            draft_beam_width=3,
            search_depth=20,
            max_documents=7,
        )

    logger.info(f"Effort level {level} mapped to {config}")
    return config


def calculate_candidates_from_effort(effort_level: int, base_count: int = 5) -> int:
    """Calculate candidate count scaled by effort level.

    Args:
        effort_level: Effort level (1-5)
        base_count: Base number of candidates

    Returns:
        Scaled candidate count
    """
    multiplier = 1 + (effort_level - 1) * 0.5
    return int(base_count * multiplier)


def calculate_beam_width_from_effort(effort_level: int, base_width: int = 1) -> int:
    """Calculate beam width scaled by effort level.

    Args:
        effort_level: Effort level (1-5)
        base_width: Base beam width

    Returns:
        Scaled beam width
    """
    extra_width = (effort_level - 1) // 2
    return base_width + extra_width
