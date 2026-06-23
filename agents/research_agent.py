"""
ResearchAgent

Orchestrates the full research workflow:
  User Query -> PubMed Search -> Article Fetch -> LLM Summary -> JSON Report

Usage:
    from tools.pubmed_tool import PubMedSearchTool
    from services.literature_summary import LiteratureSummarizer
    from agents.research_agent import ResearchAgent

    pubmed = PubMedSearchTool(email="...", verify_ssl=False)
    summarizer = LiteratureSummarizer(
        api_base="https://api.openai.com/v1",
        api_key="sk-...",
        model="gpt-4o",
    )
    agent = ResearchAgent(pubmed=pubmed, summarizer=summarizer)
    report = agent.research("SEC61G in Lung Cancer")
    print(report.to_json())
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from pydantic import BaseModel, Field

from tools.pubmed_tool import PubMedSearchTool, PubMedSearchResult
from services.literature_summary import (
    LiteratureSummarizer,
    LiteratureSummary,
    LiteratureSummaryError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output Models
# ---------------------------------------------------------------------------

class ResearchReport(BaseModel):
    """Final structured report from a research query."""

    # Metadata
    query: str = Field(description="Original user research question")
    model_used: str = Field(description="LLM model used for summarization")
    language: str = Field(default="en", description="Output language")
    elapsed_seconds: float = Field(
        default=0.0,
        description="Total wall-clock time for the full workflow",
    )

    # Search results
    total_pubmed_hits: int = Field(
        default=0,
        description="Number of articles returned by PubMed",
    )
    articles: list[dict] = Field(
        default_factory=list,
        description="Fetched articles (pmid, title, abstract, doi, etc.)",
    )

    # Literature analysis
    research_background: str = Field(default="")
    current_hotspots: list[dict] = Field(default_factory=list)
    main_findings: list[str] = Field(default_factory=list)
    experimental_methods: list[dict] = Field(default_factory=list)
    future_directions: list[dict] = Field(default_factory=list)

    # Errors
    errors: list[str] = Field(
        default_factory=list,
        description="Non-fatal errors encountered during the workflow",
    )
    status: str = Field(
        default="pending",
        description="Workflow status: pending|running|completed|partial|failed",
    )

    def to_json(self, indent: int = 2) -> str:
        """Serialize the report to a pretty-printed JSON string."""
        import json
        return json.dumps(
            self.model_dump(),
            indent=indent,
            ensure_ascii=False,
        )


# ---------------------------------------------------------------------------
# ResearchAgent
# ---------------------------------------------------------------------------

class ResearchAgent:
    """End-to-end research agent for PubMed literature analysis.

    Workflow:
        1. PubMed Search  - search for articles matching the query
        2. LLM Summary    - analyze and summarize the retrieved abstracts
        3. Report         - assemble a structured JSON report

    Parameters
    ----------
    pubmed : PubMedSearchTool
        Configured PubMed search tool instance.
    summarizer : LiteratureSummarizer
        Configured LLM summarizer instance.
    max_articles : int
        Default max articles to fetch per query (1-100).
    language : str
        Default output language ("en" or "zh").
    """

    def __init__(
        self,
        pubmed: PubMedSearchTool,
        summarizer: LiteratureSummarizer,
        max_articles: int = 20,
        language: str = "en",
    ) -> None:
        self.pubmed = pubmed
        self.summarizer = summarizer
        self.max_articles = max_articles
        self.language = language

        logger.info(
            "ResearchAgent initialized (max_articles=%d, language=%s, model=%s)",
            max_articles,
            language,
            summarizer.model,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def research(
        self,
        query: str,
        max_results: Optional[int] = None,
        language: Optional[str] = None,
    ) -> ResearchReport:
        """Execute the full research workflow.

        Parameters
        ----------
        query : str
            The research question (e.g. "SEC61G in Lung Cancer").
        max_results : int, optional
            Override the default max articles to fetch.
        language : str, optional
            Override the default output language.

        Returns
        -------
        ResearchReport
            Structured JSON-serializable report.
        """
        start_time = time.perf_counter()
        max_n = max_results or self.max_articles
        lang = language or self.language

        logger.info("Research started: query=%r, max=%d, lang=%s", query, max_n, lang)

        report = ResearchReport(
            query=query,
            model_used=self.summarizer.model,
            language=lang,
            status="running",
        )

        # --- Step 1: PubMed Search ---
        logger.info("[Step 1/3] Searching PubMed...")
        search_result = self._safe_search(query, max_n, report)

        if not search_result or not search_result.articles:
            if report.status != "failed":
                report.status = "completed"
            report.elapsed_seconds = round(time.perf_counter() - start_time, 3)
            logger.warning(
                "No articles found for query=%r (%.2fs)",
                query,
                report.elapsed_seconds,
            )
            return report

        report.total_pubmed_hits = search_result.total_count
        report.articles = [art.to_dict() for art in search_result.articles]

        # --- Step 2: LLM Summary ---
        logger.info("[Step 2/3] Summarizing %d articles...", len(report.articles))
        summary = self._safe_summarize(report.articles, lang, report)

        if summary:
            self._merge_summary(report, summary)
            report.status = "completed"
        else:
            report.status = "partial"

        # --- Finalize ---
        report.elapsed_seconds = round(time.perf_counter() - start_time, 3)
        logger.info(
            "Research completed: status=%s, articles=%d, %.2fs",
            report.status,
            report.total_pubmed_hits,
            report.elapsed_seconds,
        )

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_search(
        self,
        query: str,
        max_n: int,
        report: ResearchReport,
    ) -> Optional[PubMedSearchResult]:
        """Run PubMed search, capturing errors into the report."""
        try:
            return self.pubmed.search(query, max_results=max_n)
        except Exception as exc:
            msg = f"PubMed search failed: {exc}"
            logger.error(msg)
            report.errors.append(msg)
            report.status = "failed"
            return None

    def _safe_summarize(
        self,
        articles: list[dict],
        language: str,
        report: ResearchReport,
    ) -> Optional[LiteratureSummary]:
        """Run LLM summarization, capturing errors into the report."""
        try:
            return self.summarizer.summarize(articles, language=language)
        except LiteratureSummaryError as exc:
            msg = f"LLM summarization failed: {exc}"
            logger.error(msg)
            report.errors.append(msg)
            return None
        except Exception as exc:
            msg = f"LLM summarization unexpected error: {exc}"
            logger.error(msg)
            report.errors.append(msg)
            return None

    @staticmethod
    def _merge_summary(report: ResearchReport, summary: LiteratureSummary) -> None:
        """Merge LiteratureSummary fields into the ResearchReport."""
        report.research_background = summary.research_background
        report.main_findings = summary.main_findings
        report.current_hotspots = [
            h.model_dump() for h in summary.current_hotspots
        ]
        report.experimental_methods = [
            m.model_dump() for m in summary.experimental_methods
        ]
        report.future_directions = [
            d.model_dump() for d in summary.future_directions
        ]
        report.model_used = summary.model_used or report.model_used
