"""Draft competition generating multiple section variants."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from .research_world import WorldState

logger = logging.getLogger(__name__)


@dataclass
class SectionVariant:
    """Variant of a draft section."""

    title: str
    content: str
    style: str
    references: list[str]
    insights: list[str]
    score: float = 0.0


@dataclass
class DraftVariant:
    """Complete draft variant."""

    title: str
    sections: list[SectionVariant]
    formatting: str
    tone: str
    overall_score: float = 0.0


@dataclass
class DraftCompetition:
    """Competition for generating and scoring draft variants."""

    render_engine: Any = None

    async def generate_candidates(
        self, state: WorldState, count: int
    ) -> list[DraftVariant]:
        """Generate multiple draft variants.

        Args:
            state: Current WorldState
            count: Number of draft variants to generate

        Returns:
            List of draft variant candidates
        """
        logger.info(f"Generating {count} draft variants for plan: {state.plan[:50]}...")

        candidates = []
        for i in range(count):
            draft = self._generate_draft_variant(state, i)
            candidates.append(draft)

        logger.info(f"Generated {len(candidates)} draft variants")
        return candidates

    def _generate_draft_variant(
        self, state: WorldState, variant_index: int
    ) -> DraftVariant:
        """Generate a single draft variant.

        Args:
            state: Current WorldState
            variant_index: Index of variant for diversity

        Returns:
            Generated draft variant
        """
        if variant_index % 3 == 0:
            style = "academic"
            tone = "formal"
            sections = [
                SectionVariant(
                    title="Introduction",
                    content=f"This research explores {state.plan[:100]}...",
                    style=style,
                    references=["ref1", "ref2"],
                    insights=["key insight 1"],
                )
            ]
        elif variant_index % 3 == 1:
            style = "technical"
            tone = "neutral"
            sections = [
                SectionVariant(
                    title="Technical Overview",
                    content=f"Technical aspects of {state.plan[:100]} include...",
                    style=style,
                    references=["tech_ref1"],
                    insights=["technical insight"],
                )
            ]
        else:
            style = "executive"
            tone = "concise"
            sections = [
                SectionVariant(
                    title="Executive Summary",
                    content=f"Key findings on {state.plan[:100]}...",
                    style=style,
                    references=["exec_ref1"],
                    insights=["business insight"],
                )
            ]

        return DraftVariant(
            title=f"{state.plan[:50]}... ({style})",
            sections=sections,
            formatting="markdown",
            tone=tone,
            overall_score=0.0,
        )

    def score(self, candidates: list[DraftVariant], state: WorldState) -> list[float]:
        """Score draft variants.

        Args:
            candidates: List of draft candidates
            state: Current WorldState

        Returns:
            List of scores for each draft
        """
        logger.info(f"Scoring {len(candidates)} draft variants")

        scores = []
        for i, candidate in enumerate(candidates):
            score = self._calculate_draft_score(candidate, state, i)
            scores.append(score)
            logger.debug(f"Draft {i} score: {score:.3f}")

        return scores

    def _calculate_draft_score(
        self, draft: DraftVariant, state: WorldState, index: int
    ) -> float:
        """Calculate score for a draft variant.

        Args:
            draft: Draft variant to score
            state: Current WorldState
            index: Index of candidate

        Returns:
            Score value (0.0 to 1.0)
        """
        completeness_score = min(1.0, len(draft.sections) / 5.0)
        content_score = sum(
            min(1.0, len(s.content) / 50.0) for s in draft.sections
        ) / max(1, len(draft.sections))
        reference_score = min(1.0, sum(len(s.references) for s in draft.sections) / 5.0)
        insight_score = min(1.0, sum(len(s.insights) for s in draft.sections) / 5.0)
        diversity_bonus = (index + 1) / (len(draft.sections) + 1) * 0.05

        total_score = (
            completeness_score * 0.2
            + content_score * 0.3
            + reference_score * 0.25
            + insight_score * 0.2
            + diversity_bonus * 0.05
        )
        return max(0.0, min(1.0, total_score))

    def beam_select(
        self, candidates: list[DraftVariant], scores: list[float], width: int
    ) -> list[DraftVariant]:
        """Select top drafts using beam search.

        Args:
            candidates: List of draft candidates
            scores: Corresponding scores
            width: Beam width

        Returns:
            List of selected drafts sorted by score
        """
        logger.info(f"Beam selecting top {width} from {len(candidates)} draft variants")

        indexed = list(zip(candidates, scores, range(len(candidates))))
        indexed.sort(key=lambda x: x[1], reverse=True)

        selected = [item[0] for item in indexed[:width]]
        logger.info(f"Selected {len(selected)} drafts with top score={scores[0]:.3f}")

        return selected

    async def run_competition(
        self, state: WorldState, num_candidates: int, beam_width: int
    ) -> DraftVariant:
        """Run full draft competition.

        Args:
            state: Current WorldState
            num_candidates: Number of candidates
            beam_width: Beam width

        Returns:
            Best draft from competition
        """
        candidates = await self.generate_candidates(state, num_candidates)
        scores = self.score(candidates, state)
        selected = self.beam_select(candidates, scores, beam_width)

        best = selected[0]
        logger.info(
            f"Draft competition complete: best variant score={scores[candidates.index(best)]:.3f}"
        )
        return best
