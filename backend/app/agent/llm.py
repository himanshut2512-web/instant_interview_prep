"""Async wrapper around the Anthropic SDK used by the prep agent.

* Every request is streamed (long outputs, no HTTP timeouts) and limited by a
  semaphore so parallel generation respects PREP_MAX_CONCURRENCY.
* Structured outputs (output_config.format) give us schema-valid JSON.
* Server-side refusal fallbacks (fallbacks="default") are opted into by
  default; if the account/proxy rejects the beta we retry without it.
* Company research uses Claude's server-side web_search / web_fetch tools and
  reports each search, fetched page and progress note as it happens.
"""

from __future__ import annotations

import base64
import inspect
import json
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import anthropic

from ..config import Settings

log = logging.getLogger("prep.llm")

FALLBACK_BETA = "server-side-fallback-2026-07-01"
PROGRESS_UPDATES_BETA = "thinking-display-updates-2026-08-18"
_OPTIONAL_KEYS = ("betas", "fallbacks", "thinking")

# Models that support adaptive thinking, effort and the dynamic-filtering web tools.
_MODERN_MARKERS = ("opus-5", "opus-4-8", "opus-4-7", "opus-4-6", "sonnet-5", "sonnet-4-6", "fable", "mythos")

EventCallback = Callable[[str, str], Awaitable[None] | None]


def is_modern_model(model: str) -> bool:
    lowered = model.lower()
    return any(marker in lowered for marker in _MODERN_MARKERS)


class LLMError(RuntimeError):
    """A Claude call failed in a way the pipeline can report and recover from."""


class LLMRefusal(LLMError):
    pass


class LLMTruncated(LLMError):
    pass


@dataclass
class ResearchOutcome:
    text: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    successful_searches: int = 0
    search_errors: list[str] = field(default_factory=list)


async def _maybe_await(value: Any) -> None:
    if inspect.isawaitable(value):
        await value


def _short(exc: Exception, limit: int = 240) -> str:
    text = getattr(exc, "message", None) or str(exc)
    return text if len(text) <= limit else text[:limit] + "…"


