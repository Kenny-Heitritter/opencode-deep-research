"""MCP tool implementations for web search, fetch, and extraction."""

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from src.models import Document, Note, SearchResult

logger = logging.getLogger(__name__)


class WebTools:
    """Web tools for searching, fetching, and extracting content."""

    def __init__(self, timeout: float = 30.0):
        """Initialize web tools.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Enter context manager."""
        self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._client:
            await self._client.aclose()

    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        """Search the web using DuckDuckGo.

        Args:
            query: Search query string
            num_results: Maximum number of results to return

        Returns:
            List of search results
        """
        if not self._client:
            raise RuntimeError("WebTools not initialized. Use async with statement.")

        logger.info(f"Searching for: {query}")

        try:
            params = {
                "q": query,
                "kl": "us-en",
            }

            response = await self._client.get(
                "https://html.duckduckgo.com/html/",
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; DeepResearch/1.0)"},
            )
            response.raise_for_status()

            results = self._parse_duckduckgo_results(response.text, num_results)
            logger.info(f"Found {len(results)} search results")
            return results

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise

    def _parse_duckduckgo_results(
        self, html: str, num_results: int
    ) -> list[SearchResult]:
        """Parse DuckDuckGo HTML search results.

        Args:
            html: HTML response from DuckDuckGo
            num_results: Maximum number of results to parse

        Returns:
            List of parsed search results
        """
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for result in soup.find_all("div", class_="result"):
            if len(results) >= num_results:
                break

            title_tag = result.find("a", class_="result__a")
            snippet_tag = result.find("a", class_="result__snippet")

            if title_tag and title_tag.get("href"):
                raw_url = title_tag.get("href", "")
                url = self._clean_duckduckgo_url(str(raw_url))
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                if url and title:
                    results.append(SearchResult(url=url, title=title, snippet=snippet))

        return results

    def _clean_duckduckgo_url(self, url: str) -> str:
        """Clean DuckDuckGo redirect URL.

        Args:
            url: DuckDuckGo redirect URL

        Returns:
            Cleaned direct URL
        """
        match = re.search(r"uddg=([^&]+)", url)
        if match:
            from urllib.parse import unquote

            return unquote(match.group(1))
        return url

    async def fetch(self, url: str) -> Document:
        """Fetch and parse content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Document with fetched content
        """
        if not self._client:
            raise RuntimeError("WebTools not initialized. Use async with statement.")

        logger.info(f"Fetching: {url}")

        try:
            response = await self._client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; DeepResearch/1.0)"},
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else url

            content = self._extract_text_content(soup)

            doc = Document(url=url, title=title_text, content=content)
            logger.info(f"Fetched {len(content)} characters from {url}")
            return doc

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted text content
        """
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    async def extract_with_jina(self, url: str, query: str) -> list[Note]:
        """Extract relevant information using Jina AI reader.

        Args:
            url: URL to extract from
            query: Extraction query/question

        Returns:
            List of extracted notes
        """
        if not self._client:
            raise RuntimeError("WebTools not initialized. Use async with statement.")

        logger.info(f"Extracting from {url} with query: {query}")

        try:
            jina_url = (
                f"https://r.jina.ai/http://{urlparse(url).netloc}{urlparse(url).path}"
            )

            response = await self._client.get(
                jina_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; DeepResearch/1.0)"},
            )
            response.raise_for_status()

            content = response.text.strip()

            if not content:
                return []

            note = Note(
                extract_query=query,
                content=content,
                source_url=url,
            )

            logger.info(f"Extracted {len(content)} characters from {url}")
            return [note]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error extracting from {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error extracting from {url}: {e}")
            return []
