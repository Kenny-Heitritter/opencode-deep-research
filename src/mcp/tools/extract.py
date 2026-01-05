#!/usr/bin/env python3
"""
Evidence extraction implementation using LLM

This module provides functionality to extract relevant notes and evidence from
documents using LLM-based analysis with full provenance tracking.
"""

import os
import logging
from typing import List, Optional
import json
import re

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from models.evidence import Document, Note, Span

logger = logging.getLogger(__name__)


class EvidenceExtractor:
    """Extracts evidence from documents using LLM analysis"""

    def __init__(self, opencode_caller=None):
        """
        Initialize the evidence extractor.

        Args:
            opencode_caller: Function to call OpenCode LLM (from MCPServer.call_opencode)
        """
        self.opencode_caller = opencode_caller

    async def extract(
        self, document: Document, query: str, max_notes: int = 10
    ) -> List[Note]:
        """
        Extract relevant notes from a document based on a query.

        Args:
            document: Document to extract from
            query: Research query to guide extraction
            max_notes: Maximum number of notes to extract (default: 10)

        Returns:
            List of Note objects with span provenance

        Raises:
            Exception: If extraction fails
        """
        logger.info(f"Extracting evidence from {document.url} for query: {query}")

        if not self.opencode_caller:
            logger.warning("No OpenCode caller provided, using mock extraction")
            return await self._mock_extract(document, query, max_notes)

        try:
            extraction_prompt = self._build_extraction_prompt(
                document, query, max_notes
            )

            response = await self.opencode_caller(extraction_prompt)

            notes = self._parse_extraction_response(response, document, query)

            logger.info(f"Extracted {len(notes)} notes from {document.url}")
            return notes

        except Exception as e:
            logger.error(f"Failed to extract evidence: {e}")
            raise Exception(f"Evidence extraction failed: {e}")

    def _build_extraction_prompt(
        self, document: Document, query: str, max_notes: int
    ) -> str:
        """Build the prompt for LLM-based extraction"""

        content_preview = document.content[:15000]

        prompt = f"""You are an expert research assistant. Extract relevant evidence from the following document to answer the research query.

Research Query: {query}

Document Title: {document.title}
Document URL: {document.url}
Document Content:
{content_preview}

Instructions:
1. Extract {max_notes} key pieces of evidence that are most relevant to the research query
2. For each piece of evidence, provide:
   - The exact quote from the document (verbatim text)
   - A brief explanation of why it's relevant
   - The approximate character position where it appears in the content

Output Format (JSON):
{{
  "notes": [
    {{
      "quote": "exact text from document",
      "relevance": "why this is relevant to the query",
      "start_char": approximate_character_position,
      "confidence": 0.0-1.0
    }}
  ]
}}

Extract the most relevant, factual information. Focus on specific claims, data, and insights.
"""
        return prompt

    def _parse_extraction_response(
        self, response: str, document: Document, query: str
    ) -> List[Note]:
        """Parse the LLM response and create Note objects with spans"""

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            notes = []
            for item in data.get("notes", []):
                quote = item.get("quote", "")
                if not quote:
                    continue

                start_char = item.get("start_char", 0)

                actual_start = document.content.find(quote)
                if actual_start >= 0:
                    start_char = actual_start
                else:
                    partial_quote = quote[:100]
                    partial_start = document.content.find(partial_quote)
                    if partial_start >= 0:
                        start_char = partial_start

                end_char = start_char + len(quote)

                span = Span(
                    document_url=document.url,
                    start_char=start_char,
                    end_char=end_char,
                    text=quote,
                )

                relevance = item.get("relevance", "")
                confidence = item.get("confidence", 0.8)

                note = Note(
                    content=quote,
                    spans=[span],
                    query=query,
                    confidence=confidence,
                    metadata={
                        "relevance": relevance,
                        "document_title": document.title,
                    },
                )
                notes.append(note)

            return notes

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse extraction response: {e}")
            return []

    async def _mock_extract(
        self, document: Document, query: str, max_notes: int
    ) -> List[Note]:
        """
        Mock extraction for testing without LLM.

        This extracts sentences from the document as notes with proper span tracking.
        """
        sentences = self._split_into_sentences(document.content)

        query_terms = set(query.lower().split())

        scored_sentences = []
        for sentence, start_char in sentences:
            sentence_lower = sentence.lower()
            score = sum(1 for term in query_terms if term in sentence_lower)
            if score > 0 and len(sentence) > 20:
                scored_sentences.append((score, sentence, start_char))

        scored_sentences.sort(reverse=True, key=lambda x: x[0])

        notes = []
        for score, sentence, start_char in scored_sentences[:max_notes]:
            end_char = start_char + len(sentence)

            span = Span(
                document_url=document.url,
                start_char=start_char,
                end_char=end_char,
                text=sentence,
            )

            note = Note(
                content=sentence,
                spans=[span],
                query=query,
                confidence=min(score / len(query_terms), 1.0),
                metadata={
                    "extraction_method": "mock",
                    "document_title": document.title,
                },
            )
            notes.append(note)

        logger.info(f"Mock extracted {len(notes)} notes")
        return notes

    def _split_into_sentences(self, text: str) -> List[tuple[str, int]]:
        """
        Split text into sentences with character positions.

        Returns:
            List of (sentence, start_char) tuples
        """
        sentence_pattern = r"(?<=[.!?])\s+"

        sentences = []
        current_pos = 0

        for match in re.finditer(sentence_pattern, text):
            sentence = text[current_pos : match.start()].strip()
            if sentence:
                sentences.append((sentence, current_pos))
            current_pos = match.end()

        if current_pos < len(text):
            sentence = text[current_pos:].strip()
            if sentence:
                sentences.append((sentence, current_pos))

        return sentences


async def extract(
    document: Document, query: str, max_notes: int = 10, opencode_caller=None
) -> List[Note]:
    """
    Convenience function to extract evidence from a document.

    Args:
        document: Document to extract from
        query: Research query
        max_notes: Maximum number of notes to extract
        opencode_caller: Optional OpenCode LLM caller function

    Returns:
        List of Note objects
    """
    extractor = EvidenceExtractor(opencode_caller)
    return await extractor.extract(document, query, max_notes)


async def test_extract():
    """Test the extraction functionality"""
    logging.basicConfig(level=logging.INFO)

    from fetch import fetch

    url = "https://en.wikipedia.org/wiki/Quantum_computing"
    query = "quantum computing applications"

    try:
        doc = await fetch(url)
        print(f"Fetched document: {doc.title} ({doc.word_count} words)")

        notes = await extract(doc, query, max_notes=5)

        print(f"\nExtracted {len(notes)} notes:\n")
        for i, note in enumerate(notes, 1):
            print(f"{i}. {note.content[:100]}...")
            print(f"   Source: {note.primary_source}")
            print(f"   Confidence: {note.confidence:.2f}")
            print(f"   Span: chars {note.spans[0].start_char}-{note.spans[0].end_char}")
            print()

    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_extract())