class ClaudeLLM:
    def __init__(self, settings: Settings, client: Any | None = None):
        self.settings = settings
        self.model = settings.model
        self.modern = is_modern_model(self.model)
        self.client = client or anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key, max_retries=4, timeout=900.0
        )
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)
        self._fallbacks = settings.enable_fallbacks and self.modern
        self._progress_updates = self.modern

    # ------------------------------------------------------------- plumbing
    def _params(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        effort: str | None = None,
        json_schema: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        progress_updates: bool = False,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        output_config: dict[str, Any] = {}
        if self.modern:
            output_config["effort"] = effort or self.settings.effort
        if json_schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": json_schema}
        if output_config:
            params["output_config"] = output_config
        if tools:
            params["tools"] = tools
        betas: list[str] = []
        if self._fallbacks:
            betas.append(FALLBACK_BETA)
            params["fallbacks"] = "default"
        if progress_updates and self._progress_updates:
            betas.append(PROGRESS_UPDATES_BETA)
            params["thinking"] = {"type": "adaptive", "display": "updates"}
        if betas:
            params["betas"] = betas
        return params

    async def _stream(self, params: dict[str, Any], on_block: Callable[[Any], Any] | None = None) -> Any:
        try:
            return await self._consume(params, on_block)
        except anthropic.BadRequestError as exc:
            if "betas" not in params:
                raise
            plain = {k: v for k, v in params.items() if k not in _OPTIONAL_KEYS}
            # If the plain request fails too, the 400 had another cause - keep the betas for later calls.
            message = await self._consume(plain, on_block)
            log.warning("Claude rejected an optional beta feature (%s); continuing without it.", _short(exc))
            self._fallbacks = False
            self._progress_updates = False
            return message

    async def _consume(self, params: dict[str, Any], on_block: Callable[[Any], Any] | None) -> Any:
        async with self.client.beta.messages.stream(**params) as stream:
            if on_block is not None:
                async for event in stream:
                    if event.type == "content_block_stop":
                        try:
                            await _maybe_await(on_block(event.content_block))
                        except Exception:  # progress reporting must never break the call
                            log.exception("on_block callback failed")
            return await stream.get_final_message()

    @staticmethod
    def _text(message: Any) -> str:
        return "".join(getattr(b, "text", "") for b in message.content if getattr(b, "type", "") == "text").strip()

    @staticmethod
    def _raise_for_stop(message: Any) -> None:
        if message.stop_reason == "refusal":
            details = getattr(message, "stop_details", None)
            category = getattr(details, "category", None) if details is not None else None
            suffix = f" (category: {category})" if category else ""
            raise LLMRefusal(f"Claude declined this request{suffix}.")
        if message.stop_reason == "max_tokens":
            raise LLMTruncated("Claude's answer was cut off by the max_tokens limit.")

    # ------------------------------------------------------------ requests
    async def generate_json(
        self,
        *,
        system: str,
        context_blocks: list[dict[str, Any]],
        task: str,
        schema: dict[str, Any],
        max_tokens: int = 32000,
        effort: str | None = None,
    ) -> dict[str, Any]:
        content = [*context_blocks, {"type": "text", "text": task}]
        params = self._params(
            system=system,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
            effort=effort,
            json_schema=schema,
        )
        async with self._semaphore:
            message = await self._stream(params)
        self._raise_for_stop(message)
        text = self._text(message)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Claude returned invalid JSON ({exc.msg}).") from exc
        if not isinstance(data, dict):
            raise LLMError("Claude returned JSON that is not an object.")
        return data

    async def generate_text(
        self,
        *,
        system: str,
        content: str | list[dict[str, Any]],
        max_tokens: int = 16000,
        effort: str | None = None,
    ) -> str:
        params = self._params(
            system=system,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
            effort=effort,
        )
        async with self._semaphore:
            message = await self._stream(params)
        if message.stop_reason == "refusal":
            self._raise_for_stop(message)
        text = self._text(message)
        if not text:
            raise LLMError("Claude returned an empty answer.")
        return text

    async def transcribe_pdf(self, data: bytes) -> str:
        """Read a scanned/image-only PDF with Claude's PDF support."""
        content = [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(data).decode("ascii"),
                },
            },
            {
                "type": "text",
                "text": "Transcribe this document (a resume or job description) to plain text. Keep section "
                "headings, bullet points, dates, employers, skills and metrics. Output only the transcription.",
            },
        ]
        return await self.generate_text(
            system="You are a precise document transcriber.", content=content, max_tokens=16000, effort="low"
        )

    async def research(
        self,
        *,
        system: str,
        prompt: str,
        max_searches: int,
        max_fetches: int,
        on_event: EventCallback | None = None,
        max_continuations: int = 6,
    ) -> ResearchOutcome:
        """Let Claude search and read the web, then write a research report."""
        if self.modern:
            tools: list[dict[str, Any]] = [
                {"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches},
                {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": max_fetches},
            ]
        else:
            tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": max_searches}]

        outcome = ResearchOutcome()
        seen: set[str] = set()

        async def emit(kind: str, payload: str) -> None:
            if on_event is not None:
                await _maybe_await(on_event(kind, payload))

        def add_source(url: str | None, title: str | None) -> bool:
            if not url or url in seen:
                return False
            seen.add(url)
            outcome.sources.append({"url": url, "title": (title or url).strip()})
            return True

        async def on_block(block: Any) -> None:
            kind = getattr(block, "type", "")
            if kind == "server_tool_use":
                name = getattr(block, "name", "")
                tool_input = getattr(block, "input", None) or {}
                if name == "web_search" and tool_input.get("query"):
                    outcome.queries.append(str(tool_input["query"]))
                    await emit("search", str(tool_input["query"]))
                elif name == "web_fetch" and tool_input.get("url"):
                    await emit("fetch", str(tool_input["url"]))
            elif kind == "web_search_tool_result":
                content = getattr(block, "content", None)
                if isinstance(content, list):
                    outcome.successful_searches += 1
                    added = sum(add_source(getattr(r, "url", None), getattr(r, "title", None)) for r in content)
                    await emit("results", f"{len(content)} results ({added} new sources)")
                else:
                    code = str(getattr(content, "error_code", "unknown_error"))
                    outcome.search_errors.append(code)
                    await emit("error", f"web search error: {code}")
            elif kind == "web_fetch_tool_result":
                content = getattr(block, "content", None)
                if getattr(content, "type", "") == "web_fetch_result":
                    url = getattr(content, "url", None)
                    document = getattr(content, "content", None)
                    add_source(url, getattr(document, "title", None))
                    await emit("fetched", str(url))
                else:
                    await emit("error", f"page fetch failed: {getattr(content, 'error_code', 'unknown_error')}")
            elif kind == "thinking":
                note = (getattr(block, "thinking", "") or "").strip()
                if note:
                    await emit("note", note)
            elif kind == "text":
                for citation in getattr(block, "citations", None) or []:
                    add_source(getattr(citation, "url", None), getattr(citation, "title", None))

        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        final = None
        for _ in range(max_continuations):
            params = self._params(
                system=system,
                messages=messages,
                max_tokens=32000,
                effort=self.settings.research_effort,
                tools=tools,
                progress_updates=True,
            )
            async with self._semaphore:
                final = await self._stream(params, on_block=on_block)
            if final.stop_reason != "pause_turn":
                break
            # Long server-tool turn paused: append it and send again to resume.
            messages = [*messages, {"role": "assistant", "content": final.content}]
            await emit("note", "Still researching - continuing the search session…")

        if final is None:
            raise LLMError("Research produced no response.")
        if final.stop_reason == "refusal":
            self._raise_for_stop(final)
        outcome.text = self._text(final)
        if final.stop_reason == "pause_turn" and not outcome.text:
            raise LLMError("Research did not finish within the continuation limit.")
        return outcome
