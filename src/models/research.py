"""Core data models for Deep Research runs."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ResearchPhase(Enum):
    """Research execution phases."""

    PLANNING = "planning"
    GATHERING = "gathering"
    ANALYSIS = "analysis"
    DRAFTING = "drafting"
    COMPLETE = "complete"
    FAILED = "failed"


class EffortLevel(Enum):
    """Research effort levels."""

    QUICK = 1
    STANDARD = 2
    DEEP = 3


@dataclass
class Paragraph:
    """A paragraph within a section with optional note bindings."""

    id: str
    content: str
    note_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "note_ids": self.note_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paragraph":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            note_ids=data.get("note_ids", []),
        )


@dataclass
class Section:
    """A section of the research report."""

    id: str
    title: str
    paragraphs: List[Paragraph] = field(default_factory=list)
    subsections: List["Section"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "subsections": [s.to_dict() for s in self.subsections],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Section":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            paragraphs=[Paragraph.from_dict(p) for p in data.get("paragraphs", [])],
            subsections=[Section.from_dict(s) for s in data.get("subsections", [])],
        )


@dataclass
class Draft:
    """A draft version of the research report."""

    id: str
    version: int
    sections: List[Section] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "version": self.version,
            "sections": [s.to_dict() for s in self.sections],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Draft":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            version=data["version"],
            sections=[Section.from_dict(s) for s in data.get("sections", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class ResearchRun:
    """Complete state of a research run."""

    run_id: str
    query: str
    effort: EffortLevel
    phase: ResearchPhase = ResearchPhase.PLANNING
    drafts: List[Draft] = field(default_factory=list)
    current_draft_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "query": self.query,
            "effort": self.effort.value,
            "phase": self.phase.value,
            "drafts": [d.to_dict() for d in self.drafts],
            "current_draft_id": self.current_draft_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchRun":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            query=data["query"],
            effort=EffortLevel(data["effort"]),
            phase=ResearchPhase(data["phase"]),
            drafts=[Draft.from_dict(d) for d in data.get("drafts", [])],
            current_draft_id=data.get("current_draft_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )

    def get_current_draft(self) -> Optional[Draft]:
        """Get the current draft being worked on."""
        if not self.current_draft_id:
            return None
        for draft in self.drafts:
            if draft.id == self.current_draft_id:
                return draft
        return None

    def add_draft(self, draft: Draft) -> None:
        """Add a new draft and set it as current."""
        self.drafts.append(draft)
        self.current_draft_id = draft.id
        self.updated_at = datetime.utcnow()
