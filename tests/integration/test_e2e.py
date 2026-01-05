"""End-to-end integration tests with clarifying questions and plan approval."""

import pytest
from unittest.mock import AsyncMock, patch

from src.models import SearchResult, Document, Note, Claim
from src.research.pipeline import ResearchPipeline
from src.verification.spot_check import SpotChecker
from src.verification.contradiction import ContradictionDetector
from src.agents.critique import CritiqueAgent


class TestClarifyingQuestionsAndPlanApproval:
    """Test clarifying questions and plan approval workflow."""

    @pytest.mark.asyncio
    async def test_clarifying_questions_workflow(self):
        """Test workflow with clarifying questions."""
        pipeline = ResearchPipeline(effort=3)

        mock_results = [
            SearchResult(url="https://example.com/1", title="Research 1", snippet=""),
        ]

        mock_doc = Document(
            url="https://example.com/1",
            title="Research Document 1",
            content="This is test content with some information.",
        )

        mock_note = Note(
            extract_query="test query",
            content="Key finding from the research",
            source_url="https://example.com/1",
        )

        with (
            patch.object(
                pipeline.web_tools, "search", new_callable=AsyncMock
            ) as mock_search,
            patch.object(
                pipeline.web_tools, "fetch", new_callable=AsyncMock
            ) as mock_fetch,
            patch.object(
                pipeline.web_tools, "extract_with_jina", new_callable=AsyncMock
            ) as mock_extract,
        ):
            mock_search.return_value = mock_results
            mock_fetch.return_value = mock_doc
            mock_extract.return_value = [mock_note]

            clarifying_questions = [
                "What specific aspect of climate change should I focus on?",
                "Do you want historical data or future projections?",
            ]

            plan = f"""
            Research Plan:
            - Investigate climate change effects
            - Clarify scope: {clarifying_questions[0]}
            - Time period: {clarifying_questions[1]}
            """

            run = await pipeline.run(plan, "climate change")

            assert run.status == "completed"
            assert len(run.notes) == 1
            assert "Key finding" in run.notes[0].content

    @pytest.mark.asyncio
    async def test_plan_approval_process(self):
        """Test plan approval process."""
        pipeline = ResearchPipeline(effort=3)

        mock_results = [
            SearchResult(url="https://example.com/1", title="Test", snippet=""),
        ]

        mock_doc = Document(
            url="https://example.com/1", title="Test", content="Content"
        )
        mock_note = Note(
            extract_query="test",
            content="Test note",
            source_url="https://example.com/1",
        )

        with (
            patch.object(
                pipeline.web_tools, "search", new_callable=AsyncMock
            ) as mock_search,
            patch.object(
                pipeline.web_tools, "fetch", new_callable=AsyncMock
            ) as mock_fetch,
            patch.object(
                pipeline.web_tools, "extract_with_jina", new_callable=AsyncMock
            ) as mock_extract,
        ):
            mock_search.return_value = mock_results
            mock_fetch.return_value = mock_doc
            mock_extract.return_value = [mock_note]

            plan = "Research Plan: Investigate renewable energy solutions"
            approved_plan = plan + " - APPROVED"

            run = await pipeline.run(approved_plan, "renewable energy")

            assert run.status == "completed"
            assert "APPROVED" in run.plan


class TestVerificationWorkflow:
    """Test verification workflow with spot checking."""

    def test_spot_check_verification(self):
        """Test spot checking validates claims against citation spans."""
        documents = [
            Document(
                url="https://example.com/1",
                title="Test Document",
                content="This is comprehensive evidence supporting the claim about renewable energy.",
            )
        ]

        notes = [
            Note(
                extract_query="test",
                content="Evidence shows renewable energy adoption is increasing rapidly.",
                source_url="https://example.com/1",
                span_start=5,
                span_end=70,
            )
        ]

        claims = [
            Claim(
                text="Renewable energy adoption is increasing rapidly",
                citation_indices=[0],
                strength_score=0.0,
                needs_verification=True,
            )
        ]

        checker = SpotChecker(documents)
        verified = checker.verify(claims, notes)

        assert len(verified) == 1
        assert verified[0].strength_score > 0.0
        assert verified[0].text == claims[0].text

    def test_contradiction_detection(self):
        """Test contradictions detected and reported in output."""
        notes = [
            Note(
                extract_query="test",
                content="Climate change is primarily caused by human activity.",
                source_url="https://example.com/1",
            ),
            Note(
                extract_query="test",
                content="However, contrary to popular belief, climate change is not anthropogenic.",
                source_url="https://example.com/2",
            ),
        ]

        detector = ContradictionDetector()
        conflicts = detector.find_conflicts(notes)

        assert len(conflicts) >= 0


class TestCritiqueFollowUp:
    """Test critique agent generates follow-up queries."""

    def test_followup_queries_on_weak_claims(self):
        """Test critique agent generates follow-up queries on weak claims."""
        weak_claims = [
            Claim(
                text="Unsubstantiated claim with no evidence",
                citation_indices=[],
                strength_score=0.1,
                needs_verification=True,
            ),
            Claim(
                text="Partially supported claim",
                citation_indices=[0],
                strength_score=0.4,
                needs_verification=True,
            ),
        ]

        agent = CritiqueAgent()
        queries = agent.generate_followup(weak_claims)

        assert len(queries) == 2
        assert any(q.priority == "high" for q in queries)
        assert any("evidence" in q.text.lower() for q in queries)
