"""Tests for markdown rendering with citations."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    ResearchRun,
    Draft,
    Section,
    Paragraph,
    DraftAST,
    Note,
    SectionNode,
    ParagraphNode,
    EffortLevel,
    NoteType,
    ResearchPhase,
)
from src.artifacts import Renderer, ArtifactManager, StateManager


def test_basic_citation_rendering():
    """Test that citations render correctly in markdown."""
    print("Testing basic citation rendering...")

    draft_ast = DraftAST(draft_id="draft-1")

    note1 = Note(
        id="note-1",
        type=NoteType.CITATION,
        content="Example finding from research",
        source_title="Research Paper 2024",
        source_url="https://example.com/paper",
    )

    note2 = Note(
        id="note-2",
        type=NoteType.EVIDENCE,
        content="Supporting evidence from another source",
        source_title="Study on Topic",
        author="Dr. Smith",
    )

    draft_ast.add_note(note1)
    draft_ast.add_note(note2)

    para1 = ParagraphNode(
        id="para-1",
        content="This is a paragraph with citations.",
        note_ids=["note-1", "note-2"],
    )

    para2 = ParagraphNode(
        id="para-2",
        content="This paragraph has only one citation.",
        note_ids=["note-1"],
    )

    section = SectionNode(id="sec-1", title="Introduction", paragraphs=[para1, para2])

    draft_ast.add_section(section)

    renderer = Renderer()
    markdown = renderer.render_full_report(draft_ast)

    print("Rendered markdown:")
    print(markdown)
    print()

    assert "[1]" in markdown, "Citation [1] not found in markdown"
    assert "[2]" in markdown, "Citation [2] not found in markdown"
    assert "## References" in markdown, "References section not found"
    assert "Research Paper 2024" in markdown, "Source title not in references"

    print("✓ Basic citation rendering test passed")


def test_nested_sections():
    """Test rendering nested sections with citations."""
    print("Testing nested sections...")

    draft_ast = DraftAST(draft_id="draft-2")

    note1 = Note(
        id="note-1",
        type=NoteType.CITATION,
        content="First source",
        source_title="Source A",
    )

    draft_ast.add_note(note1)

    para1 = ParagraphNode(
        id="para-1", content="Parent section content.", note_ids=["note-1"]
    )
    para2 = ParagraphNode(id="para-2", content="Child section content.")

    subsection = SectionNode(
        id="subsec-1", title="Subsection", paragraphs=[para2], level=2
    )

    main_section = SectionNode(
        id="sec-1", title="Main Section", paragraphs=[para1], subsections=[subsection]
    )

    draft_ast.add_section(main_section)

    renderer = Renderer()
    markdown = renderer.render_full_report(draft_ast)

    print("Rendered markdown:")
    print(markdown)
    print()

    assert "# Main Section" in markdown, "Main section heading not found"
    assert "## Subsection" in markdown, "Subsection heading not found"
    assert "[1]" in markdown, "Citation not found"

    print("✓ Nested sections test passed")


def test_paragraph_without_citations():
    """Test rendering paragraphs without citations."""
    print("Testing paragraphs without citations...")

    draft_ast = DraftAST(draft_id="draft-3")

    para = ParagraphNode(id="para-1", content="This paragraph has no citations.")

    section = SectionNode(id="sec-1", title="Introduction", paragraphs=[para])

    draft_ast.add_section(section)

    renderer = Renderer()
    markdown = renderer.render_draft(draft_ast)

    print("Rendered markdown:")
    print(markdown)
    print()

    assert "This paragraph has no citations." in markdown
    assert "[1]" not in markdown, "Citation found in paragraph without notes"

    print("✓ Paragraphs without citations test passed")


def test_references_section():
    """Test references section rendering."""
    print("Testing references section rendering...")

    notes = [
        Note(
            id="note-1",
            type=NoteType.CITATION,
            content="Content",
            source_title="Paper One",
            source_url="https://example.com/1",
            author="Author A",
            date="2024",
        ),
        Note(
            id="note-2",
            type=NoteType.CITATION,
            content="Content",
            source_title="Paper Two",
            author="Author B",
        ),
    ]

    renderer = Renderer()
    references = renderer.render_references(notes)

    print("Rendered references:")
    print(references)
    print()

    assert "## References" in references
    assert "[1]" in references
    assert "[2]" in references
    assert "Paper One" in references
    assert "Paper Two" in references

    print("✓ References section test passed")


def test_artifact_manager_paths():
    """Test artifact manager path generation."""
    print("Testing artifact manager paths...")

    manager = ArtifactManager(Path("/tmp/test-project"))

    run_id = "test-run-123"

    assert manager.get_run_dir(run_id) == Path(
        "/tmp/test-project/.opencode/deep-research/test-run-123"
    )
    assert manager.get_state_path(run_id) == Path(
        "/tmp/test-project/.opencode/deep-research/test-run-123/state.json"
    )
    assert manager.get_report_path(run_id) == Path(
        "/tmp/test-project/.opencode/deep-research/test-run-123/report.md"
    )
    assert manager.get_references_path(run_id) == Path(
        "/tmp/test-project/.opencode/deep-research/test-run-123/references.json"
    )

    print("✓ Artifact manager paths test passed")


def test_state_serialization():
    """Test research run state serialization and deserialization."""
    print("Testing state serialization...")

    run = ResearchRun(
        run_id="test-run-456",
        query="What is machine learning?",
        effort=EffortLevel.STANDARD,
        phase=ResearchPhase.PLANNING,
    )

    draft = Draft(
        id="draft-1",
        version=1,
        sections=[
            Section(
                id="sec-1",
                title="Introduction",
                paragraphs=[
                    Paragraph(id="para-1", content="Test content", note_ids=["note-1"])
                ],
            )
        ],
    )

    run.add_draft(draft)

    run_dict = run.to_dict()

    assert run_dict["run_id"] == "test-run-456"
    assert run_dict["query"] == "What is machine learning?"
    assert run_dict["effort"] == 2
    assert run_dict["phase"] == "planning"
    assert len(run_dict["drafts"]) == 1

    restored_run = ResearchRun.from_dict(run_dict)

    assert restored_run.run_id == run.run_id
    assert restored_run.query == run.query
    assert restored_run.effort == run.effort
    assert restored_run.phase == run.phase
    assert len(restored_run.drafts) == len(run.drafts)

    print("✓ State serialization test passed")


def test_draft_ast_note_binding():
    """Test binding notes to paragraphs in draft AST."""
    print("Testing draft AST note binding...")

    draft_ast = DraftAST(draft_id="draft-4")

    note = Note(
        id="note-1",
        type=NoteType.EVIDENCE,
        content="Important evidence",
        source_title="Source",
    )

    para = ParagraphNode(id="para-1", content="Paragraph content.")
    section = SectionNode(id="sec-1", title="Section", paragraphs=[para])
    draft_ast.add_section(section)

    draft_ast.bind_note("para-1", note)

    assert "note-1" in para.note_ids, "Note not bound to paragraph"
    assert draft_ast.get_note("note-1") == note, "Note not added to draft AST"

    citation_num = draft_ast.get_citation_number("note-1")
    assert citation_num == 1, f"Expected citation number 1, got {citation_num}"

    print("✓ Draft AST note binding test passed")


def test_full_integration():
    """Integration test: create run, render report, save and load state."""
    print("Testing full integration...")

    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())

    try:
        manager = ArtifactManager(temp_dir)

        run = ResearchRun(
            run_id="integration-test",
            query="Test query",
            effort=EffortLevel.QUICK,
            phase=ResearchPhase.COMPLETE,
        )

        draft_ast = DraftAST(draft_id="draft-1")

        note1 = Note(
            id="note-1",
            type=NoteType.CITATION,
            content="Citation content",
            source_title="Test Source",
        )
        draft_ast.add_note(note1)

        para = ParagraphNode(
            id="para-1", content="Test paragraph.", note_ids=["note-1"]
        )
        section = SectionNode(id="sec-1", title="Test Section", paragraphs=[para])
        draft_ast.add_section(section)

        renderer = Renderer()
        markdown = renderer.render_full_report(draft_ast)

        manager.save_report(run.run_id, markdown)

        state_path = manager.save_state(run)
        assert state_path.exists(), "State file not created"

        loaded_run = manager.load_state(run.run_id)
        assert loaded_run.run_id == run.run_id
        assert loaded_run.query == run.query

        loaded_report = manager.load_report(run.run_id)
        assert "Test Section" in loaded_report
        assert "[1]" in loaded_report
        assert "Test Source" in loaded_report

        print("✓ Full integration test passed")

    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Deep Research Rendering Tests")
    print("=" * 60)
    print()

    tests = [
        test_basic_citation_rendering,
        test_nested_sections,
        test_paragraph_without_citations,
        test_references_section,
        test_artifact_manager_paths,
        test_state_serialization,
        test_draft_ast_note_binding,
        test_full_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Tests: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
