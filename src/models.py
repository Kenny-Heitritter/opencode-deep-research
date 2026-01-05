"""Type definitions and models for Deep Research pipeline."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class SearchResult:
    """Result from web search."""

    url: str
    title: str
    snippet: str
    relevance_score: Optional[float] = None


@dataclass
class Document:
    """Fetched document from URL."""

    url: str
    title: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Note:
    """Extracted note from document."""

    extract_query: str
    content: str
    source_url: str
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    relevance_score: Optional[float] = None


@dataclass
class ResearchRun:
    """Complete research run results."""

    run_id: str
    plan: str
    effort: int
    status: str
    query: str
    search_results: list[SearchResult]
    documents: list[Document]
    notes: list[Note]
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    errors: list[str] = field(default_factory=list)


@dataclass
class DraftSection:
    """Section in the research draft."""

    title: str
    content: str


@dataclass
class DraftAST:
    """Abstract syntax tree for research draft."""

    query: str
    plan: str
    sections: list[DraftSection]
    references: list[tuple[int, str, str]] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
