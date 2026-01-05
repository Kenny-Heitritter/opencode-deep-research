#!/usr/bin/env python3
"""
Evidence data models for Deep Research

This module defines the core data structures for managing evidence gathered
during the research process, including search results, documents, text spans,
and extracted notes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Span:
    """
    Represents a text span within a document for provenance tracking.

    A span captures the exact location and content of text within a source document,
    enabling precise citation and verification of claims.
    """

    document_url: str
    start_char: int
    end_char: int
    text: str

    def __post_init__(self):
        """Validate span data"""
        if self.start_char < 0:
            raise ValueError("start_char must be non-negative")
        if self.end_char <= self.start_char:
            raise ValueError("end_char must be greater than start_char")
        if not self.document_url:
            raise ValueError("document_url cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "document_url": self.document_url,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Span":
        """Create from dictionary"""
        return cls(
            document_url=data["document_url"],
            start_char=data["start_char"],
            end_char=data["end_char"],
            text=data["text"],
        )


@dataclass
class SearchResult:
    """
    Represents a single search result from a web search.

    Contains basic metadata about a web page that was found during search,
    which can then be fetched and analyzed for evidence extraction.
    """

    url: str
    title: str
    snippet: str
    rank: int
    search_query: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate search result data"""
        if not self.url:
            raise ValueError("url cannot be empty")
        if self.rank < 1:
            raise ValueError("rank must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "rank": self.rank,
            "search_query": self.search_query,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create from dictionary"""
        return cls(
            url=data["url"],
            title=data["title"],
            snippet=data["snippet"],
            rank=data["rank"],
            search_query=data["search_query"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class Document:
    """
    Represents a fetched document with its content and metadata.

    A document is the result of fetching a URL, containing the full text content
    and metadata needed for evidence extraction and provenance tracking.
    """

    url: str
    title: str
    content: str
    content_type: str
    fetch_timestamp: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    char_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate derived fields"""
        if self.char_count == 0:
            self.char_count = len(self.content)
        if self.word_count == 0:
            self.word_count = len(self.content.split())
        if not self.url:
            raise ValueError("url cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type,
            "fetch_timestamp": self.fetch_timestamp.isoformat(),
            "word_count": self.word_count,
            "char_count": self.char_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create from dictionary"""
        return cls(
            url=data["url"],
            title=data["title"],
            content=data["content"],
            content_type=data["content_type"],
            fetch_timestamp=datetime.fromisoformat(data["fetch_timestamp"]),
            word_count=data.get("word_count", 0),
            char_count=data.get("char_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Note:
    """
    Represents an extracted note (evidence) from a document.

    A note is a piece of information extracted from one or more documents,
    with full provenance tracking through spans. Notes are the building blocks
    of research reports, each backed by verifiable sources.
    """

    content: str
    spans: List[Span]
    query: str
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate note data"""
        if not self.content:
            raise ValueError("content cannot be empty")
        if not self.spans:
            raise ValueError("note must have at least one source span")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    @property
    def source_urls(self) -> List[str]:
        """Get unique source URLs for this note"""
        return list(set(span.document_url for span in self.spans))

    @property
    def primary_source(self) -> str:
        """Get the primary (first) source URL"""
        return self.spans[0].document_url if self.spans else ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "spans": [span.to_dict() for span in self.spans],
            "query": self.query,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        """Create from dictionary"""
        return cls(
            content=data["content"],
            spans=[Span.from_dict(s) for s in data["spans"]],
            query=data["query"],
            confidence=data.get("confidence", 1.0),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )
