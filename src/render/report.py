"""Markdown renderer with [^N] citations and ## References section."""

import logging
from typing import Optional
from collections import defaultdict

from src.models import DraftAST, DraftSection, Note, ResearchRun

logger = logging.getLogger(__name__)


class ReportRenderer:
    """Render research reports with proper citations and references."""

    def __init__(self):
        """Initialize report renderer."""
        self.citation_counter = 0
        self.url_to_citation: dict[str, int] = {}

    def render(self, draft: DraftAST) -> str:
        """Render a draft AST to markdown with citations.

        Args:
            draft: Draft abstract syntax tree

        Returns:
            Markdown string with citations and references
        """
        self.citation_counter = 0
        self.url_to_citation.clear()

        report_parts = []

        report_parts.append(f"# Research Report: {draft.query}\n\n")
        report_parts.append(f"**Plan:** {draft.plan}\n\n")
        report_parts.append("---\n\n")

        for section in draft.sections:
            report_parts.append(self._render_section(section))

        if draft.references:
            report_parts.append(self._render_references(draft.references))

        if draft.contradictions:
            report_parts.append(self._render_contradictions(draft.contradictions))

        if draft.uncertainties:
            report_parts.append(self._render_uncertainties(draft.uncertainties))

        return "".join(report_parts)

    def _render_section(self, section: DraftSection) -> str:
        """Render a single section with citations.

        Args:
            section: Section to render

        Returns:
            Markdown for the section
        """
        header = f"## {section.title}\n\n"
        content = self._add_citations(section.content)
        return f"{header}{content}\n\n"

    def _add_citations(self, text: str) -> str:
        """Add citation placeholders to text.

        Args:
            text: Text to add citations to

        Returns:
            Text with citation markers
        """
        return text

    def _render_references(self, references: list[tuple[int, str, str]]) -> str:
        """Render references section.

        Args:
            references: List of (citation_num, url, title) tuples

        Returns:
            Markdown references section
        """
        lines = ["## References\n\n"]

        for num, url, title in references:
            lines.append(f"[^{num}] {title}\n\n")
            lines.append(f"Source: {url}\n\n")

        return "".join(lines)

    def _render_contradictions(self, contradictions: list[str]) -> str:
        """Render contradictions section.

        Args:
            contradictions: List of contradictions found

        Returns:
            Markdown contradictions section
        """
        lines = ["## Contradictions\\n\\n"]

        for i, contradiction in enumerate(contradictions, 1):
            lines.append(f"{i}. {contradiction}\\n")

        lines.append("\n")
        return "".join(lines)

    def _render_uncertainties(self, uncertainties: list[str]) -> str:
        """Render uncertainties section.

        Args:
            uncertainties: List of uncertainties found

        Returns:
            Markdown uncertainties section
        """
        lines = ["## Uncertainties\\n\\n"]

        for i, uncertainty in enumerate(uncertainties, 1):
            lines.append(f"{i}. {uncertainty}\\n")

        lines.append("\n")
        return "".join(lines)

    def render_from_run(self, run: ResearchRun) -> str:
        """Render a report directly from a ResearchRun.

        Args:
            run: Research run with collected data

        Returns:
            Complete markdown report
        """
        draft = self._create_draft_from_run(run)
        return self.render(draft)

    def _create_draft_from_run(self, run: ResearchRun) -> DraftAST:
        """Create a DraftAST from a ResearchRun.

        Args:
            run: Research run

        Returns:
            DraftAST for rendering
        """
        renderer = ReportRenderer()

        content_parts = []
        reference_map: dict[str, tuple[str, str]] = {}

        citation_num = 1
        for note in run.notes:
            if note.source_url not in reference_map:
                doc_title = next(
                    (d.title for d in run.documents if d.url == note.source_url),
                    note.source_url,
                )
                reference_map[note.source_url] = (str(citation_num), doc_title)
                citation_num += 1

            citation = reference_map[note.source_url][0]
            content_parts.append(f"{note.content} [^{citation}]\n\n")

        sections = [
            DraftSection(
                title="Research Findings",
                content="".join(content_parts),
            ),
            DraftSection(
                title="Search Summary",
                content=(
                    f"This research investigated '{run.query}' "
                    f"with effort level {run.effort}.\n\n"
                    f"Found {len(run.search_results)} search results, "
                    f"fetched {len(run.documents)} documents, "
                    f"and extracted {len(run.notes)} relevant notes.\n\n"
                ),
            ),
        ]

        references = [
            (int(num), url, title) for url, (num, title) in reference_map.items()
        ]

        return DraftAST(
            query=run.query,
            plan=run.plan,
            sections=sections,
            references=references,
            contradictions=[],
            uncertainties=[],
        )
