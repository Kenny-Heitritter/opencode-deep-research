"""Tests for verification module: support checking, contradiction detection, and critique."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    Draft,
    Section,
    Paragraph,
    DraftAST,
    DraftNote,
    SectionNode,
    ParagraphNode,
    NoteType,
)
from src.verification import (
    SupportChecker,
    SupportCheckResult,
    ContradictionDetector,
    Contradiction,
    ContradictionSeverity,
    CritiqueAgent,
    FollowUpQuery,
    UncertaintyTracker,
    UncertaintyType,
)


def test_support_checker_with_notes():
    """Test that supported paragraphs pass the check."""
    print("Testing support checker with notes...")

    checker = SupportChecker(min_confidence=0.6)

    note1 = DraftNote(
        id="note-1",
        type=NoteType.EVIDENCE,
        content="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        confidence=0.9,
    )

    note2 = DraftNote(
        id="note-2",
        type=NoteType.CITATION,
        content="Deep learning uses neural networks with multiple layers to process complex data.",
        confidence=0.85,
    )

    paragraph = ParagraphNode(
        id="para-1",
        content="Machine learning, particularly deep learning with neural networks, has revolutionized artificial intelligence by enabling computers to learn from data.",
        note_ids=["note-1", "note-2"],
    )

    result = checker.check_paragraph(paragraph, [note1, note2])

    assert result.is_supported, (
        f"Paragraph should be supported, issues: {result.issues}"
    )
    assert result.confidence >= 0.6, f"Confidence too low: {result.confidence}"
    print(f"  ✓ Supported paragraph passed check (confidence: {result.confidence:.2f})")


def test_support_checker_no_notes():
    """Test that paragraphs without notes fail the check."""
    print("Testing support checker without notes...")

    checker = SupportChecker()

    paragraph = ParagraphNode(
        id="para-1",
        content="This paragraph makes claims without any supporting evidence.",
        note_ids=[],
    )

    result = checker.check_paragraph(paragraph, [])

    assert not result.is_supported, "Paragraph without notes should not be supported"
    assert "no supporting notes" in str(result.issues).lower()
    print("  ✓ Unsupported paragraph correctly identified")


def test_support_checker_low_confidence_notes():
    """Test that low confidence notes trigger issues."""
    print("Testing support checker with low confidence notes...")

    checker = SupportChecker(min_confidence=0.7)

    note = DraftNote(
        id="note-1",
        type=NoteType.EVIDENCE,
        content="Some uncertain information",
        confidence=0.3,  # Low confidence
    )

    paragraph = ParagraphNode(
        id="para-1",
        content="This paragraph has low confidence evidence.",
        note_ids=["note-1"],
    )

    result = checker.check_paragraph(paragraph, [note])

    assert not result.is_supported
    assert any("low confidence" in issue.lower() for issue in result.issues)
    print("  ✓ Low confidence notes correctly flagged")


def test_contradiction_detector_opposing_terms():
    """Test detection of contradictions using opposing terms."""
    print("Testing contradiction detector with opposing terms...")

    detector = ContradictionDetector(min_confidence=0.7)

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
                        content="The company's revenue showed significant growth over the past year, with profits increasing by 25%.",
                    ),
                    Paragraph(
                        id="para-2",
                        content="Financial reports indicate the company's revenue experienced a decrease during the same period.",
                    ),
                ],
            )
        ],
    )

    contradictions = detector.find_contradictions(draft)

    assert len(contradictions) > 0, (
        "Should detect contradiction between growth and decrease"
    )
    contradiction = contradictions[0]
    assert contradiction.confidence >= 0.7
    print(f"  ✓ Detected contradiction: {contradiction.reason}")


def test_contradiction_detector_negation():
    """Test detection of contradictions using negation patterns."""
    print("Testing contradiction detector with negation...")

    detector = ContradictionDetector(min_confidence=0.7)

    draft_ast = DraftAST(draft_id="draft-1")

    para1 = ParagraphNode(
        id="para-1",
        content="The treatment is safe and effective for most patients.",
    )

    para2 = ParagraphNode(
        id="para-2",
        content="The treatment is not safe for patients with certain conditions.",
    )

    section = SectionNode(
        id="sec-1", title="Treatment Safety", paragraphs=[para1, para2]
    )
    draft_ast.add_section(section)

    contradictions = detector.find_contradictions_ast(draft_ast)

    assert len(contradictions) > 0, "Should detect negation-based contradiction"
    print(f"  ✓ Detected {len(contradictions)} contradiction(s)")


def test_contradiction_detector_no_contradictions():
    """Test that non-contradicting paragraphs pass."""
    print("Testing contradiction detector with no contradictions...")

    detector = ContradictionDetector()

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
                        content="Machine learning is a field of artificial intelligence.",
                    ),
                    Paragraph(
                        id="para-2",
                        content="Deep learning is a subset of machine learning techniques.",
                    ),
                ],
            )
        ],
    )

    contradictions = detector.find_contradictions(draft)

    assert len(contradictions) == 0, (
        f"Should not detect contradictions, found: {len(contradictions)}"
    )
    print("  ✓ No false positive contradictions detected")


def test_critique_agent_contradiction_query():
    """Test critique agent generates queries for contradictions."""
    print("Testing critique agent with contradictions...")

    agent = CritiqueAgent()

    contradiction = Contradiction(
        paragraph1_id="para-1",
        paragraph2_id="para-2",
        paragraph1_content="The study found positive results.",
        paragraph2_content="The study found negative results.",
        reason="Opposing terms detected: 'positive' vs 'negative'",
        severity=ContradictionSeverity.HIGH,
        confidence=0.9,
        section1_title="Results",
        section2_title="Discussion",
    )

    queries = agent.generate_followup_queries([contradiction])

    assert len(queries) > 0, "Should generate at least one follow-up query"
    assert len(queries[0]) > 10, "Query should be substantive"
    print(f"  ✓ Generated query: {queries[0][:80]}...")


def test_critique_agent_detailed_queries():
    """Test critique agent generates detailed queries with priorities."""
    print("Testing critique agent detailed queries...")

    agent = CritiqueAgent()

    contradiction = Contradiction(
        paragraph1_id="para-1",
        paragraph2_id="para-2",
        paragraph1_content="Temperature increased.",
        paragraph2_content="Temperature decreased.",
        reason="Conflicting temperature trends",
        severity=ContradictionSeverity.HIGH,
        confidence=0.95,
    )

    queries = agent.generate_detailed_followup_queries(contradictions=[contradiction])

    assert len(queries) > 0
    assert isinstance(queries[0], FollowUpQuery)
    assert queries[0].priority >= 4, "High severity should have high priority"
    assert len(queries[0].related_paragraph_ids) == 2
    print(f"  ✓ Generated detailed query with priority {queries[0].priority}")


def test_uncertainty_tracker_add():
    """Test adding uncertainties to tracker."""
    print("Testing uncertainty tracker...")

    tracker = UncertaintyTracker()

    uncertainty = tracker.add_uncertainty(
        claim="The exact date is unclear",
        reason="Multiple sources provide different dates",
        uncertainty_type=UncertaintyType.CONFLICTING_SOURCES,
        sources=["source1.com", "source2.com"],
    )

    assert len(tracker.get_all_uncertainties()) == 1
    assert uncertainty.type == UncertaintyType.CONFLICTING_SOURCES
    print("  ✓ Uncertainty added successfully")


def test_uncertainty_tracker_from_contradiction():
    """Test adding contradiction as uncertainty."""
    print("Testing uncertainty tracker with contradiction...")

    tracker = UncertaintyTracker()

    contradiction = Contradiction(
        paragraph1_id="para-1",
        paragraph2_id="para-2",
        paragraph1_content="Data shows increase",
        paragraph2_content="Data shows decrease",
        reason="Opposing trends",
        severity=ContradictionSeverity.MEDIUM,
        confidence=0.8,
    )

    uncertainty = tracker.add_contradiction_as_uncertainty(contradiction)

    assert uncertainty.type == UncertaintyType.CONTRADICTION
    assert len(uncertainty.related_paragraph_ids) == 2
    print("  ✓ Contradiction converted to uncertainty")


def test_uncertainty_tracker_markdown():
    """Test markdown generation for uncertainties."""
    print("Testing uncertainty tracker markdown generation...")

    tracker = UncertaintyTracker()

    tracker.add_uncertainty(
        claim="Climate impact unclear",
        reason="Insufficient long-term data available",
        uncertainty_type=UncertaintyType.INSUFFICIENT_EVIDENCE,
    )

    tracker.add_uncertainty(
        claim="Study results vary",
        reason="Different methodologies produce different outcomes",
        uncertainty_type=UncertaintyType.CONFLICTING_SOURCES,
        sources=["study1.com", "study2.com"],
    )

    markdown = tracker.to_markdown()

    assert "## Uncertainties and Contradictions" in markdown
    assert "Climate impact unclear" in markdown
    assert "Study results vary" in markdown
    assert "study1.com" in markdown
    print("  ✓ Markdown generated correctly")


def test_support_checker_get_unsupported():
    """Test getting only unsupported paragraphs."""
    print("Testing support checker unsupported filter...")

    checker = SupportChecker()

    note = DraftNote(
        id="note-1", type=NoteType.EVIDENCE, content="Evidence for first paragraph"
    )

    para1 = ParagraphNode(
        id="para-1",
        content="First paragraph with evidence",
        note_ids=["note-1"],
    )

    para2 = ParagraphNode(
        id="para-2",
        content="Second paragraph without evidence",
        note_ids=[],
    )

    unsupported = checker.get_unsupported_paragraphs([para1, para2], [note])

    assert len(unsupported) == 1
    assert unsupported[0].paragraph_id == "para-2"
    print("  ✓ Correctly filtered unsupported paragraphs")


def test_integration_verification_pipeline():
    """Test full verification pipeline: support check -> contradiction -> critique."""
    print("Testing full verification pipeline...")

    # Create draft with issues
    draft = Draft(
        id="draft-1",
        version=1,
        sections=[
            Section(
                id="sec-1",
                title="Findings",
                paragraphs=[
                    Paragraph(
                        id="para-1",
                        content="The research shows positive outcomes with high confidence.",
                        note_ids=[],  # No support
                    ),
                    Paragraph(
                        id="para-2",
                        content="The research shows negative outcomes and failures.",
                        note_ids=["note-1"],
                    ),
                ],
            )
        ],
    )

    note = DraftNote(
        id="note-1", type=NoteType.EVIDENCE, content="Some evidence", confidence=0.5
    )

    # Step 1: Check support
    checker = SupportChecker()
    unsupported = checker.get_unsupported_paragraphs(
        [p for s in draft.sections for p in s.paragraphs], [note]
    )

    assert len(unsupported) > 0, "Should find unsupported paragraphs"

    # Step 2: Detect contradictions
    detector = ContradictionDetector(min_confidence=0.7)
    contradictions = detector.find_contradictions(draft)

    assert len(contradictions) > 0, "Should detect contradictions"

    # Step 3: Generate critique queries
    agent = CritiqueAgent()
    queries = agent.generate_detailed_followup_queries(
        contradictions=contradictions, unsupported=unsupported
    )

    assert len(queries) > 0, "Should generate follow-up queries"

    # Step 4: Track uncertainties
    tracker = UncertaintyTracker()
    for contradiction in contradictions:
        tracker.add_contradiction_as_uncertainty(contradiction)

    markdown = tracker.to_markdown()
    assert len(markdown) > 0, "Should generate uncertainty section"

    print(
        f"  ✓ Full pipeline: {len(unsupported)} unsupported, {len(contradictions)} contradictions, {len(queries)} queries"
    )


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Verification Tests")
    print("=" * 60)
    print()

    tests = [
        test_support_checker_with_notes,
        test_support_checker_no_notes,
        test_support_checker_low_confidence_notes,
        test_contradiction_detector_opposing_terms,
        test_contradiction_detector_negation,
        test_contradiction_detector_no_contradictions,
        test_critique_agent_contradiction_query,
        test_critique_agent_detailed_queries,
        test_uncertainty_tracker_add,
        test_uncertainty_tracker_from_contradiction,
        test_uncertainty_tracker_markdown,
        test_support_checker_get_unsupported,
        test_integration_verification_pipeline,
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
