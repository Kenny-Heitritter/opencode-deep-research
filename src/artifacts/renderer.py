"""Markdown renderer with citations for research reports."""

from typing import List, Dict, Set, Optional
import logging

from ..models import DraftAST, DraftNote, SectionNode, ParagraphNode


logger = logging.getLogger(__name__)


class Renderer:
    """Renders draft AST to markdown with inline citations and references."""

    def __init__(self):
        """Initialize the renderer."""
        self.citation_map: Dict[str, int] = {}

    def render_draft(self, draft: DraftAST) -> str:
        """
        Render a draft AST to markdown with citations.

        Args:
            draft: The draft AST to render

        Returns:
            Markdown string with inline citations [1], [2], etc.
        """
        self.citation_map = self._build_citation_map(draft)

        lines = []

        for section in draft.sections:
            lines.extend(self._render_section(section, level=1))
            lines.append("")

        return "\n".join(lines)

    def render_references(self, notes: List[DraftNote]) -> str:
        """
        Render references section for a list of notes.

        Args:
            notes: List of notes to render as references

        Returns:
            Markdown string with numbered references
        """
        if not notes:
            return ""

        lines = ["## References", ""]

        for i, note in enumerate(notes, start=1):
            citation_text = note.get_citation_text()
            lines.append(f"[{i}] {citation_text}")

        return "\n".join(lines)

    def render_full_report(self, draft: DraftAST) -> str:
        """
        Render a complete report with body and references.

        Args:
            draft: The draft AST to render

        Returns:
            Complete markdown report with inline citations and references section
        """
        body = self.render_draft(draft)
        referenced_notes = draft.get_all_referenced_notes()
        references = self.render_references(referenced_notes)

        if references:
            return f"{body}\n\n{references}\n"
        else:
            return body

    def _build_citation_map(self, draft: DraftAST) -> Dict[str, int]:
        """Build a mapping from note IDs to citation numbers."""
        citation_map = {}
        referenced_notes = draft.get_all_referenced_notes()

        for i, note in enumerate(referenced_notes, start=1):
            citation_map[note.id] = i

        return citation_map

    def _render_section(self, section: SectionNode, level: int) -> List[str]:
        """Render a section node to markdown lines."""
        lines = []

        heading_prefix = "#" * level
        lines.append(f"{heading_prefix} {section.title}")
        lines.append("")

        for paragraph in section.paragraphs:
            para_text = self._render_paragraph(paragraph)
            lines.append(para_text)
            lines.append("")

        for subsection in section.subsections:
            lines.extend(self._render_section(subsection, level + 1))
            lines.append("")

        return lines

    def _render_paragraph(self, paragraph: ParagraphNode) -> str:
        """Render a paragraph with inline citations."""
        text = paragraph.content

        if paragraph.note_ids:
            citations = [
                f"[{self.citation_map[note_id]}]"
                for note_id in paragraph.note_ids
                if note_id in self.citation_map
            ]

            if citations:
                citation_str = "".join(citations)
                text = f"{text}{citation_str}"

        return text

    def render_draft_metadata(self, draft: DraftAST, run_query: str) -> str:
        """
        Render metadata header for a draft.

        Args:
            draft: The draft AST
            run_query: The research query

        Returns:
            Markdown metadata header
        """
        referenced_notes = draft.get_all_referenced_notes()
        note_count = len(referenced_notes)
        section_count = len(draft.sections)

        lines = [
            f"# Research Report: {run_query}",
            "",
            f"**Draft ID:** {draft.draft_id}",
            f"**Sections:** {section_count}",
            f"**Citations:** {note_count}",
            "",
        ]

        return "\n".join(lines)

    def render_contradictions_section(self, notes: List[DraftNote]) -> str:
        """
        Render a contradictions and uncertainties section.

        Args:
            notes: List of notes marked as contradictions or uncertainties

        Returns:
            Markdown section for contradictions
        """
        if not notes:
            return ""

        lines = ["## Contradictions and Uncertainties", ""]

        for note in notes:
            if note.type.value in ["contradiction", "uncertainty"]:
                confidence_str = (
                    f"(confidence: {note.confidence:.0%})"
                    if note.confidence < 1.0
                    else ""
                )
                lines.append(f"- {note.content} {confidence_str}")
                if note.source_title:
                    lines.append(f"  *Source: {note.source_title}*")
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape special markdown characters."""
        special_chars = [
            "\\",
            "`",
            "*",
            "_",
            "{",
            "}",
            "[",
            "]",
            "(",
            ")",
            "#",
            "+",
            "-",
            ".",
            "!",
        ]
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text
