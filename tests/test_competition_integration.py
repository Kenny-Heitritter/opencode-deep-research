"""Integration tests for competition architecture."""

import pytest
import asyncio
from src.competition import (
    ResearchWorld,
    WorldState,
    OutlineCompetition,
    QueryCompetition,
    DraftCompetition,
    effort_map,
)


class TestResearchWorld:
    """Test ResearchWorld WorldModel."""

    def test_initialize_creates_state(self):
        """Test that initialize creates a valid WorldState."""
        world = ResearchWorld()
        state = world.initialize("Test research plan", effort=3)

        assert state is not None
        assert state.plan == "Test research plan"
        assert state.effort == 3
        assert state.phase == "initialize"
        assert state.run_id is not None
        assert len(state.run_id) > 0

    def test_initialize_effort_bounds(self):
        """Test that effort is bounded to 1-5."""
        world = ResearchWorld()

        state_low = world.initialize("Plan", effort=0)
        assert state_low.effort == 1

        state_high = world.initialize("Plan", effort=10)
        assert state_high.effort == 5

    def test_update_state(self):
        """Test updating world state."""
        world = ResearchWorld()
        state = world.initialize("Plan", effort=3)

        updated = world.update_state(
            state, phase="outline", outlines=["outline1", "outline2"]
        )

        assert updated.phase == "outline"
        assert len(updated.outlines) == 2


class TestEffortMap:
    """Test effort configuration mapping."""

    def test_effort_map_valid_levels(self):
        """Test effort_map for all valid levels."""
        for level in range(1, 6):
            config = effort_map(level)

            assert config.level == level
            assert config.num_outline_candidates > 0
            assert config.outline_beam_width > 0
            assert config.num_query_candidates_per_section > 0
            assert config.query_beam_width > 0
            assert config.num_draft_candidates > 0
            assert config.draft_beam_width > 0

    def test_effort_map_scaling(self):
        """Test that higher effort increases parameters."""
        config_1 = effort_map(1)
        config_3 = effort_map(3)
        config_5 = effort_map(5)

        assert config_5.num_outline_candidates > config_3.num_outline_candidates
        assert config_3.num_outline_candidates > config_1.num_outline_candidates

        assert config_5.draft_beam_width >= config_3.draft_beam_width
        assert config_3.draft_beam_width >= config_1.draft_beam_width

    def test_effort_map_invalid_level(self):
        """Test effort_map with invalid level."""
        with pytest.raises(ValueError):
            effort_map(0)

        with pytest.raises(ValueError):
            effort_map(6)


class TestOutlineCompetition:
    """Test outline generation and competition."""

    @pytest.mark.asyncio
    async def test_generate_candidates(self):
        """Test generating multiple outline candidates."""
        competition = OutlineCompetition()
        world = ResearchWorld()
        state = world.initialize("Test research on AI safety", effort=3)

        candidates = await competition.generate_candidates(state, count=5)

        assert len(candidates) == 5
        for candidate in candidates:
            assert candidate.title is not None
            assert len(candidate.sections) > 0
            assert candidate.rationale is not None

    def test_score_candidates(self):
        """Test scoring outline candidates."""
        competition = OutlineCompetition()
        world = ResearchWorld()
        state = world.initialize("Test plan", effort=3)

        candidates = competition._generate_outline_variant(state, 0)
        candidates_list = [candidates]

        scores = competition.score(candidates_list, state)

        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    def test_beam_select(self):
        """Test beam selection of candidates."""
        from src.competition.outline import Outline

        competition = OutlineCompetition()
        candidates = [
            Outline(title="A", sections=["1", "2"], rationale="test", score=0.0),
            Outline(title="B", sections=["1"], rationale="test", score=0.0),
            Outline(title="C", sections=["1", "2", "3"], rationale="test", score=0.0),
        ]

        world = ResearchWorld()
        state = world.initialize("Plan", effort=3)
        scores = competition.score(candidates, state)

        selected = competition.beam_select(candidates, scores, width=2)

        assert len(selected) == 2
        assert all(c.title in ["A", "B", "C"] for c in selected)

    @pytest.mark.asyncio
    async def test_run_competition(self):
        """Test full outline competition pipeline."""
        competition = OutlineCompetition()
        world = ResearchWorld()
        state = world.initialize("AI research plan", effort=3)

        best_outline = await competition.run_competition(
            state, num_candidates=5, beam_width=2
        )

        assert best_outline is not None
        assert best_outline.title is not None
        assert len(best_outline.sections) > 0


