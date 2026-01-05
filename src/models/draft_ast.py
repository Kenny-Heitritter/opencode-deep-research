"""Draft Abstract Syntax Tree with note bindings to evidence."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from enum import Enum


class NoteType(Enum):
    """Types of research notes."""

    CITATION = "citation"
    EVIDENCE = "evidence"
    QUOTE = "quote"
    CLAIM = "claim"
    UNCERTAINTY = "uncertainty"
    CONTRADICTION = "contradiction"


@dataclass
class Note:
    """A research note containing evidence, citations, or context."""

    id: str
    type: NoteType
    content: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "author": self.author,
            "date": self.date,
            "confidence": self.confidence,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Note":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=NoteType(data["type"]),
            content=data["content"],
            source_url=data.get("source_url"),
            source_title=data.get("source_title"),
            author=data.get("author"),
            date=data.get("date"),
            confidence=data.get("confidence", 1.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def get_citation_text(self) -> str:
        """Generate citation text for this note."""
        parts = []
        if self.author:
            parts.append(self.author)
        if self.source_title:
            parts.append(f'"{self.source_title}"')
        if self.date:
            parts.append(f"({self.date})")
        if self.source_url:
            parts.append(self.source_url)

        return ", ".join(parts) if parts else self.content[:100]


@dataclass
class ParagraphNode:
    """AST node representing a paragraph with note bindings."""

    id: str
    content: str
    note_ids: List[str] = field(default_factory=list)

    def bind_note(self, note_id: str) -> None:
        """Bind a note to this paragraph."""
        if note_id not in self.note_ids:
            self.note_ids.append(note_id)

    def unbind_note(self, note_id: str) -> None:
        """Remove a note binding from this paragraph."""
        if note_id in self.note_ids:
            self.note_ids.remove(note_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "note_ids": self.note_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParagraphNode":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            note_ids=data.get("note_ids", []),
        )


@dataclass
class SectionNode:
    """AST node representing a section with subsections and paragraphs."""

    id: str
    title: str
    paragraphs: List[ParagraphNode] = field(default_factory=list)
    subsections: List["SectionNode"] = field(default_factory=list)
    level: int = 1

    def add_paragraph(self, paragraph: ParagraphNode) -> None:
        """Add a paragraph to this section."""
        self.paragraphs.append(paragraph)

    def add_subsection(self, subsection: "SectionNode") -> None:
        """Add a subsection to this section."""
        self.subsections.append(subsection)

    def get_all_note_ids(self) -> Set[str]:
        """Get all note IDs referenced in this section and subsections."""
        note_ids = set()
        for para in self.paragraphs:
            note_ids.update(para.note_ids)
        for subsection in self.subsections:
            note_ids.update(subsection.get_all_note_ids())
        return note_ids

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "subsections": [s.to_dict() for s in self.subsections],
            "level": self.level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectionNode":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            paragraphs=[ParagraphNode.from_dict(p) for p in data.get("paragraphs", [])],
            subsections=[SectionNode.from_dict(s) for s in data.get("subsections", [])],
            level=data.get("level", 1),
        )


@dataclass
class DraftAST:
    """Draft Abstract Syntax Tree tracking document structure and note bindings."""

    draft_id: str
    sections: List[SectionNode] = field(default_factory=list)
    notes: Dict[str, Note] = field(default_factory=dict)
    note_order: List[str] = field(default_factory=list)

    def add_section(self, section: SectionNode) -> None:
        """Add a section to the draft."""
        self.sections.append(section)

    def add_note(self, note: Note) -> None:
        """Add a note to the draft's note collection."""
        self.notes[note.id] = note
        if note.id not in self.note_order:
            self.note_order.append(note.id)

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        return self.notes.get(note_id)

    def bind_note(self, paragraph_id: str, note: Note) -> None:
        """Bind a note to a paragraph."""
        self.add_note(note)

        for section in self.sections:
            self._bind_note_to_section(section, paragraph_id, note.id)

    def _bind_note_to_section(
        self, section: SectionNode, paragraph_id: str, note_id: str
    ) -> bool:
        """Recursively bind note to paragraph in section tree."""
        for para in section.paragraphs:
            if para.id == paragraph_id:
                para.bind_note(note_id)
                return True

        for subsection in section.subsections:
            if self._bind_note_to_section(subsection, paragraph_id, note_id):
                return True

        return False

    def get_all_referenced_notes(self) -> List[Note]:
        """Get all notes that are actually referenced in the draft."""
        referenced_ids = set()
        for section in self.sections:
            referenced_ids.update(section.get_all_note_ids())

        return [
            self.notes[note_id]
            for note_id in self.note_order
            if note_id in referenced_ids
        ]

    def get_citation_number(self, note_id: str) -> Optional[int]:
        """Get the citation number for a note (1-based)."""
        referenced_notes = self.get_all_referenced_notes()
        for i, note in enumerate(referenced_notes, start=1):
            if note.id == note_id:
                return i
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "draft_id": self.draft_id,
            "sections": [s.to_dict() for s in self.sections],
            "notes": {note_id: note.to_dict() for note_id, note in self.notes.items()},
            "note_order": self.note_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DraftAST":
        """Create from dictionary."""
        return cls(
            draft_id=data["draft_id"],
            sections=[SectionNode.from_dict(s) for s in data.get("sections", [])],
            notes={
                note_id: Note.from_dict(note_data)
                for note_id, note_data in data.get("notes", {}).items()
            },
            note_order=data.get("note_order", []),
        )
