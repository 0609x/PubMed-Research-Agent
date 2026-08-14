# -*- coding: utf-8 -*-
"""Unit tests for the /api/v1/search endpoints (pipeline wiring + persistence)."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import backend.app.models.analysis  # noqa: F401  (register tables)
import backend.app.models.article  # noqa: F401
import backend.app.models.search  # noqa: F401
from backend.app.main import app
from backend.app.models.database import Base, get_db
from backend.agents.research_agent import ResearchReport

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


class FakeAgent:
    def __init__(self, report=None, error=None):
        self.report = report
        self.error = error

    def research(
        self,
        query,
        max_results=None,
        language=None,
        search_mode="advanced",
        sort_by="relevance",
        min_year=None,
        max_year=None,
        min_impact_factor=None,
    ):
        if self.error:
            raise self.error
        return self.report


def _report() -> ResearchReport:
    return ResearchReport(
        query="SEC61G in lung cancer",
        rewritten_query="SEC61G[Title/Abstract] AND lung cancer",
        model_used="deepseek-v4-flash",
        language="en",
        total_pubmed_hits=2,
        status="completed",
        articles=[
            {
                "pmid": "100",
                "title": "SEC61G in lung cancer",
                "abstract": "We studied SEC61G.",
                "doi": "10.1/x",
                "authors": [{"last_name": "Smith", "fore_name": "J"}],
                "journal": "Cancer Res",
                "publish_date": "2024",
                "publication_type": "Journal Article",
            }
        ],
        research_background="Background text",
        current_hotspots=[{"name": "hotspot", "evidence": "evidence"}],
        main_findings=["finding"],
        experimental_methods=[{"name": "method", "papers": ["100"]}],
        future_directions=[{"topic": "topic", "rationale": "rationale"}],
    )


@pytest.fixture(autouse=True)
def _fresh_db():
    async def _reset():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_reset())

    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    asyncio.run(_reset())


def test_post_search_runs_pipeline_and_persists(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.v1.search.build_agent", lambda settings: FakeAgent(report=_report())
    )
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/search",
            json={"query": "SEC61G in lung cancer", "max_results": 20, "language": "en"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "completed"
    assert body["total_found"] == 2
    assert body["pubmed_query"] == "SEC61G[Title/Abstract] AND lung cancer"
    assert body["analysis"] is not None
    assert body["analysis"]["research_background"] == "Background text"
    assert body["analysis"]["main_findings"] == ["finding"]
    assert body["analysis"]["model_used"] == "deepseek-v4-flash"

    with TestClient(app) as client:
        detail = client.get(f"/api/v1/search/{body['id']}")
    assert detail.status_code == 200
    data = detail.json()
    assert len(data["articles"]) == 1
    assert data["articles"][0]["pmid"] == "100"
    assert data["articles"][0]["authors"] == [{"last_name": "Smith", "fore_name": "J"}]
    assert data["analysis"]["current_hotspots"] == [{"name": "hotspot", "evidence": "evidence"}]


def test_post_search_failure_marks_failed(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.v1.search.build_agent",
        lambda settings: FakeAgent(error=RuntimeError("boom")),
    )
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/search", json={"query": "SEC61G", "max_results": 5}
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "failed"
    assert "boom" in body["error_message"]


def test_history_lists_recent_searches(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.v1.search.build_agent", lambda settings: FakeAgent(report=_report())
    )
    with TestClient(app) as client:
        client.post("/api/v1/search", json={"query": "first query"})
        client.post("/api/v1/search", json={"query": "second query"})
        history = client.get("/api/v1/search/history")
    assert history.status_code == 200
    items = history.json()
    assert len(items) == 2
    assert items[0]["query_text"] == "second query"
    assert items[1]["query_text"] == "first query"
