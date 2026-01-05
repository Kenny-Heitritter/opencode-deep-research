"""Research mode with replay capabilities."""

import json
import logging
import uuid
from typing import Optional
from pathlib import Path

from src.models import ResearchRun, SearchResult, Document, Note
from src.research.pipeline import ResearchPipeline

logger = logging.getLogger(__name__)


class ResearchMode:
    """Research mode with deterministic replay support."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize research mode.

        Args:
            storage_dir: Directory to store run data
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(".research_runs")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def run(
        self, plan: str, effort: int, query: Optional[str] = None
    ) -> ResearchRun:
        """Run research and store results for replay.

        Args:
            plan: Research plan
            effort: Effort level
            query: Optional search query

        Returns:
            Research run results
        """
        pipeline = ResearchPipeline(effort=effort)
        run = await pipeline.run(plan, query)

        self._store_run(run)
        return run

    async def replay(self, run_id: str) -> ResearchRun:
        """Replay a previous research run with deterministic output.

        Args:
            run_id: Run ID to replay

        Returns:
            Research run with same data
        """
        run_data = self._load_run(run_id)
        if not run_data:
            raise ValueError(f"Run {run_id} not found in storage")

        logger.info(f"Replaying run {run_id}")

        replay_run = ResearchRun(
            run_id=str(uuid.uuid4()),
            plan=run_data["plan"],
            effort=run_data["effort"],
            status="replayed",
            query=run_data["query"],
            search_results=[
                SearchResult(
                    url=r["url"],
                    title=r["title"],
                    snippet=r["snippet"],
                    relevance_score=r.get("relevance_score"),
                )
                for r in run_data["search_results"]
            ],
            documents=[
                Document(
                    url=d["url"],
                    title=d["title"],
                    content=d["content"],
                )
                for d in run_data["documents"]
            ],
            notes=[
                Note(
                    extract_query=n["extract_query"],
                    content=n["content"],
                    source_url=n["source_url"],
                    span_start=n.get("span_start"),
                    span_end=n.get("span_end"),
                    relevance_score=n.get("relevance_score"),
                )
                for n in run_data["notes"]
            ],
            errors=run_data.get("errors", []),
        )

        return replay_run

    def _store_run(self, run: ResearchRun):
        """Store run data for later replay.

        Args:
            run: Research run to store
        """
        run_file = self.storage_dir / f"{run.run_id}.json"

        run_data = {
            "run_id": run.run_id,
            "plan": run.plan,
            "effort": run.effort,
            "status": run.status,
            "query": run.query,
            "search_results": [
                {
                    "url": r.url,
                    "title": r.title,
                    "snippet": r.snippet,
                    "relevance_score": r.relevance_score,
                }
                for r in run.search_results
            ],
            "documents": [
                {
                    "url": d.url,
                    "title": d.title,
                    "content": d.content,
                }
                for d in run.documents
            ],
            "notes": [
                {
                    "extract_query": n.extract_query,
                    "content": n.content,
                    "source_url": n.source_url,
                    "span_start": n.span_start,
                    "span_end": n.span_end,
                    "relevance_score": n.relevance_score,
                }
                for n in run.notes
            ],
            "errors": run.errors,
        }

        with open(run_file, "w") as f:
            json.dump(run_data, f, indent=2)

        logger.info(f"Stored run {run.run_id} to {run_file}")

    def _load_run(self, run_id: str) -> Optional[dict]:
        """Load run data from storage.

        Args:
            run_id: Run ID to load

        Returns:
            Run data dict if found
        """
        run_file = self.storage_dir / f"{run_id}.json"

        if not run_file.exists():
            return None

        with open(run_file, "r") as f:
            run_data = json.load(f)

        logger.info(f"Loaded run {run_id} from {run_file}")
        return run_data
