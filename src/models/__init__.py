#!/usr/bin/env python3
"""
Data models for Deep Research

This package contains all data models used in the research pipeline.
"""

from .evidence import SearchResult, Document, Span, Note

__all__ = [
    "SearchResult",
    "Document",
    "Span",
    "Note",
]
