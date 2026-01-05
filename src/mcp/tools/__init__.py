#!/usr/bin/env python3
"""
Evidence gathering tools for Deep Research

This package provides the core tools for gathering evidence:
- search: Web search functionality
- fetch: Document fetching and processing
- extract: LLM-based evidence extraction with provenance tracking
"""

from .search import search, SearchEngine
from .fetch import fetch, DocumentFetcher
from .extract import extract, EvidenceExtractor

__all__ = [
    "search",
    "SearchEngine",
    "fetch",
    "DocumentFetcher",
    "extract",
    "EvidenceExtractor",
]
