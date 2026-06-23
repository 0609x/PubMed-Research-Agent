"""Unit tests for agents/research_agent.py"""

from __future__ import annotations

import json
import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.research_agent import ResearchAgent, ResearchReport
from tools.pubmed_tool import (
    PubMedSearchTool,
    PubMedSearchResult,
    PubMedArticle,
    Author,
)
from services.literature_summary import (
    LiteratureSummarizer,
    LiteratureSummary,
    LiteratureSummaryError,
    ResearchHotspot,
    FutureDirection,
    ExperimentalMethod,
)


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

def make_articles(n: int = 3) -> list[PubMedArticle]:
    """Create n sample PubMedArticle objects."""
    return [
        PubMedArticle(
            pmid=str(10000 + i),
            title=f"Sample study {i} about SEC61G",
            abstract=f"This is the abstract of study {i}. Methods included...",
            doi=f"10.1000/test{i}",
            authors=[Author(last_name="Smith", fore_name="John")],
            journal="Journal of Test",
            publish_date="2024",
        )
        for i in range(n)
    ]


def make_search_result(query: str, n: int = 3) -> PubMedSearchResult:
    return PubMedSearchResult(
        query=query,
        total_count=n,
        articles=make_articles(n),
    )


def make_summary() -> LiteratureSummary:
    return LiteratureSummary(
        research_background="SEC61G background summary.",
        current_hotspots=[
            ResearchHotspot(
                topic="Prognostic biomarker",
                description="High SEC61G predicts poor survival.",
                evidence=["PMID:10000"],
            )
        ],
        main_findings=["Finding A", "Finding B"],
        experimental_methods=[
            ExperimentalMethod(method="IHC", purpose="Expression", frequency=2)
        ],
        future_directions=[
            FutureDirection(
                direction="Targeted therapy",
                rationale="SEC61G is a driver.",
                challenges=["Selectivity"],
            )
        ],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pubmed():
    tool = MagicMock(spec=PubMedSearchTool)
    tool.search.return_value = make_search_result("SEC61G", n=5)
    return tool


@pytest.fixture
def mock_summarizer():
    s = MagicMock(spec=LiteratureSummarizer)
    s.model = "gpt-4o-mini"
    s.summarize.return_value = make_summary()
    return s


@pytest.fixture
def agent(mock_pubmed, mock_summarizer):
    return ResearchAgent(
        pubmed=mock_pubmed,
        summarizer=mock_summarizer,
        max_articles=10,
        language="en",
    )


# ---------------------------------------------------------------------------
# ResearchReport
# ---------------------------------------------------------------------------

class TestResearchReport:
    def test_to_json(self):
        report = ResearchReport(
            query="test query",
            model_used="gpt-4o",
            status="completed",
            articles=[{"pmid": "1", "title": "T"}],
            main_findings=["Finding A"],
        )
        result = report.to_json()
        data = json.loads(result)
        assert data["query"] == "test query"
        assert data["status"] == "completed"
        assert len(data["articles"]) == 1
        assert "Finding A" in data["main_findings"]

    def test_default_values(self):
        report = ResearchReport(query="q", model_used="m")
        assert report.total_pubmed_hits == 0
        assert report.articles == []
        assert report.errors == []
        assert report.status == "pending"
        assert report.research_background == ""


# ---------------------------------------------------------------------------
# ResearchAgent
# ---------------------------------------------------------------------------

class TestResearchAgent:
    def test_happy_path(self, agent):
        report = agent.research("SEC61G in Lung Cancer")

        assert report.status == "completed"
        assert report.query == "SEC61G in Lung Cancer"
        assert report.total_pubmed_hits == 5
        assert len(report.articles) == 5
        assert report.articles[0]["pmid"] == "10000"
        assert "SEC61G background" in report.research_background
        assert len(report.current_hotspots) == 1
        assert len(report.main_findings) == 2
        assert len(report.experimental_methods) == 1
        assert len(report.future_directions) == 1
        assert report.model_used == "gpt-4o-mini"
        assert report.elapsed_seconds >= 0
        assert report.errors == []

    def test_custom_max_results(self, agent, mock_pubmed):
        report = agent.research("query", max_results=5)
        mock_pubmed.search.assert_called_once_with("query", max_results=5)

    def test_custom_language(self, agent, mock_summarizer):
        report = agent.research("query", language="zh")
        mock_summarizer.summarize.assert_called_once()
        call_kwargs = mock_summarizer.summarize.call_args
        assert call_kwargs[1]["language"] == "zh"

    def test_pubmed_failure(self, mock_summarizer):
        mock_pubmed = MagicMock(spec=PubMedSearchTool)
        mock_pubmed.search.side_effect = RuntimeError("API down")

        agent = ResearchAgent(
            pubmed=mock_pubmed,
            summarizer=mock_summarizer,
        )
        report = agent.research("query")

        assert report.status == "failed"
        assert "API down" in report.errors[0]
        assert report.total_pubmed_hits == 0
        assert report.articles == []

    def test_no_articles_found(self, agent, mock_pubmed):
        mock_pubmed.search.return_value = PubMedSearchResult(
            query="rare query",
            total_count=0,
            articles=[],
        )
        report = agent.research("rare query")

        assert report.status == "completed"
        assert report.total_pubmed_hits == 0
        assert not report.articles
        assert report.research_background == ""

    def test_summarizer_failure(self, mock_pubmed):
        mock_summarizer = MagicMock(spec=LiteratureSummarizer)
        mock_summarizer.model = "test-model"
        mock_summarizer.summarize.side_effect = LiteratureSummaryError("timeout")

        agent = ResearchAgent(
            pubmed=mock_pubmed,
            summarizer=mock_summarizer,
        )
        report = agent.research("query")

        assert report.status == "partial"
        assert report.total_pubmed_hits == 5
        assert len(report.articles) == 5
        assert "timeout" in report.errors[0]
        assert report.research_background == ""

    def test_to_json_output(self, agent):
        report = agent.research("SEC61G")
        json_str = report.to_json()

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["query"] == "SEC61G"
        assert data["status"] == "completed"
        assert "current_hotspots" in data
        assert "future_directions" in data

    def test_uses_default_max_articles(self, agent, mock_pubmed):
        report = agent.research("query")
        mock_pubmed.search.assert_called_once_with("query", max_results=10)

    def test_default_language(self, agent, mock_summarizer):
        agent.language = "zh"
        report = agent.research("query")
        call_kwargs = mock_summarizer.summarize.call_args
        assert call_kwargs[1]["language"] == "zh"
