"""Computation competition framework for Deep Research."""

from .research_world import ResearchWorld, WorldState
from .outline import OutlineCompetition
from .query import QueryCompetition
from .draft import DraftCompetition
from .effort import effort_map

__all__ = [
    "ResearchWorld",
    "WorldState",
    "OutlineCompetition",
    "QueryCompetition",
    "DraftCompetition",
    "effort_map",
]
