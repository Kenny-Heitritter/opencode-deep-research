"""Critique agent for generating follow-up queries on weak claims."""

import logging

from src.models import Claim, Query

logger = logging.getLogger(__name__)


class CritiqueAgent:
    """Generate targeted follow-up queries for weak claims."""

    def generate_followup(self, weak_claims: list[Claim]) -> list[Query]:
        """Generate follow-up queries on weak claims.

        Args:
            weak_claims: List of claims with low strength scores

        Returns:
            List of follow-up queries
        """
        queries = []

        for claim in weak_claims:
            if claim.strength_score < 0.3:
                queries.append(
                    Query(
                        text=f"Find evidence to support or refute: {claim.text}",
                        reason=f"Claim has low strength score ({claim.strength_score:.2f})",
                        priority="high",
                    )
                )
            elif claim.strength_score < 0.5:
                queries.append(
                    Query(
                        text=f"Find additional evidence for: {claim.text}",
                        reason=f"Claim has moderate strength score ({claim.strength_score:.2f})",
                        priority="medium",
                    )
                )

        logger.info(f"Generated {len(queries)} follow-up queries")
        return queries
