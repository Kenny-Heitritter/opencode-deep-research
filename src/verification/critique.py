"""Critique agent for generating targeted follow-up queries.

This module provides functionality to analyze contradictions, unsupported claims,
and uncertainties, then generate targeted follow-up queries to resolve them.
"""

from typing import List, Optional, Callable
from dataclasses import dataclass

from .contradiction import Contradiction
from .support_check import SupportCheckResult


@dataclass
class FollowUpQuery:
    """A targeted follow-up query to resolve issues."""

    query: str
    reason: str  # Why this query is needed
    priority: int  # 1-5, with 5 being highest priority
    related_paragraph_ids: List[str]  # Paragraphs this query relates to


class CritiqueAgent:
    """Generates targeted follow-up queries to resolve issues in research.

    This agent analyzes contradictions, unsupported claims, and uncertainties
    to generate specific queries that will help resolve these issues.
    """

    def __init__(
        self,
        llm_generator: Optional[Callable[[str, List[str]], List[str]]] = None,
    ):
        """Initialize critique agent.

        Args:
            llm_generator: Optional LLM-based query generator that takes
                          (issue_description, context_paragraphs) and returns
                          list of query strings.
        """
        self.llm_generator = llm_generator

    def generate_followup_queries(
        self, contradictions: List[Contradiction]
    ) -> List[str]:
        """Generate follow-up queries to resolve contradictions.

        Args:
            contradictions: List of detected contradictions

        Returns:
            List of follow-up query strings
        """
        followup_queries_with_details = self.generate_detailed_followup_queries(
            contradictions=contradictions
        )
        return [q.query for q in followup_queries_with_details]

    def generate_detailed_followup_queries(
        self,
        contradictions: Optional[List[Contradiction]] = None,
        unsupported: Optional[List[SupportCheckResult]] = None,
    ) -> List[FollowUpQuery]:
        """Generate detailed follow-up queries for multiple issue types.

        Args:
            contradictions: Optional list of contradictions to resolve
            unsupported: Optional list of unsupported paragraphs

        Returns:
            List of FollowUpQuery objects with priorities
        """
        queries = []

        # Generate queries for contradictions
        if contradictions:
            for contradiction in contradictions:
                query = self._generate_contradiction_query(contradiction)
                if query:
                    queries.append(query)

        # Generate queries for unsupported claims
        if unsupported:
            for result in unsupported:
                query = self._generate_support_query(result)
                if query:
                    queries.append(query)

        # Sort by priority (highest first)
        queries.sort(key=lambda q: q.priority, reverse=True)

        return queries

    def _generate_contradiction_query(
        self, contradiction: Contradiction
    ) -> Optional[FollowUpQuery]:
        """Generate a query to resolve a specific contradiction.

        Args:
            contradiction: The contradiction to resolve

        Returns:
            FollowUpQuery or None
        """
        # Use LLM generator if available
        if self.llm_generator:
            context_paragraphs = [
                contradiction.paragraph1_content,
                contradiction.paragraph2_content,
            ]
            queries = self.llm_generator(contradiction.reason, context_paragraphs)
            if queries:
                return FollowUpQuery(
                    query=queries[0],
                    reason=f"Resolve contradiction: {contradiction.reason}",
                    priority=self._contradiction_priority(contradiction),
                    related_paragraph_ids=[
                        contradiction.paragraph1_id,
                        contradiction.paragraph2_id,
                    ],
                )

        # Fallback: Template-based query generation
        query_text = self._template_contradiction_query(contradiction)

        return FollowUpQuery(
            query=query_text,
            reason=f"Resolve contradiction: {contradiction.reason}",
            priority=self._contradiction_priority(contradiction),
            related_paragraph_ids=[
                contradiction.paragraph1_id,
                contradiction.paragraph2_id,
            ],
        )

    def _template_contradiction_query(self, contradiction: Contradiction) -> str:
        """Generate a template-based query for a contradiction.

        Args:
            contradiction: The contradiction to resolve

        Returns:
            Query string
        """
        # Extract key terms from both paragraphs
        para1_terms = self._extract_key_terms(contradiction.paragraph1_content)
        para2_terms = self._extract_key_terms(contradiction.paragraph2_content)

        # Find common topic
        common_terms = set(para1_terms) & set(para2_terms)

        if common_terms:
            topic = ", ".join(list(common_terms)[:3])
            return (
                f"What is the accurate information regarding {topic}? "
                f"There appear to be conflicting claims."
            )
        else:
            # Use section titles if available
            if contradiction.section1_title and contradiction.section2_title:
                return (
                    f"Clarify the relationship between {contradiction.section1_title} "
                    f"and {contradiction.section2_title}. Sources show conflicting information."
                )
            else:
                return "Clarify conflicting information found in research sources."

    def _generate_support_query(
        self, result: SupportCheckResult
    ) -> Optional[FollowUpQuery]:
        """Generate a query to find support for unsupported paragraph.

        Args:
            result: SupportCheckResult showing unsupported paragraph

        Returns:
            FollowUpQuery or None
        """
        # Determine priority based on issues
        priority = 4  # High priority for unsupported claims

        # Generate query based on issues
        if "no supporting notes" in str(result.issues).lower():
            reason = "Paragraph has no supporting evidence"
            query = "Find sources to support: " + result.paragraph_id[:100]
        elif "low confidence" in str(result.issues).lower():
            reason = "Evidence has low confidence"
            query = "Find additional high-quality sources to verify claims"
        else:
            reason = "Paragraph claims not adequately supported"
            query = "Find supporting evidence for claims made"

        return FollowUpQuery(
            query=query,
            reason=reason,
            priority=priority,
            related_paragraph_ids=[result.paragraph_id],
        )

    def _extract_key_terms(self, text: str, max_terms: int = 5) -> List[str]:
        """Extract key terms from text.

        Args:
            text: Text to extract from
            max_terms: Maximum number of terms to extract

        Returns:
            List of key terms
        """
        # Simple extraction: nouns and significant words
        # Filter out common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "this",
            "that",
            "these",
            "those",
        }

        words = text.lower().split()
        # Filter and deduplicate
        key_terms = []
        seen = set()

        for word in words:
            # Clean word
            word = word.strip(".,!?;:()")
            # Keep if significant (length > 3, not stop word, not seen)
            if len(word) > 3 and word not in stop_words and word not in seen:
                key_terms.append(word)
                seen.add(word)

            if len(key_terms) >= max_terms:
                break

        return key_terms

    def _contradiction_priority(self, contradiction: Contradiction) -> int:
        """Determine priority for contradiction query.

        Args:
            contradiction: The contradiction

        Returns:
            Priority from 1-5
        """
        from .contradiction import ContradictionSeverity

        if contradiction.severity == ContradictionSeverity.HIGH:
            return 5
        elif contradiction.severity == ContradictionSeverity.MEDIUM:
            return 4
        else:
            return 3

    def merge_similar_queries(
        self, queries: List[FollowUpQuery], similarity_threshold: float = 0.7
    ) -> List[FollowUpQuery]:
        """Merge similar queries to avoid redundancy.

        Args:
            queries: List of queries to merge
            similarity_threshold: Threshold for considering queries similar

        Returns:
            Merged list of queries
        """
        if not queries:
            return []

        merged = []
        used = set()

        for i, query1 in enumerate(queries):
            if i in used:
                continue

            similar_queries = [query1]

            for j, query2 in enumerate(queries[i + 1 :], start=i + 1):
                if j in used:
                    continue

                # Check similarity based on keyword overlap
                words1 = set(query1.query.lower().split())
                words2 = set(query2.query.lower().split())

                overlap = len(words1 & words2)
                total = len(words1 | words2)

                if total > 0 and overlap / total >= similarity_threshold:
                    similar_queries.append(query2)
                    used.add(j)

            # Merge similar queries
            if len(similar_queries) == 1:
                merged.append(query1)
            else:
                # Combine related paragraphs and use highest priority
                all_para_ids = []
                max_priority = 0
                for sq in similar_queries:
                    all_para_ids.extend(sq.related_paragraph_ids)
                    max_priority = max(max_priority, sq.priority)

                merged.append(
                    FollowUpQuery(
                        query=query1.query,  # Use first query text
                        reason=f"Merged query addressing {len(similar_queries)} related issues",
                        priority=max_priority,
                        related_paragraph_ids=list(set(all_para_ids)),
                    )
                )

        return merged
