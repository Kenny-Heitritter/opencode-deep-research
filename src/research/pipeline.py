"""Coordinator for search -> fetch -> extract -> notes workflow."""

import logging
import uuid
from typing import Optional

from src.models import Document, Note, ResearchRun, SearchResult
from src.mcp.tools import WebTools

logger = logging.getLogger(__name__)


class ResearchPipeline:
    """Pipeline coordinator for Deep Research workflow."""

    def __init__(self, effort: int = 3):
        """Initialize research pipeline.

        Args:
            effort: Research effort level (1-5), affects search depth and extraction
        """
        self.effort = max(1, min(5, effort))
        self.web_tools = WebTools()

    async def run(self, plan: str, query: Optional[str] = None) -> ResearchRun:
        """Execute the full research pipeline.

        Args:
            plan: Research plan or topic
            query: Optional specific search query (derived from plan if not provided)

        Returns:
            Complete ResearchRun with all collected data
        """
        run_id = str(uuid.uuid4())
        search_query = query or plan

        logger.info(f"Starting research run {run_id} with effort {self.effort}")
        logger.info(f"Query: {search_query}")

        run = ResearchRun(
            run_id=run_id,
            plan=plan,
            effort=self.effort,
            status="running",
            query=search_query,
            search_results=[],
            documents=[],
            notes=[],
            errors=[],
        )

        try:
            async with self.web_tools:
                run.search_results = await self._search_phase(run, search_query)
                run.documents = await self._fetch_phase(run)
                run.notes = await self._extract_phase(run, search_query)

            run.status = "completed"
            logger.info(f"Research run {run_id} completed successfully")

        except Exception as e:
            run.status = "failed"
            run.errors.append(str(e))
            logger.error(f"Research run {run_id} failed: {e}")

        return run

    async def _search_phase(self, run: ResearchRun, query: str) -> list[SearchResult]:
        """Execute search phase.

        Args:
            run: Research run instance
            query: Search query

        Returns:
            List of search results
        """
        num_results = self._calculate_num_results()
        logger.info(f"Search phase: querying for {num_results} results")

        try:
            results = await self.web_tools.search(query, num_results=num_results)
            logger.info(f"Found {len(results)} search results")
            return results
        except Exception as e:
            logger.error(f"Search phase failed: {e}")
            run.errors.append(f"Search failed: {str(e)}")
            return []

    def _calculate_num_results(self) -> int:
        """Calculate number of search results based on effort level.

        Returns:
            Number of search results to fetch
        """
        return 5 + (self.effort * 3)

    async def _fetch_phase(self, run: ResearchRun) -> list[Document]:
        """Execute fetch phase.

        Args:
            run: Research run instance

        Returns:
            List of fetched documents
        """
        max_fetch = self._calculate_max_fetch()
        urls_to_fetch = [r.url for r in run.search_results[:max_fetch]]

        logger.info(f"Fetch phase: fetching {len(urls_to_fetch)} documents")

        documents = []
        for url in urls_to_fetch:
            try:
                doc = await self.web_tools.fetch(url)
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                run.errors.append(f"Fetch failed for {url}: {str(e)}")

        logger.info(f"Fetched {len(documents)} documents successfully")
        return documents

    def _calculate_max_fetch(self) -> int:
        """Calculate max documents to fetch based on effort level.

        Returns:
            Maximum number of documents to fetch
        """
        return 2 + self.effort

    async def _extract_phase(self, run: ResearchRun, query: str) -> list[Note]:
        """Execute extraction phase.

        Args:
            run: Research run instance
            query: Extraction query

        Returns:
            List of extracted notes
        """
        logger.info("Extract phase: extracting relevant information")
        all_notes = []

        for doc in run.documents:
            try:
                notes = await self.web_tools.extract_with_jina(doc.url, query)
                all_notes.extend(notes)
            except Exception as e:
                logger.warning(f"Failed to extract from {doc.url}: {e}")
                run.errors.append(f"Extraction failed for {doc.url}: {str(e)}")

        logger.info(f"Extracted {len(all_notes)} notes")
        return all_notes
