"""Outline generation with competition and beam search."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .research_world import WorldState

logger = logging.getLogger(__name__)


@dataclass
class Outline:
    """Research outline with sections."""

    title: str
    sections: list[str]
    rationale: str
    score: float = 0.0


@dataclass
class OutlineCompetition:
    """Competition for generating and selecting the best outline."""

    generator: Any = None
    scoring_model: Optional[Any] = None

    async def generate_candidates(self, state: WorldState, count: int) -> list[Outline]:
        """Generate multiple outline candidates.

        Args:
            state: Current WorldState
            count: Number of candidates to generate

        Returns:
            List of outline candidates
        """
        logger.info(
            f"Generating {count} outline candidates for plan: {state.plan[:50]}..."
        )

        candidates = []
        for i in range(count):
            outline = self._generate_outline_variant(state, i)
            candidates.append(outline)

        logger.info(f"Generated {len(candidates)} outline candidates")
        return candidates

    def _generate_outline_variant(
        self, state: WorldState, variant_index: int
    ) -> Outline:
        """Generate a single outline variant.

        Args:
            state: Current WorldState
            variant_index: Index of this variant for diversity

        Returns:
            Generated outline
        """
        base_sections = [
            "Introduction",
            "Background",
            "Methodology",
            "Key Findings",
            "Analysis",
            "Conclusions",
        ]

        if variant_index % 2 == 1:
            sections = [
                "Overview",
                "Historical Context",
                "Current State",
                "Critical Analysis",
                "Future Directions",
                "Summary",
            ]
        elif variant_index % 3 == 2:
            sections = [
                "Executive Summary",
                "Problem Statement",
                "Literature Review",
                "Discussion",
                "Implications",
                "Recommendations",
                "References",
            ]
        else:
            sections = base_sections

        rationale = f"Variant {variant_index} focuses on structured analysis"

        return Outline(
            title=f"{state.plan[:50]}...",
            sections=sections,
            rationale=rationale,
            score=0.0,
        )

    def score(self, candidates: list[Outline], state: WorldState) -> list[float]:
        """Score outline candidates based on quality metrics.

        Args:
            candidates: List of outline candidates
            state: Current WorldState

        Returns:
            List of scores for each candidate
        """
        logger.info(f"Scoring {len(candidates)} outline candidates")

        scores = []
        for i, candidate in enumerate(candidates):
            score = self._calculate_outline_score(candidate, state, i)
            scores.append(score)
            logger.debug(f"Outline {i} score: {score:.3f}")

        return scores

    def _calculate_outline_score(
        self, outline: Outline, state: WorldState, index: int
    ) -> float:
        """Calculate score for a single outline.

        Args:
            outline: Outline to score
            state: Current WorldState
            index: Index of candidate (for diversity)

        Returns:
            Score value
        """
        diversity_factor = (index + 1) / 10.0
        completeness_score = len(outline.sections) / 10.0
        structure_score = 0.5 + (len(outline.sections) % 3) * 0.1

        total_score = (
            completeness_score * 0.6 + structure_score * 0.4 - diversity_factor * 0.1
        )
        return max(0.0, min(1.0, total_score))

    def beam_select(
        self, candidates: list[Outline], scores: list[float], width: int
    ) -> list[Outline]:
        """Select top candidates using beam search.

        Args:
            candidates: List of outline candidates
            scores: Corresponding scores for each candidate
            width: Beam width (number to select)

        Returns:
            List of selected candidates sorted by score
        """
        logger.info(f"Beam selecting top {width} from {len(candidates)} candidates")

        indexed_scores = list(zip(candidates, scores, range(len(candidates))))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        selected = [item[0] for item in indexed_scores[:width]]
        logger.info(
            f"Selected {len(selected)} candidates with scores {[f'{s:.3f}' for s in scores[:width]]}"
        )

        return selected

    async def run_competition(
        self, state: WorldState, num_candidates: int, beam_width: int
    ) -> Outline:
        """Run full outline competition.

        Args:
            state: Current WorldState
            num_candidates: Number of candidates to generate
            beam_width: Beam width for selection

        Returns:
            Best outline from competition
        """
        candidates = await self.generate_candidates(state, num_candidates)
        scores = self.score(candidates, state)
        selected = self.beam_select(candidates, scores, beam_width)

        best = selected[0]
        logger.info(
            f"Competition complete: best outline score={scores[candidates.index(best)]:.3f}"
        )
        return best
