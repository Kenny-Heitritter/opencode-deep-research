"""Test cancellation support."""

import pytest

from src.models import Document, Note, DraftSection
from src.research.cancellation import RunController


class TestCancellation:
    """Test mid-run cancellation with partial artifact return."""

    def test_create_and_cancel_run(self):
        """Test cancel returns partial artifacts (sections completed, citations)."""
        controller = RunController()

        run_id = controller.create_run("Test plan", 3, "test query")

        assert run_id in controller.active_runs
        assert run_id in controller.run_data
        assert controller.run_data[run_id].status == "initialized"

        partial_run = controller.cancel(run_id)

        assert partial_run.run_id == run_id
        assert partial_run.status == "cancelled"
        assert controller.is_cancelled(run_id) is True

    def test_partial_run_with_documents(self):
        """Test partial run includes citations collected from documents."""
        controller = RunController()

        run_id = controller.create_run("Test plan", 3, "test query")

        controller.run_data[run_id].documents = [
            Document(
                url="https://example.com/1",
                title="Document 1",
                content="Content 1",
            ),
            Document(
                url="https://example.com/2",
                title="Document 2",
                content="Content 2",
            ),
        ]

        controller.run_data[run_id].notes = [
            Note(
                extract_query="test",
                content="Note from doc 1",
                source_url="https://example.com/1",
            ),
            Note(
                extract_query="test",
                content="Note from doc 2",
                source_url="https://example.com/2",
            ),
        ]

        partial_run = controller.cancel(run_id)

        assert len(partial_run.completed_sections) > 0
        assert len(partial_run.citations_collected) == 2
        assert len(partial_run.notes) == 2

        section = partial_run.completed_sections[0]
        assert "cancelled" in section.content.lower()

    def test_cancel_nonexistent_run_raises_error(self):
        """Test cancelling non-existent run raises error."""
        controller = RunController()

        with pytest.raises(ValueError, match="Run .* not found"):
            controller.cancel("nonexistent-run-id")

    def test_cleanup_completed_run(self):
        """Test cleanup removes run from controller."""
        controller = RunController()

        run_id = controller.create_run("Test plan", 3)

        controller.cancel(run_id)
        controller.cleanup(run_id)

        assert run_id not in controller.active_runs
        assert run_id not in controller.run_data
