"""Query competition for research sections."""

import logging
from dataclasses import dataclass, field
from typing import Any

from .research_world import WorldState

logger = logging.getLogger(__name__)


@dataclass
class QueryHypothesis:
    """Research query hypothesis."""

    question: str
    search_query: str
    rationale: str
    expected_insights: list[str]
    source_hints: list[str]
    score: float = 0.0


@dataclass
class QueryCompetition:
    """Competition for generating and scoring research queries."""

    web_tools: Any = None

    async def generate_candidates(
        self, state: WorldState, section: str, count: int
    ) -> list[QueryHypothesis]:
        """Generate multiple query hypotheses for a section.

        Args:
            state: Current WorldState
            section: Section title/subject
            count: Number of query candidates to generate

        Returns:
            List of query hypothesis candidates
        """
        logger.info(f"Generating {count} query candidates for section: {section}")

        candidates = []
        for i in range(count):
            hypothesis = self._generate_query_variant(state, section, i)
            candidates.append(hypothesis)

        logger.info(f"Generated {len(candidates)} query candidates for {section}")
        return candidates

    def _generate_query_variant(
        self, state: WorldState, section: str, variant_index: int
    ) -> QueryHypothesis:
        """Generate a single query hypothesis variant.

        Args:
            state: Current WorldState
            section: Section title
            variant_index: Index of this variant

        Returns:
            Generated query hypothesis
        """
        base_query = state.plan[:100]

        if variant_index == 0:
            question = (
                f"What are the key aspects of {section} in relation to {base_query}?"
            )
            search_query = f"{section} {base_query}"
            source_hints = ["academic sources", "expert opinions"]
        elif variant_index == 1:
            question = f"How does {section} impact {base_query}?"
            search_query = f"{section} impact effects {base_query}"
            source_hints = ["case studies", "research papers"]
        elif variant_index == 2:
            question = f"What are current trends in {section} for {base_query}?"
            search_query = f"{section} trends latest {base_query}"
            source_hints = ["recent publications", "industry reports"]
        elif variant_index == 3:
            question = f"What challenges exist in {section} regarding {base_query}?"
            search_query = f"{section} challenges problems {base_query}"
            source_hints = ["critical analysis", "expert forums"]
        else:
            question = (
                f"What future developments are expected in {section} for {base_query}?"
            )
            search_query = f"{section} future predictions {base_query} 2024 2025"
            source_hints = ["forecasts", "expert predictions"]

        expected_insights = [
            f"Key findings about {section}",
            f"Data and statistics related to {base_query}",
            f"Expert perspectives on {section}",
        ]

        return QueryHypothesis(
            question=question,
            search_query=search_query,
            rationale=f"Variant {variant_index} explores {section} from a {'comprehensive' if variant_index < 2 else 'specific'} perspective",
            expected_insights=expected_insights,
            source_hints=source_hints,
            score=0.0,
        )

    def score(
        self, candidates: list[QueryHypothesis], state: WorldState
    ) -> list[float]:
        """Score query hypotheses.

        Args:
            candidates: List of query candidates
            state: Current WorldState

        Returns:
            List of scores for each candidate
        """
        logger.info(f"Scoring {len(candidates)} query candidates")

        scores = []
        for i, candidate in enumerate(candidates):
            score = self._calculate_query_score(candidate, state, i)
            scores.append(score)
            logger.debug(f"Query {i} score: {score:.3f}")

        return scores

    def _calculate_query_score(
        self, query: QueryHypothesis, state: WorldState, index: int
    ) -> float:
        """Calculate score for a query hypothesis.

        Args:
            query: Query hypothesis to score
            state: Current WorldState
            index: Index of candidate

        Returns:
            Score value (0.0 to 1.0)
        """
        relevance_score = (
            0.8 if state.plan.lower() in query.search_query.lower() else 0.5
        )
        specificity_score = min(1.0, len(query.search_query.split()) / 10.0)
        insight_potential = min(1.0, len(query.expected_insights) / 5.0)
        variety_bonus = (index + 1) / (len(query.expected_insights) + 1) * 0.1

        total_score = (
            relevance_score * 0.4
            + specificity_score * 0.3
            + insight_potential * 0.2
            + variety_bonus * 0.1
        )
        return max(0.0, min(1.0, total_score))

    def beam_select(
        self, candidates: list[QueryHypothesis], scores: list[float], width: int
    ) -> list[QueryHypothesis]:
        """Select top queries using beam search.

        Args:
            candidates: List of query candidates
            scores: Corresponding scores
            width: Beam width

        Returns:
            List of selected candidates sorted by score
        """
        logger.info(
            f"Beam selecting top {width} from {len(candidates)} query candidates"
        )

        indexed = list(zip(candidates, scores, range(len(candidates))))
        indexed.sort(key=lambda x: x[1], reverse=True)

        selected = [item[0] for item in indexed[:width]]
        logger.info(f"Selected {len(selected)} queries with top score={scores[0]:.3f}")

        return selected

    async def execute_queries(
        self, state: WorldState, queries: list[QueryHypothesis]
    ) -> WorldState:
        """Execute selected queries and update state with results.

        Args:
            state: Current WorldState
            queries: List of selected queries to execute

        Returns:
            Updated WorldState with query results
        """
        logger.info(f"Executing {len(queries)} queries")

        if not self.web_tools:
            logger.warning("No web tools available, skipping query execution")
            return state

        from src.research.pipeline import ResearchPipeline

        pipeline = ResearchPipeline(effort=state.effort)
        query_results = {}

        try:
            async with self.web_tools:
                for query in queries:
                    logger.info(f"Executing query: {query.search_query}")
                    results = await self.web_tools.search(
                        query.search_query, num_results=5 + state.effort
                    )
                    query_results[query.search_query] = results
                    logger.info(f"Query returned {len(results)} results")

        except Exception as e:
            logger.error(f"Error executing queries: {e}")

        return state

    async def run_competition(
        self, state: WorldState, section: str, num_candidates: int, beam_width: int
    ) -> list[QueryHypothesis]:
        """Run full query competition for a section.

        Args:
            state: Current WorldState
            section: Section to research
            num_candidates: Number of query candidates
            beam_width: Beam width

        Returns:
            List of selected best queries
        """
        candidates = await self.generate_candidates(state, section, num_candidates)
        scores = self.score(candidates, state)
        selected = self.beam_select(candidates, scores, beam_width)

        logger.info(
            f"Query competition for '{section}' complete: selected {len(selected)} queries"
        )
        return selected
