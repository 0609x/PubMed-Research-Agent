"""
Literature Summary Service

Uses OpenAI-compatible LLM APIs to analyze multiple PubMed abstracts
and produce structured research summaries.

Supported model providers (any OpenAI-compatible endpoint):
- OpenAI GPT (gpt-4o, gpt-4o-mini, ...)
- Qwen (via DashScope / vLLM)
- DeepSeek (deepseek-chat, deepseek-reasoner)
- Any local vLLM / Ollama endpoint

Usage:
    summarizer = LiteratureSummarizer(
        api_base="https://api.openai.com/v1",
        api_key="sk-...",
        model="gpt-4o",
    )
    result = summarizer.summarize(articles, language="zh")
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------

class ResearchHotspot(BaseModel):
    topic: str = Field(description="Name of the research hotspot")
    description: str = Field(description="Brief description of this hotspot")
    evidence: list[str] = Field(default_factory=list)


class FutureDirection(BaseModel):
    direction: str = Field(description="Proposed future research direction")
    rationale: str = Field(description="Why this direction is promising")
    challenges: list[str] = Field(default_factory=list)


class ExperimentalMethod(BaseModel):
    method: str = Field(description="Name of the method")
    purpose: str = Field(description="What this method was used for")
    frequency: int = Field(default=0)


class LiteratureSummary(BaseModel):
    research_background: str = Field(description="Comprehensive research background (2-3 paragraphs)")
    current_hotspots: list[ResearchHotspot] = Field(description="Top 3-5 current research hotspots")
    main_findings: list[str] = Field(description="Key findings across the reviewed literature (5-8 bullet points)")
    experimental_methods: list[ExperimentalMethod] = Field(description="Experimental validation methods identified")
    future_directions: list[FutureDirection] = Field(description="3-5 future research directions")
    model_used: str = Field(default="")
    token_usage: dict = Field(default_factory=dict)
    elapsed_seconds: float = Field(default=0.0)


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an expert biomedical research analyst. Your task is to analyze "
    "a set of PubMed abstracts and produce a structured literature summary.\n\n"
    "Follow these rules strictly:\n"
    "1. Base all analysis ONLY on the provided abstracts. Do not fabricate.\n"
    "2. Output valid JSON matching the specified schema exactly.\n"
    "3. If information for a field is not found, use an empty string/list.\n"
    "4. Cite PMIDs when referencing specific findings.\n"
    "5. Write in {language}."
)

USER_PROMPT_TEMPLATE = (
    "Analyze the following {count} PubMed abstracts and produce a structured "
    "literature summary.\n\n"
    "Return a JSON object with:\n"
    '- "research_background": string (2-3 paragraphs)\n'
    '- "current_hotspots": [{{"topic": "string", "description": "string", "evidence": ["PMID:..."]}}]\n'
    '- "main_findings": ["string", ...]\n'
    '- "experimental_methods": [{{"method": "string", "purpose": "string", "frequency": int}}]\n'
    '- "future_directions": [{{"direction": "string", "rationale": "string", "challenges": ["string"]}}]\n\n'
    "ABSTRACTS:\n{articles_text}"
)


# ---------------------------------------------------------------------------
# Model Presets
# ---------------------------------------------------------------------------

MODEL_PRESETS: dict[str, dict] = {
    "gpt-4o": {
        "api_base": "https://api.openai.com/v1",
        "description": "OpenAI GPT-4o",
    },
    "gpt-4o-mini": {
        "api_base": "https://api.openai.com/v1",
        "description": "OpenAI GPT-4o Mini",
    },
    "deepseek-chat": {
        "api_base": "https://api.deepseek.com/v1",
        "description": "DeepSeek V3 Chat",
    },
    "deepseek-reasoner": {
        "api_base": "https://api.deepseek.com/v1",
        "description": "DeepSeek R1 Reasoner",
    },
    "qwen-turbo": {
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "description": "Qwen Turbo",
    },
    "qwen-plus": {
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "description": "Qwen Plus",
    },
    "qwen-max": {
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "description": "Qwen Max",
    },
}


# ---------------------------------------------------------------------------
# LiteratureSummarizer
# ---------------------------------------------------------------------------

class LiteratureSummarizer:
    """Summarize PubMed abstracts using OpenAI-compatible LLM APIs."""

    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float = 120.0,
        verify_ssl: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("API key is required.")

        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.Client] = None

        logger.info(
            "LiteratureSummarizer initialized (model=%s, base=%s)",
            model, api_base,
        )

    @classmethod
    def from_preset(
        cls,
        model: str,
        api_key: str,
        api_base: Optional[str] = None,
        **kwargs,
    ) -> "LiteratureSummarizer":
        preset = MODEL_PRESETS.get(model)
        if preset is None:
            raise ValueError(
                f"Unknown model preset: {model}. "
                f"Available: {list(MODEL_PRESETS.keys())}"
            )
        base = api_base or preset["api_base"]
        return cls(api_base=base, api_key=api_key, model=model, **kwargs)

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout),
                verify=self.verify_ssl,
            )
        return self._client

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def summarize(
        self,
        articles: list[dict],
        language: str = "en",
    ) -> LiteratureSummary:
        if not articles:
            raise ValueError("At least one article is required.")

        start_time = time.perf_counter()
        logger.info("Summarizing %d articles (language=%s)", len(articles), language)

        articles_text = self._format_articles(articles)
        system_prompt = SYSTEM_PROMPT.format(language=language)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            count=len(articles),
            articles_text=articles_text,
        )

        raw_json = self._call_llm(system_prompt, user_prompt)

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM JSON: %s", exc)
            raw_fixed = self._repair_json(raw_json)
            try:
                data = json.loads(raw_fixed)
                logger.info("JSON repaired successfully")
            except json.JSONDecodeError:
                raise LiteratureSummaryError(
                    f"LLM returned invalid JSON: {exc}"
                ) from exc

        summary = LiteratureSummary(**data)
        summary.model_used = self.model
        elapsed = time.perf_counter() - start_time
        summary.elapsed_seconds = round(elapsed, 3)

        logger.info(
            "Summary completed in %.2fs (hotspots=%d, findings=%d, directions=%d)",
            elapsed,
            len(summary.current_hotspots),
            len(summary.main_findings),
            len(summary.future_directions),
        )

        return summary

    # ----------------------------------------------------------------
    # Internal
    # ----------------------------------------------------------------

    def _format_articles(self, articles: list[dict]) -> str:
        blocks = []
        for i, art in enumerate(articles, 1):
            pmid = art.get("pmid", f"UNKNOWN_{i}")
            title = art.get("title", "")
            abstract = art.get("abstract", "")
            if len(abstract) > 1500:
                abstract = abstract[:1500] + "..."
            blocks.append(
                f"[{i}] PMID:{pmid}\n"
                f"Title: {title}\n"
                f"Abstract: {abstract}\n"
            )
        return "\n".join(blocks)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("LLM API HTTP error: %s", exc.response.text[:500])
            raise LiteratureSummaryError(
                f"LLM API returned {exc.response.status_code}: "
                f"{exc.response.text[:300]}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("LLM API request error: %s", exc)
            raise LiteratureSummaryError(
                f"LLM API request failed: {exc}"
            ) from exc

        choices = body.get("choices", [])
        if not choices:
            raise LiteratureSummaryError("LLM returned empty choices.")
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise LiteratureSummaryError("LLM returned empty content.")
        return content.strip()

    @staticmethod
    def _repair_json(raw: str) -> str:
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw.strip())
        raw = re.sub(r",(\s*[}\]])", r"\1", raw)
        return raw


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class LiteratureSummaryError(Exception):
    """Raised when literature summarization fails."""
