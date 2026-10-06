"""Company interview research with graceful degradation.

1. live_web        - Claude's server-side web_search + web_fetch tools.
2. search_fallback - DuckDuckGo (ddgs) results + page extracts, summarised by Claude.
                     Used when the web search tool is disabled for the API org.
3. model_knowledge - Claude's own knowledge, explicitly labelled as such.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable

import anthropic
import httpx

from . import prompts
from .llm import ClaudeLLM, LLMError, LLMRefusal
from .plan import PrepContext

log = logging.getLogger("prep.research")

# Errors that no fallback can fix (bad key, unknown model) - surface them immediately.
FATAL_API_ERRORS = (anthropic.AuthenticationError, anthropic.NotFoundError)

LogFn = Callable[[str, str], None]
SourcesFn = Callable[[list[dict[str, str]]], int]

MODE_LABELS = {
    "live_web": "live web research",
    "search_fallback": "backup web search",
    "model_knowledge": "Claude's own knowledge (no live web access)",
    "offline": "offline knowledge base",
}


@dataclass
class ResearchResult:
    report_md: str
    mode: str
    sources: list[dict[str, str]] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)


def _host(url: str) -> str:
    match = re.match(r"https?://(?:www\.)?([^/]+)", url or "")
    return match.group(1) if match else url


async def research_company(
    llm: ClaudeLLM,
    ctx: PrepContext,
    *,
    web_search_enabled: bool,
    log_fn: LogFn,
    sources_fn: SourcesFn,
) -> ResearchResult:
    searches, fetches = ctx.targets["searches"], ctx.targets["fetches"]

    if web_search_enabled:
        async def on_event(kind: str, payload: str) -> None:
            if kind == "search":
                log_fn(f'Searching the web: "{payload}"', "search")
            elif kind == "fetch":
                log_fn(f"Reading {_host(payload)}", "fetch")
            elif kind == "results":
                log_fn(f"Got {payload}", "result")
            elif kind == "note":
                log_fn(payload, "note")
            elif kind == "error":
                log_fn(payload, "warn")

        try:
            outcome = await llm.research(
                system=prompts.RESEARCH_SYSTEM,
                prompt=prompts.research_prompt(ctx, min_searches=max(4, searches // 2), max_fetches=fetches),
                max_searches=searches,
                max_fetches=fetches,
                on_event=on_event,
            )
            sources_fn(outcome.sources)
            if outcome.successful_searches > 0 and len(outcome.text) > 200:
                return ResearchResult(outcome.text, "live_web", outcome.sources, outcome.queries)
            reason = ", ".join(sorted(set(outcome.search_errors))) or "no usable results"
            log_fn(f"Live web search unavailable ({reason}) - switching to the backup search engine.", "warn")
        except (LLMRefusal, *FATAL_API_ERRORS):
            raise
        except (anthropic.APIStatusError, anthropic.APIConnectionError, LLMError) as exc:
            status = getattr(exc, "status_code", None)
            detail = f" (HTTP {status})" if status else ""
            log_fn(f"Claude web search failed{detail} - switching to the backup search engine.", "warn")
            log.warning("web search research failed: %s", exc)

    try:
        fallback = await _search_fallback(llm, ctx, log_fn)
        if fallback is not None:
            sources_fn(fallback.sources)
            return fallback
    except (LLMRefusal, *FATAL_API_ERRORS):
        raise
    except Exception as exc:  # network blocked, rate limited, parsing failures...
        log.warning("search fallback failed: %s", exc)
        log_fn("Backup web search is unavailable from this network.", "warn")

    log_fn("Falling back to Claude's own knowledge of the company (no live web data).", "warn")
    report = await llm.generate_text(
        system=prompts.RESEARCH_SYSTEM,
        content=prompts.KNOWLEDGE_FALLBACK_TASK.format(
            company=ctx.company, role=ctx.role_or_default, years=ctx.years_label, band=ctx.band
        ),
        max_tokens=12000,
    )
    return ResearchResult(report, "model_knowledge")


# --------------------------------------------------------------------- fallback
def fallback_queries(ctx: PrepContext) -> list[str]:
    role = ctx.role or "interview"
    company = ctx.company
    return [
        f"{company} {role} interview questions",
        f"{company} {role} interview experience",
        f"{company} interview process rounds",
        f"{company} interview questions glassdoor ambitionbox",
        f"{company} interview experience geeksforgeeks",
    ]


def _ddgs_search(queries: list[str], per_query: int) -> list[dict[str, str]]:
    from ddgs import DDGS

    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    engine = DDGS(timeout=12)
    errors = 0
    for query in queries:
        try:
            results = engine.text(query, max_results=per_query) or []
        except Exception as exc:
            errors += 1
            log.info("ddgs query failed (%s): %s", query, exc)
            continue
        for result in results:
            url = result.get("href") or result.get("url") or ""
            if not url or url in seen:
                continue
            seen.add(url)
            hits.append({"query": query, "title": result.get("title", ""), "url": url, "snippet": result.get("body", "")})
    if not hits and errors:
        raise RuntimeError("all backup search queries failed")
    return hits


def _page_text(html: str, limit: int) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "form", "svg", "aside"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"\n\s*\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()[:limit]


async def _fetch_pages(urls: list[str], limit_chars: int = 6000) -> dict[str, str]:
    headers = {"User-Agent": "Mozilla/5.0 (InstantInterviewPrep research bot)"}
    pages: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:

        async def fetch(url: str) -> None:
            try:
                response = await client.get(url)
                if response.status_code == 200 and "html" in response.headers.get("content-type", ""):
                    pages[url] = await asyncio.to_thread(_page_text, response.text[:1_500_000], limit_chars)
            except Exception as exc:
                log.info("fetch failed %s: %s", url, exc)

        await asyncio.gather(*(fetch(u) for u in urls))
    return pages


_PRIORITY_HOSTS = ("geeksforgeeks", "glassdoor", "ambitionbox", "leetcode", "reddit", "medium", "naukri", "interviewbit")


async def _search_fallback(llm: ClaudeLLM, ctx: PrepContext, log_fn: LogFn) -> ResearchResult | None:
    queries = fallback_queries(ctx)
    for q in queries:
        log_fn(f'Backup search: "{q}"', "search")
    hits = await asyncio.to_thread(_ddgs_search, queries, 8)
    if not hits:
        return None
    log_fn(f"Backup search found {len(hits)} results", "result")

    ranked = sorted(hits, key=lambda h: 0 if any(p in h["url"] for p in _PRIORITY_HOSTS) else 1)
    to_read = [h["url"] for h in ranked[: ctx.targets["fetches"] + 2]]
    for url in to_read:
        log_fn(f"Reading {_host(url)}", "fetch")
    pages = await _fetch_pages(to_read)

    material_parts = []
    for hit in hits[:40]:
        material_parts.append(f"[{hit['title']}]({hit['url']})\n{hit['snippet']}")
    for url, text in pages.items():
        if text:
            material_parts.append(f"<page url=\"{url}\">\n{text}\n</page>")
    report = await llm.generate_text(
        system=prompts.RESEARCH_SYSTEM,
        content=prompts.SEARCH_FALLBACK_TASK.format(
            company=ctx.company,
            role=ctx.role_or_default,
            years=ctx.years_label,
            band=ctx.band,
            material="\n\n".join(material_parts),
        ),
        max_tokens=16000,
    )
    sources = [{"url": h["url"], "title": h["title"] or h["url"]} for h in hits[:30]]
    return ResearchResult(report, "search_fallback", sources, queries)


def research_summary(result: ResearchResult) -> dict[str, Any]:
    return {"mode": result.mode, "label": MODE_LABELS.get(result.mode, result.mode), "sources": len(result.sources)}
