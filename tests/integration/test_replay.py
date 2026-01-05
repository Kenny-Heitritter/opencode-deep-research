"""Replay mode verification with deterministic output."""

import pytest
from unittest.mock import AsyncMock, patch

from src.models import SearchResult, Document, Note
from src.research.mode import ResearchMode
from src.research.pipeline import ResearchPipeline


class TestReplayMode:
    """Test replay mode produces deterministic output."""

    @pytest.mark.asyncio
    async def test_replay_provides_deterministic_output(self):
        """Test replay produces near-identical output (95%+ match)."""
        mode = ResearchMode()

        mock_results = [
            SearchResult(
                url="https://example.com/1",
                title="Test Result 1",
                snippet="Test snippet",
                relevance_score=0.9,
            ),
            SearchResult(
                url="https://example.com/2",
                title="Test Result 2",
                snippet="Another snippet",
                relevance_score=0.8,
            ),
        ]

        mock_docs = [
            Document(
                url="https://example.com/1",
                title="Document 1",
                content="Content from first document",
            ),
            Document(
                url="https://example.com/2",
                title="Document 2",
                content="Content from second document",
            ),
        ]

        mock_notes = [
            Note(
                extract_query="test query",
                content="First important finding",
                source_url="https://example.com/1",
            ),
            Note(
                extract_query="test query",
                content="Second important finding",
                source_url="https://example.com/2",
            ),
        ]

        with (
            patch.object(ResearchPipeline, "run", new_callable=AsyncMock) as mock_run,
        ):
            from src.models import ResearchRun

            original_run = ResearchRun(
                run_id="test-run-123",
                plan="Test plan",
                effort=3,
                status="completed",
                query="test query",
                search_results=mock_results,
                documents=mock_docs,
                notes=mock_notes,
                errors=[],
            )

            mock_run.return_value = original_run

            original = await mode.run("Test plan", 3, "test query")
            replayed = await mode.replay(original.run_id)

            assert replayed.status == "replayed"
            assert replayed.plan == original.plan
            assert replayed.effort == original.effort
            assert replayed.query == original.query

            assert len(replayed.search_results) == len(original.search_results)
            assert len(replayed.documents) == len(original.documents)
            assert len(replayed.notes) == len(original.notes)

            for i, (orig_note, replay_note) in enumerate(
                zip(original.notes, replayed.notes)
            ):
                assert replay_note.content == orig_note.content, (
                    f"Note {i} content mismatch"
                )
                assert replay_note.source_url == orig_note.source_url, (
                    f"Note {i} source mismatch"
                )

            original_content = "".join(n.content for n in original.notes)
            replay_content = "".join(n.content for n in replayed.notes)

            similarity = self._calculate_similarity(original_content, replay_content)
            assert similarity >= 0.95, (
                f"Replay similarity {similarity:.2%} below 95% threshold"
            )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 1.0

        return intersection / union

    @pytest.mark.asyncio
    async def test_replay_nonexistent_run_raises_error(self):
        """Test replay of non-existent run raises error."""
        mode = ResearchMode()

        with pytest.raises(ValueError, match="Run .* not found in storage"):
            await mode.replay("nonexistent-run-id")
