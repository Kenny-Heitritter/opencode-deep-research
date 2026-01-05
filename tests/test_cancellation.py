"""Tests for cancellation functionality and partial artifact generation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    ResearchRun,
    Draft,
    Section,
    Paragraph,
    ResearchPhase,
    EffortLevel,
)
from src.orchestrator import Cancellation, PartialArtifact, CancellationStatus


def test_cancel_during_planning():
    """Test cancellation during planning phase."""
    print("Testing cancellation during planning phase...")

    run = ResearchRun(
        run_id="run-planning",
        query="What is quantum computing?",
        effort=EffortLevel.STANDARD,
        phase=ResearchPhase.PLANNING,
    )

    run.metadata["clarifying_questions"] = [
        "What aspects of quantum computing are you most interested in?",
        "Do you need technical details or a general overview?",
    ]

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    assert artifact.run_id == "run-planning"
    assert artifact.cancellation_status == CancellationStatus.CANCELLED_PLANNING
    assert artifact.phase_at_cancellation == ResearchPhase.PLANNING
    assert len(artifact.sections_completed) == 0
    print("  ✓ Planning phase cancellation handled correctly")


def test_cancel_during_gathering():
    """Test cancellation during gathering phase."""
    print("Testing cancellation during gathering phase...")

    run = ResearchRun(
        run_id="run-gathering",
        query="Climate change impacts",
        effort=EffortLevel.DEEP,
        phase=ResearchPhase.GATHERING,
    )

    run.metadata["outline"] = "1. Introduction\n2. Evidence\n3. Conclusion"
    run.metadata["queries_completed"] = [
        "climate change effects on agriculture",
        "sea level rise predictions",
    ]
    run.metadata["sources_gathered"] = [
        "https://example.com/climate1",
        "https://example.com/climate2",
    ]

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    assert artifact.cancellation_status == CancellationStatus.CANCELLED_GATHERING
    assert artifact.metadata["outline"] is not None
    assert len(artifact.metadata["queries_completed"]) == 2
    print("  ✓ Gathering phase cancellation preserved metadata")


def test_cancel_during_drafting():
    """Test cancellation during drafting phase with partial content."""
    print("Testing cancellation during drafting phase...")

    draft = Draft(
        id="draft-1",
        version=1,
        sections=[
            Section(
                id="sec-1",
                title="Introduction",
                paragraphs=[
                    Paragraph(
                        id="para-1",
                        content="This is the introduction to the research topic.",
                    ),
                    Paragraph(
                        id="para-2",
                        content="We will explore several key aspects.",
                    ),
                ],
            ),
            Section(
                id="sec-2",
                title="Background",
                paragraphs=[
                    Paragraph(
                        id="para-3",
                        content="Historical context is important for understanding.",
                    )
                ],
            ),
        ],
    )

    run = ResearchRun(
        run_id="run-drafting",
        query="History of space exploration",
        effort=EffortLevel.STANDARD,
        phase=ResearchPhase.DRAFTING,
    )

    run.add_draft(draft)
    run.metadata["sections_remaining"] = ["Conclusion", "References"]

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    assert artifact.cancellation_status == CancellationStatus.CANCELLED_DRAFTING
    assert len(artifact.sections_completed) == 2
    assert artifact.sections_completed[0].title == "Introduction"
    assert len(artifact.sections_completed[0].paragraphs) == 2
    print("  ✓ Drafting phase cancellation preserved sections")


def test_partial_artifact_to_markdown_planning():
    """Test markdown generation for planning phase cancellation."""
    print("Testing markdown generation for planning phase...")

    run = ResearchRun(
        run_id="run-1",
        query="Test query",
        effort=EffortLevel.QUICK,
        phase=ResearchPhase.PLANNING,
    )

    run.metadata["clarifying_questions"] = ["Question 1?", "Question 2?"]

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    markdown = artifact.to_markdown()

    assert "Research Report (Incomplete)" in markdown
    assert "Test query" in markdown
    assert "planning phase" in markdown.lower()
    assert "Question 1?" in markdown
    print("  ✓ Planning phase markdown generated correctly")


def test_partial_artifact_to_markdown_drafting():
    """Test markdown generation for drafting phase cancellation."""
    print("Testing markdown generation for drafting phase...")

    draft = Draft(
        id="draft-1",
        version=1,
        sections=[
            Section(
                id="sec-1",
                title="Main Section",
                paragraphs=[
                    Paragraph(
                        id="para-1",
                        content="First paragraph of content.",
                    ),
                ],
                subsections=[
                    Section(
                        id="subsec-1",
                        title="Subsection",
                        paragraphs=[
                            Paragraph(
                                id="para-2",
                                content="Subsection content.",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    run = ResearchRun(
        run_id="run-2",
        query="Another query",
        effort=EffortLevel.STANDARD,
        phase=ResearchPhase.DRAFTING,
    )

    run.add_draft(draft)

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    markdown = artifact.to_markdown()

    assert "Main Section" in markdown
    assert "First paragraph of content." in markdown
    assert "Subsection" in markdown
    assert "Subsection content." in markdown
    assert "incomplete" in markdown.lower()
    print("  ✓ Drafting phase markdown includes sections")


def test_cancellation_retrieval():
    """Test retrieving cancelled run artifacts."""
    print("Testing cancellation retrieval...")

    run = ResearchRun(
        run_id="run-retrieve",
        query="Test",
        effort=EffortLevel.QUICK,
        phase=ResearchPhase.ANALYSIS,
    )

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    # Retrieve the artifact
    retrieved = cancellation.get_partial_artifact("run-retrieve")

    assert retrieved is not None
    assert retrieved.run_id == "run-retrieve"
    assert cancellation.is_cancelled("run-retrieve")

    # Test non-existent run
    non_existent = cancellation.get_partial_artifact("non-existent")
    assert non_existent is None
    assert not cancellation.is_cancelled("non-existent")

    print("  ✓ Cancellation retrieval works correctly")


def test_cancellation_clear():
    """Test clearing cancelled runs."""
    print("Testing cancellation clearing...")

    run = ResearchRun(
        run_id="run-clear",
        query="Test",
        effort=EffortLevel.QUICK,
        phase=ResearchPhase.GATHERING,
    )

    cancellation = Cancellation()
    cancellation.cancel_run(run)

    assert cancellation.is_cancelled("run-clear")

    # Clear the run
    cancellation.clear_cancelled_run("run-clear")

    assert not cancellation.is_cancelled("run-clear")
    assert cancellation.get_partial_artifact("run-clear") is None

    print("  ✓ Cancellation clearing works correctly")


def test_partial_artifact_serialization():
    """Test serialization and deserialization of partial artifacts."""
    print("Testing partial artifact serialization...")

    draft = Draft(
        id="draft-1",
        version=1,
        sections=[
            Section(
                id="sec-1",
                title="Test Section",
                paragraphs=[Paragraph(id="para-1", content="Test content")],
            )
        ],
    )

    run = ResearchRun(
        run_id="run-serial",
        query="Serialization test",
        effort=EffortLevel.STANDARD,
        phase=ResearchPhase.DRAFTING,
    )

    run.add_draft(draft)

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    # Serialize
    artifact_dict = artifact.to_dict()

    assert artifact_dict["run_id"] == "run-serial"
    assert artifact_dict["original_query"] == "Serialization test"
    assert len(artifact_dict["sections_completed"]) == 1

    # Deserialize
    restored = PartialArtifact.from_dict(artifact_dict)

    assert restored.run_id == artifact.run_id
    assert restored.original_query == artifact.original_query
    assert len(restored.sections_completed) == len(artifact.sections_completed)
    assert restored.sections_completed[0].title == "Test Section"

    print("  ✓ Serialization/deserialization works correctly")


def test_cancel_all_phases():
    """Test cancellation status for all phases."""
    print("Testing cancellation for all phases...")

    phases = [
        (ResearchPhase.PLANNING, CancellationStatus.CANCELLED_PLANNING),
        (ResearchPhase.GATHERING, CancellationStatus.CANCELLED_GATHERING),
        (ResearchPhase.ANALYSIS, CancellationStatus.CANCELLED_ANALYSIS),
        (ResearchPhase.DRAFTING, CancellationStatus.CANCELLED_DRAFTING),
        (ResearchPhase.COMPLETE, CancellationStatus.COMPLETED),
    ]

    cancellation = Cancellation()

    for phase, expected_status in phases:
        run = ResearchRun(
            run_id=f"run-{phase.value}",
            query="Test",
            effort=EffortLevel.QUICK,
            phase=phase,
        )

        artifact = cancellation.cancel_run(run)
        assert artifact.cancellation_status == expected_status

    print(f"  ✓ All {len(phases)} phases handle cancellation correctly")


def test_partial_artifact_with_metadata():
    """Test that metadata is preserved in partial artifacts."""
    print("Testing metadata preservation...")

    run = ResearchRun(
        run_id="run-meta",
        query="Metadata test",
        effort=EffortLevel.DEEP,
        phase=ResearchPhase.GATHERING,
    )

    run.metadata["custom_field"] = "custom_value"
    run.metadata["evidence_count"] = 42
    run.metadata["outline"] = "# Test Outline"

    cancellation = Cancellation()
    artifact = cancellation.cancel_run(run)

    assert artifact.metadata["custom_field"] == "custom_value"
    assert artifact.metadata["evidence_count"] == 42
    assert artifact.metadata["outline"] == "# Test Outline"

    print("  ✓ Metadata preserved in artifact")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Cancellation Tests")
    print("=" * 60)
    print()

    tests = [
        test_cancel_during_planning,
        test_cancel_during_gathering,
        test_cancel_during_drafting,
        test_partial_artifact_to_markdown_planning,
        test_partial_artifact_to_markdown_drafting,
        test_cancellation_retrieval,
        test_cancellation_clear,
        test_partial_artifact_serialization,
        test_cancel_all_phases,
        test_partial_artifact_with_metadata,
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
            import traceback

            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print(f"Tests: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
