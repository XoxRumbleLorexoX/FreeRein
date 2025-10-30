"""Web tooling utilities for search and crawling."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from readability import Document

from .config import settings

HEADERS = {"User-Agent": "lam-agent-unified/0.1 (+https://github.com/)"}
MAX_CONTENT_LENGTH = 1_048_576  # 1 MB
REQUEST_TIMEOUT = 15


def web_search_ddg(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    if not settings.enable_web:
        raise RuntimeError("Web access disabled by configuration")
    results: List[Dict[str, str]] = []
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=max_results):
            if not result:
                continue
            results.append({
                "title": result.get("title", ""),
                "href": result.get("href", ""),
                "body": result.get("body", ""),
            })
    return results


def _is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
    except Exception:
        return True
    return parser.can_fetch(HEADERS["User-Agent"], url)


def fetch_url(url: str) -> Dict[str, str]:
    if not settings.enable_web:
        raise RuntimeError("Web access disabled by configuration")
    if not _is_allowed(url):
        raise PermissionError(f"Blocked by robots.txt: {url}")
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, stream=True)
    response.raise_for_status()
    content_length = int(response.headers.get("content-length", "0"))
    if content_length and content_length > MAX_CONTENT_LENGTH:
        raise ValueError("Content too large")
    content = response.content[:MAX_CONTENT_LENGTH]
    return {"url": url, "content": content.decode(response.encoding or "utf-8", errors="ignore")}


def extract_readable(html: str, url: Optional[str] = None) -> Dict[str, str]:
    document = Document(html)
    summary_html = document.summary(html_partial=True)
    soup = BeautifulSoup(summary_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    title = document.short_title()
    return {"url": url, "title": title, "text": text}


@dataclass
class CrawlConfig:
    depth: int = 1
    max_pages: int = 8
    rate_limit: float = 1.0


def crawl(urls: Iterable[str], depth: int = 1, max_pages: int = 8) -> List[Dict[str, str]]:
    if not settings.enable_web:
        raise RuntimeError("Web access disabled by configuration")
    cfg = CrawlConfig(depth=depth, max_pages=max_pages)
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque((url, 0) for url in urls)
    pages: List[Dict[str, str]] = []

    while queue and len(pages) < cfg.max_pages:
        url, level = queue.popleft()
        if url in visited or level > cfg.depth:
            continue
        visited.add(url)
        try:
            fetched = fetch_url(url)
            readable = extract_readable(fetched["content"], url)
            pages.append(readable)
        except Exception:
            continue

        if level < cfg.depth:
            soup = BeautifulSoup(fetched["content"], "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("#"):
                    continue
                if href.startswith("/"):
                    parsed = urlparse(url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                if href.startswith("http") and href not in visited:
                    queue.append((href, level + 1))
        time.sleep(cfg.rate_limit)

    return pages