class TestQueryCompetition:
    """Test query competition for research sections."""

    @pytest.mark.asyncio
    async def test_generate_candidates(self):
        """Test generating query candidates for a section."""
        competition = QueryCompetition()
        world = ResearchWorld()
        state = world.initialize("Test plan", effort=3)

        candidates = await competition.generate_candidates(
            state, section="Introduction", count=4
        )

        assert len(candidates) == 4
        for candidate in candidates:
            assert candidate.question is not None
            assert candidate.search_query is not None
            assert len(candidate.expected_insights) > 0

    def test_score_candidates(self):
        """Test scoring query candidates."""
        competition = QueryCompetition()
        world = ResearchWorld()
        state = world.initialize("Plan", effort=3)

        candidates = competition._generate_query_variant(state, "Section", 0)
        candidates_list = [candidates]

        scores = competition.score(candidates_list, state)

        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    def test_beam_select(self):
        """Test beam selection of queries."""
        competition = QueryCompetition()
        world = ResearchWorld()
        state = world.initialize("Plan", effort=3)

        candidates = [
            competition._generate_query_variant(state, "Section", i) for i in range(4)
        ]
        scores = competition.score(candidates, state)

        selected = competition.beam_select(candidates, scores, width=2)

        assert len(selected) == 2

    @pytest.mark.asyncio
    async def test_run_competition(self):
        """Test full query competition pipeline."""
        competition = QueryCompetition()
        world = ResearchWorld()
        state = world.initialize("AI research", effort=3)

        selected_queries = await competition.run_competition(
            state, section="Background", num_candidates=4, beam_width=2
        )

        assert len(selected_queries) == 2
        for query in selected_queries:
            assert query.question is not None
            assert query.search_query is not None


class TestDraftCompetition:
    """Test draft generation and competition."""

    @pytest.mark.asyncio
    async def test_generate_candidates(self):
        """Test generating multiple draft variants."""
        competition = DraftCompetition()
        world = ResearchWorld()
        state = world.initialize("Test plan", effort=3)

        candidates = await competition.generate_candidates(state, count=3)

        assert len(candidates) == 3
        for draft in candidates:
            assert draft.title is not None
            assert len(draft.sections) > 0
            assert draft.tone is not None

    @pytest.mark.asyncio
    async def test_score_candidates(self):
        """Test scoring draft candidates."""
        competition = DraftCompetition()
        world = ResearchWorld()
        state = world.initialize("Plan", effort=3)

        draft = competition._generate_draft_variant(state, 0)
        scores = competition.score([draft], state)

        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    @pytest.mark.asyncio
    async def test_beam_select(self):
        """Test beam selection of drafts."""
        competition = DraftCompetition()
        world = ResearchWorld()
        state = world.initialize("Plan", effort=3)

        drafts = [competition._generate_draft_variant(state, i) for i in range(3)]
        scores = competition.score(drafts, state)

        selected = competition.beam_select(drafts, scores, width=2)

        assert len(selected) == 2

    @pytest.mark.asyncio
    async def test_run_competition(self):
        """Test full draft competition pipeline."""
        competition = DraftCompetition()
        world = ResearchWorld()
        state = world.initialize("AI research", effort=3)

        best_draft = await competition.run_competition(
            state, num_candidates=3, beam_width=2
        )

        assert best_draft is not None
        assert best_draft.title is not None
        assert len(best_draft.sections) > 0


class TestEndToEndCompetition:
    """Test end-to-end competition pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test full competition pipeline with effort=3."""
        world = ResearchWorld()
        state = world.initialize(
            "Comprehensive research on artificial intelligence safety", effort=3
        )

        outline_comp = OutlineCompetition()
        best_outline = await outline_comp.run_competition(
            state, num_candidates=7, beam_width=3
        )

        assert best_outline is not None
        state = world.update_state(
            state, phase="outline_complete", outlines=[best_outline]
        )

        query_comp = QueryCompetition()
        for section in ["Introduction", "Background"]:
            selected_queries = await query_comp.run_competition(
                state, section=section, num_candidates=4, beam_width=2
            )
            assert len(selected_queries) > 0

        draft_comp = DraftCompetition()
        best_draft = await draft_comp.run_competition(
            state, num_candidates=4, beam_width=2
        )

        assert best_draft is not None
