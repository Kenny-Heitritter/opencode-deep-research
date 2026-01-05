#!/usr/bin/env python3
"""
Web search implementation for evidence gathering

This module provides web search functionality using SerpAPI for Google search results.
Falls back to DuckDuckGo HTML scraping if SerpAPI is not available.
"""

import os
import logging
from typing import List, Optional
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from models.evidence import SearchResult

logger = logging.getLogger(__name__)


class SearchEngine:
    """Web search engine implementation"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the search engine.

        Args:
            api_key: SerpAPI key (optional, will check env var SERPAPI_KEY if not provided)
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.use_serpapi = bool(self.api_key)

        if not httpx:
            raise ImportError(
                "httpx is required for search functionality. Install with: pip install httpx"
            )

        if not self.use_serpapi:
            logger.warning(
                "No SerpAPI key found. Will use DuckDuckGo fallback. "
                "For better results, set SERPAPI_KEY environment variable."
            )

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform a web search for the given query.

        Args:
            query: Search query string
            num_results: Number of results to return (default: 10)

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If search fails
        """
        if self.use_serpapi:
            return await self._search_serpapi(query, num_results)
        else:
            return await self._search_duckduckgo(query, num_results)

    async def _search_serpapi(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using SerpAPI"""
        url = "https://serpapi.com/search"

        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google",
        }

        logger.info(f"Searching SerpAPI for: {query}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                results = []
                organic_results = data.get("organic_results", [])

                for i, result in enumerate(organic_results[:num_results], 1):
                    search_result = SearchResult(
                        url=result.get("link", ""),
                        title=result.get("title", ""),
                        snippet=result.get("snippet", ""),
                        rank=i,
                        search_query=query,
                    )
                    results.append(search_result)

                logger.info(f"Found {len(results)} results from SerpAPI")
                return results

            except httpx.HTTPStatusError as e:
                logger.error(f"SerpAPI HTTP error: {e}")
                raise Exception(
                    f"Search failed with status {e.response.status_code}: {e.response.text}"
                )
            except httpx.RequestError as e:
                logger.error(f"SerpAPI request error: {e}")
                raise Exception(f"Search request failed: {e}")
            except Exception as e:
                logger.error(f"SerpAPI error: {e}")
                raise Exception(f"Search failed: {e}")

    async def _search_duckduckgo(
        self, query: str, num_results: int
    ) -> List[SearchResult]:
        """
        Search using DuckDuckGo HTML scraping (fallback).

        This is a simple implementation that scrapes DuckDuckGo search results.
        It's less reliable than SerpAPI but works without an API key.
        """
        url = "https://html.duckduckgo.com/html/"

        params = {
            "q": query,
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        logger.info(f"Searching DuckDuckGo for: {query}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    data=params,
                    headers=headers,
                    timeout=30.0,
                    follow_redirects=True,
                )
                response.raise_for_status()

                results = self._parse_duckduckgo_html(response.text, query, num_results)
                logger.info(f"Found {len(results)} results from DuckDuckGo")
                return results

            except httpx.HTTPStatusError as e:
                logger.error(f"DuckDuckGo HTTP error: {e}")
                raise Exception(f"Search failed with status {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"DuckDuckGo request error: {e}")
                raise Exception(f"Search request failed: {e}")
            except Exception as e:
                logger.error(f"DuckDuckGo error: {e}")
                raise Exception(f"Search failed: {e}")

    def _parse_duckduckgo_html(
        self, html: str, query: str, num_results: int
    ) -> List[SearchResult]:
        """
        Parse DuckDuckGo HTML search results.

        This is a simple parser that extracts links, titles, and snippets.
        Note: This is fragile and may break if DuckDuckGo changes their HTML.
        """
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.current_result = {}
                self.in_result = False
                self.in_title = False
                self.in_snippet = False
                self.capture_data = False

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)

                if tag == "div" and attrs_dict.get("class") == "result":
                    self.in_result = True
                    self.current_result = {}

                elif self.in_result:
                    if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                        self.in_title = True
                        self.capture_data = True
                        href = attrs_dict.get("href", "")
                        if href.startswith("//duckduckgo.com/l/?uddg="):
                            import urllib.parse

                            href = urllib.parse.unquote(
                                href.split("uddg=")[1].split("&")[0]
                            )
                        self.current_result["url"] = href

                    elif tag == "a" and "result__snippet" in attrs_dict.get(
                        "class", ""
                    ):
                        self.in_snippet = True
                        self.capture_data = True

            def handle_endtag(self, tag):
                if tag == "div" and self.in_result:
                    if self.current_result.get("url") and self.current_result.get(
                        "title"
                    ):
                        self.results.append(self.current_result.copy())
                    self.in_result = False
                    self.current_result = {}

                elif tag == "a":
                    if self.in_title:
                        self.in_title = False
                        self.capture_data = False
                    if self.in_snippet:
                        self.in_snippet = False
                        self.capture_data = False

            def handle_data(self, data):
                if self.capture_data:
                    data = data.strip()
                    if data:
                        if self.in_title:
                            self.current_result["title"] = data
                        elif self.in_snippet:
                            self.current_result.setdefault("snippet", "")
                            self.current_result["snippet"] += " " + data

        parser = DDGParser()
        parser.feed(html)

        results = []
        for i, result in enumerate(parser.results[:num_results], 1):
            search_result = SearchResult(
                url=result.get("url", ""),
                title=result.get("title", ""),
                snippet=result.get("snippet", "").strip(),
                rank=i,
                search_query=query,
            )
            results.append(search_result)

        return results


async def search(query: str, num_results: int = 10) -> List[SearchResult]:
    """
    Convenience function to perform a web search.

    Args:
        query: Search query string
        num_results: Number of results to return (default: 10)

    Returns:
        List of SearchResult objects
    """
    engine = SearchEngine()
    return await engine.search(query, num_results)


async def test_search():
    """Test the search functionality"""
    logging.basicConfig(level=logging.INFO)

    results = await search("quantum computing applications", 5)

    print(f"\nFound {len(results)} results:\n")
    for result in results:
        print(f"{result.rank}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Snippet: {result.snippet[:100]}...")
        print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_search())
