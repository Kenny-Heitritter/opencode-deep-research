#!/usr/bin/env python3
"""
Integration tests for the evidence gathering pipeline

Tests the end-to-end pipeline: search → fetch → extract
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.evidence import SearchResult, Document, Note, Span
from src.mcp.tools.search import search, SearchEngine
from src.mcp.tools.fetch import fetch, DocumentFetcher
from src.mcp.tools.extract import extract, EvidenceExtractor


class TestEvidenceModels:
    """Test evidence data models"""

    def test_span_creation(self):
        """Test creating a Span"""
        span = Span(
            document_url="https://example.com/doc",
            start_char=100,
            end_char=200,
            text="This is a test span",
        )

        assert span.document_url == "https://example.com/doc"
        assert span.start_char == 100
        assert span.end_char == 200
        assert span.text == "This is a test span"

    def test_span_validation(self):
        """Test Span validation"""
        with pytest.raises(ValueError):
            Span(
                document_url="https://example.com",
                start_char=-1,
                end_char=100,
                text="test",
            )

        with pytest.raises(ValueError):
            Span(
                document_url="https://example.com",
                start_char=100,
                end_char=50,
                text="test",
            )

    def test_search_result_creation(self):
        """Test creating a SearchResult"""
        result = SearchResult(
            url="https://example.com",
            title="Example Page",
            snippet="This is a snippet",
            rank=1,
            search_query="test query",
        )

        assert result.url == "https://example.com"
        assert result.rank == 1
        assert result.search_query == "test query"

    def test_document_creation(self):
        """Test creating a Document"""
        doc = Document(
            url="https://example.com",
            title="Test Document",
            content="This is test content with multiple words.",
            content_type="text/html",
        )

        assert doc.url == "https://example.com"
        assert doc.word_count > 0
        assert doc.char_count == len(doc.content)

    def test_note_creation(self):
        """Test creating a Note with spans"""
        span = Span(
            document_url="https://example.com",
            start_char=0,
            end_char=20,
            text="Test evidence text",
        )

        note = Note(
            content="Test evidence text",
            spans=[span],
            query="test query",
            confidence=0.9,
        )

        assert note.content == "Test evidence text"
        assert len(note.spans) == 1
        assert note.primary_source == "https://example.com"
        assert note.confidence == 0.9

    def test_note_validation(self):
        """Test Note validation"""
        with pytest.raises(ValueError):
            Note(content="", spans=[], query="test")

        span = Span(
            document_url="https://example.com",
            start_char=0,
            end_char=10,
            text="test",
        )

        with pytest.raises(ValueError):
            Note(content="test", spans=[], query="test")


class TestSearchTool:
    """Test search functionality"""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """Test that search returns results"""
        results = await search("quantum computing applications", num_results=5)

        assert len(results) > 0
        assert len(results) <= 5

        for result in results:
            assert isinstance(result, SearchResult)
            assert result.url
            assert result.title
            assert result.rank >= 1

    @pytest.mark.asyncio
    async def test_search_engine_initialization(self):
        """Test SearchEngine initialization"""
        engine = SearchEngine()
        assert engine is not None

        results = await engine.search("test query", num_results=3)
        assert isinstance(results, list)


class TestFetchTool:
    """Test document fetching"""

    @pytest.mark.asyncio
    async def test_fetch_html_document(self):
        """Test fetching an HTML document"""
        url = "https://www.example.com"

        doc = await fetch(url)

        assert isinstance(doc, Document)
        assert doc.url == url
        assert doc.title
        assert doc.content
        assert doc.content_type == "text/html"
        assert doc.word_count > 0
        assert doc.char_count > 0

    @pytest.mark.asyncio
    async def test_document_fetcher(self):
        """Test DocumentFetcher class"""
        fetcher = DocumentFetcher(timeout=30.0)

        doc = await fetcher.fetch("https://www.example.com")
        assert isinstance(doc, Document)


class TestExtractTool:
    """Test evidence extraction"""

    @pytest.mark.asyncio
    async def test_extract_notes_from_document(self):
        """Test extracting notes from a document"""
        doc = Document(
            url="https://example.com/test",
            title="Test Document",
            content="""
            Quantum computing is a revolutionary technology. It uses quantum mechanics
            to perform computations. Applications include cryptography and optimization.
            Quantum computers can solve certain problems faster than classical computers.
            This technology is still in early stages of development.
            """,
            content_type="text/html",
        )

        notes = await extract(doc, "quantum computing applications", max_notes=3)

        assert len(notes) > 0
        assert len(notes) <= 3

        for note in notes:
            assert isinstance(note, Note)
            assert note.content
            assert len(note.spans) > 0
            assert note.spans[0].document_url == doc.url
            assert note.query == "quantum computing applications"
            assert 0 <= note.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_extractor_with_mock(self):
        """Test EvidenceExtractor with mock extraction"""
        extractor = EvidenceExtractor()

        doc = Document(
            url="https://example.com",
            title="Test",
            content="Quantum computing has many applications in science and industry.",
            content_type="text/html",
        )

        notes = await extractor.extract(doc, "quantum computing", max_notes=5)
        assert isinstance(notes, list)


class TestEndToEndPipeline:
    """Test the complete search → fetch → extract pipeline"""

    @pytest.mark.asyncio
    async def test_complete_pipeline(self):
        """Test the full evidence gathering pipeline"""
        query = "quantum computing applications"

        search_results = await search(query, num_results=5)
        assert len(search_results) > 0
        print(f"✓ Search found {len(search_results)} results")

        documents = []
        for result in search_results[:3]:
            try:
                doc = await fetch(result.url)
                documents.append(doc)
                print(f"✓ Fetched: {doc.title} ({doc.word_count} words)")
            except Exception as e:
                print(f"✗ Failed to fetch {result.url}: {e}")

        assert len(documents) > 0
        print(f"✓ Successfully fetched {len(documents)} documents")

        all_notes = []
        for doc in documents:
            try:
                notes = await extract(doc, query, max_notes=5)
                all_notes.extend(notes)
                print(f"✓ Extracted {len(notes)} notes from {doc.title}")
            except Exception as e:
                print(f"✗ Failed to extract from {doc.title}: {e}")

        assert len(all_notes) >= 10
        print(f"✓ Total notes extracted: {len(all_notes)}")

        for note in all_notes:
            assert len(note.spans) > 0
            assert note.spans[0].document_url
            assert note.spans[0].start_char >= 0
            assert note.spans[0].end_char > note.spans[0].start_char
            assert note.spans[0].text

        print(f"✓ All notes have valid source spans")

        print("\nSample notes:")
        for i, note in enumerate(all_notes[:3], 1):
            print(f"\n{i}. {note.content[:100]}...")
            print(f"   Source: {note.primary_source}")
            print(f"   Confidence: {note.confidence:.2f}")
            print(f"   Span: {note.spans[0].start_char}-{note.spans[0].end_char}")


def run_tests():
    """Run all tests"""
    print("Running evidence pipeline tests...\n")
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_tests()
