#!/usr/bin/env python3
"""Data models for Deep Research system.

This package contains all data models used in the research pipeline.
"""

# Research and draft models
from .research import ResearchRun, Section, Paragraph, Draft, ResearchPhase, EffortLevel
from .draft_ast import DraftAST, Note as DraftNote, ParagraphNode, SectionNode, NoteType

# Evidence gathering models
from .evidence import SearchResult, Document, Span, Note as EvidenceNote

__all__ = [
    # Research models
    "ResearchRun",
    "Section",
    "Paragraph",
    "Draft",
    "ResearchPhase",
    "EffortLevel",
    # Draft AST models
    "DraftAST",
    "DraftNote",
    "ParagraphNode",
    "SectionNode",
    "NoteType",
    # Evidence models
    "SearchResult",
    "Document",
    "Span",
    "EvidenceNote",
]
