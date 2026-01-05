"""Integration tests for end-to-end pipeline execution."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.models import SearchResult, Document, Note
from src.research.pipeline import ResearchPipeline
from src.render.report import ReportRenderer


class TestResearchPipeline:
    """Test ResearchPipeline execution."""

    @pytest.mark.asyncio
    async def test_search_phase(self):
        """Test search phase of pipeline."""
        pipeline = ResearchPipeline(effort=3)

        mock_results = [
            SearchResult(
                url="https://example.com/1",
                title="Result 1",
                snippet="Snippet 1",
            ),
            SearchResult(
                url="https://example.com/2",
                title="Result 2",
                snippet="Snippet 2",
            ),
        ]

        with patch.object(
            pipeline.web_tools, "search", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = mock_results

            run = await pipeline._search_phase(
                type("obj", (object,), {"errors": []})(), "test query"
            )

            assert len(run) == 2
            assert run[0].url == "https://example.com/1"
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_phase(self):
        """Test fetch phase of pipeline."""
        pipeline = ResearchPipeline(effort=3)

        mock_run = MagicMock()
        mock_run.search_results = [
            SearchResult(url="https://example.com/1", title="Test", snippet="Test"),
        ]
        mock_run.errors = []

        mock_doc = Document(
            url="https://example.com/1",
            title="Test Document",
            content="Test content",
        )

        with patch.object(
            pipeline.web_tools, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_doc

            docs = await pipeline._fetch_phase(mock_run)

            assert len(docs) == 1
            assert docs[0].url == "https://example.com/1"
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_phase(self):
        """Test extraction phase of pipeline."""
        pipeline = ResearchPipeline(effort=3)

        mock_run = MagicMock()
        mock_run.documents = [
            Document(url="https://example.com/1", title="Test", content="Content"),
        ]
        mock_run.errors = []

        mock_note = Note(
            extract_query="test query",
            content="Extracted content",
            source_url="https://example.com/1",
        )

        with patch.object(
            pipeline.web_tools, "extract_with_jina", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = [mock_note]

            notes = await pipeline._extract_phase(mock_run, "test query")

            assert len(notes) == 1
            assert notes[0].source_url == "https://example.com/1"
            mock_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_pipeline_run(self):
        """Test end-to-end pipeline execution."""
        pipeline = ResearchPipeline(effort=2)

        mock_results = [
            SearchResult(url="https://example.com/1", title="Test", snippet=""),
        ]

        mock_doc = Document(
            url="https://example.com/1",
            title="Test Document",
            content="Test content",
        )

        mock_note = Note(
            extract_query="test query",
            content="Extracted content",
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

            run = await pipeline.run("Test plan", "test query")

            assert run.status == "completed"
            assert len(run.search_results) == 1
            assert len(run.documents) == 1
            assert len(run.notes) == 1


class TestReportRenderer:
    """Test ReportRenderer functionality."""

    def test_render_basic_draft(self):
        """Test rendering basic draft."""
        from src.models import DraftAST, DraftSection

        renderer = ReportRenderer()

        draft = DraftAST(
            query="test query",
            plan="test plan",
            sections=[
                DraftSection(title="Introduction", content="Test content"),
            ],
            references=[(1, "https://example.com", "Example")],
            contradictions=[],
            uncertainties=[],
        )

        report = renderer.render(draft)

        assert "# Research Report: test query" in report
        assert "**Plan:** test plan" in report
        assert "## Introduction" in report
        assert "Test content" in report
        assert "## References" in report
        assert "[^1] Example" in report

    def test_render_with_contradictions(self):
        """Test rendering with contradictions."""
        from src.models import DraftAST, DraftSection

        renderer = ReportRenderer()

        draft = DraftAST(
            query="test",
            plan="test",
            sections=[],
            references=[],
            contradictions=["Contradiction 1", "Contradiction 2"],
            uncertainties=[],
        )

        report = renderer.render(draft)

        assert "## Contradictions" in report
        assert "1. Contradiction 1" in report
        assert "2. Contradiction 2" in report

    def test_render_with_uncertainties(self):
        """Test rendering with uncertainties."""
        from src.models import DraftAST, DraftSection

        renderer = ReportRenderer()

        draft = DraftAST(
            query="test",
            plan="test",
            sections=[],
            references=[],
            contradictions=[],
            uncertainties=["Uncertainty 1", "Uncertainty 2"],
        )

        report = renderer.render(draft)

        assert "## Uncertainties" in report
        assert "1. Uncertainty 1" in report
        assert "2. Uncertainty 2" in report

    def test_render_from_run(self):
        """Test rendering report directly from ResearchRun."""
        from datetime import datetime

        renderer = ReportRenderer()

        run = type(
            "obj",
            (object,),
            {
                "query": "test query",
                "plan": "test plan",
                "effort": 3,
                "search_results": [
                    SearchResult(url="https://example.com", title="Test", snippet=""),
                ],
                "documents": [
                    Document(
                        url="https://example.com", title="Test", content="Content"
                    ),
                ],
                "notes": [
                    Note(
                        extract_query="test",
                        content="Note content",
                        source_url="https://example.com",
                    ),
                ],
            },
        )()

        report = renderer.render_from_run(run)

        assert "# Research Report: test query" in report
        assert "## References" in report
        assert "Note content" in report


class TestIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_pipeline_to_renderer_integration(self):
        """Test complete pipeline and renderer integration."""
        pipeline = ResearchPipeline(effort=1)
        renderer = ReportRenderer()

        mock_results = [
            SearchResult(url="https://example.com", title="Test", snippet=""),
        ]

        mock_doc = Document(
            url="https://example.com",
            title="Test Document",
            content="Test content",
        )

        mock_note = Note(
            extract_query="test query",
            content="Extracted note",
            source_url="https://example.com",
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

            run = await pipeline.run("Test plan", "test query")
            report = renderer.render_from_run(run)

            assert run.status == "completed"
            assert "# Research Report: test query" in report
            assert "Extracted note" in report
            assert "## References" in report
