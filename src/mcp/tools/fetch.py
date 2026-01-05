#!/usr/bin/env python3
"""
Document fetching implementation for evidence gathering

This module provides functionality to fetch and extract content from web pages,
supporting HTML and PDF documents.
"""

import os
import logging
from typing import Optional
from datetime import datetime
import re

try:
    import httpx
except ImportError:
    httpx = None

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from models.evidence import Document

logger = logging.getLogger(__name__)


class DocumentFetcher:
    """Fetches and processes documents from URLs"""

    def __init__(self, timeout: float = 30.0):
        """
        Initialize the document fetcher.

        Args:
            timeout: Request timeout in seconds (default: 30.0)
        """
        if not httpx:
            raise ImportError(
                "httpx is required for document fetching. Install with: pip install httpx"
            )

        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def fetch(self, url: str) -> Document:
        """
        Fetch a document from a URL.

        Args:
            url: URL to fetch

        Returns:
            Document object with extracted content

        Raises:
            Exception: If fetching or processing fails
        """
        logger.info(f"Fetching document from: {url}")

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()

                if "application/pdf" in content_type:
                    return await self._process_pdf(url, response.content)
                elif "text/html" in content_type or "text/plain" in content_type:
                    return await self._process_html(url, response.text, content_type)
                else:
                    logger.warning(
                        f"Unsupported content type: {content_type}, treating as HTML"
                    )
                    return await self._process_html(url, response.text, content_type)

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching {url}: {e}")
                raise Exception(
                    f"Failed to fetch document (HTTP {e.response.status_code}): {e}"
                )
            except httpx.RequestError as e:
                logger.error(f"Request error fetching {url}: {e}")
                raise Exception(f"Failed to fetch document: {e}")
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                raise Exception(f"Failed to process document: {e}")

    async def _process_html(self, url: str, html: str, content_type: str) -> Document:
        """
        Process HTML content and extract text.

        Args:
            url: Document URL
            html: HTML content
            content_type: Content type header value

        Returns:
            Document object
        """
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            """Extract text content from HTML"""

            def __init__(self):
                super().__init__()
                self.text = []
                self.title = ""
                self.in_title = False
                self.skip_tags = {
                    "script",
                    "style",
                    "noscript",
                    "header",
                    "footer",
                    "nav",
                }
                self.current_tag = None

            def handle_starttag(self, tag, attrs):
                self.current_tag = tag
                if tag == "title":
                    self.in_title = True

            def handle_endtag(self, tag):
                if tag == "title":
                    self.in_title = False
                if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
                    self.text.append("\n")
                self.current_tag = None

            def handle_data(self, data):
                if self.in_title:
                    self.title += data.strip() + " "
                elif self.current_tag not in self.skip_tags:
                    text = data.strip()
                    if text:
                        self.text.append(text + " ")

        extractor = TextExtractor()
        extractor.feed(html)

        title = extractor.title.strip() or self._extract_title_from_url(url)
        content = "".join(extractor.text).strip()

        content = re.sub(r"\n\s*\n", "\n\n", content)
        content = re.sub(r" +", " ", content)

        logger.info(f"Extracted {len(content)} characters from HTML")

        return Document(
            url=url,
            title=title,
            content=content,
            content_type="text/html",
            metadata={"original_content_type": content_type},
        )

    async def _process_pdf(self, url: str, pdf_content: bytes) -> Document:
        """
        Process PDF content and extract text.

        Args:
            url: Document URL
            pdf_content: PDF file content

        Returns:
            Document object
        """
        try:
            import pypdf
        except ImportError:
            logger.warning("pypdf not available, PDF support disabled")
            raise Exception(
                "PDF support requires pypdf library. Install with: pip install pypdf"
            )

        import io

        try:
            pdf_file = io.BytesIO(pdf_content)
            reader = pypdf.PdfReader(pdf_file)

            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            content = "\n\n".join(text_parts)

            metadata = reader.metadata or {}
            title = metadata.get("/Title", "") or self._extract_title_from_url(url)

            logger.info(
                f"Extracted {len(content)} characters from PDF ({len(reader.pages)} pages)"
            )

            return Document(
                url=url,
                title=title,
                content=content,
                content_type="application/pdf",
                metadata={
                    "num_pages": len(reader.pages),
                    "pdf_metadata": {k: str(v) for k, v in metadata.items()},
                },
            )

        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {e}")

    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a title from the URL if no title is found in the document.

        Args:
            url: Document URL

        Returns:
            Generated title
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        if path:
            title = path.split("/")[-1]
            title = title.replace("-", " ").replace("_", " ")
            title = re.sub(r"\.[^.]+$", "", title)
            return title.title()

        return parsed.netloc


async def fetch(url: str) -> Document:
    """
    Convenience function to fetch a document.

    Args:
        url: URL to fetch

    Returns:
        Document object
    """
    fetcher = DocumentFetcher()
    return await fetcher.fetch(url)


async def test_fetch():
    """Test the fetch functionality"""
    logging.basicConfig(level=logging.INFO)

    test_urls = [
        "https://en.wikipedia.org/wiki/Quantum_computing",
        "https://www.example.com",
    ]

    for url in test_urls:
        try:
            doc = await fetch(url)
            print(f"\nFetched: {doc.title}")
            print(f"URL: {doc.url}")
            print(f"Type: {doc.content_type}")
            print(f"Words: {doc.word_count}")
            print(f"Preview: {doc.content[:200]}...")
            print()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_fetch())
