# -*- coding: utf-8 -*-
"""Unit tests for the /api/v1/graph endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


class FakeGraphStore:
    def __init__(self, ready=True, stats=None, related=None, error=False):
        self._ready = ready
        self._stats = stats or {"papers": 4, "authors": 6, "journals": 3}
        self._related = related or [
            {"pmid": "200", "title": "Other paper", "overlap": 2}
        ]
        self._error = error

    def is_ready(self):
        ready, _ = self.diagnose()
        return ready

    def diagnose(self):
        if self._error:
            raise RuntimeError("boom")
        return self._ready, ("" if self._ready else "unreachable")

    def stats(self):
        if self._error:
            raise RuntimeError("boom")
        return dict(self._stats)

    def related_papers(self, pmid, limit):
        if self._error:
            raise RuntimeError("boom")
        return [dict(r) for r in self._related]

    def subgraph(self, pmid, limit):
        if self._error:
            raise RuntimeError("boom")
        return {
            "pmid": pmid,
            "nodes": [
                {"id": f"paper:{pmid}", "type": "paper", "label": "Center", "pmid": pmid},
                {"id": "author:Wang", "type": "author", "label": "Wang", "pmid": ""},
            ],
            "links": [
                {"source": f"paper:{pmid}", "target": "author:Wang", "type": "AUTHORED"}
            ],
        }


def test_stats_returns_counts(monkeypatch):
    monkeypatch.setattr("backend.app.api.v1.graph.get_graph_store", lambda: FakeGraphStore())
    with TestClient(app) as client:
        resp = client.get("/api/v1/graph/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["papers"] == 4
    assert body["authors"] == 6
    assert body["journals"] == 3


def test_stats_when_store_unconfigured(monkeypatch):
    monkeypatch.setattr("backend.app.api.v1.graph.get_graph_store", lambda: None)
    with TestClient(app) as client:
        resp = client.get("/api/v1/graph/stats")
    assert resp.status_code == 200
    assert resp.json()["ready"] is False
    assert "not configured" in resp.json()["error"]


def test_related_papers_returns_rows(monkeypatch):
    monkeypatch.setattr("backend.app.api.v1.graph.get_graph_store", lambda: FakeGraphStore())
    with TestClient(app) as client:
        resp = client.get("/api/v1/graph/related/100")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pmid"] == "100"
    assert body["related"][0]["pmid"] == "200"
    assert body["related"][0]["overlap"] == 2


def test_related_papers_when_store_unconfigured(monkeypatch):
    monkeypatch.setattr("backend.app.api.v1.graph.get_graph_store", lambda: None)
    with TestClient(app) as client:
        resp = client.get("/api/v1/graph/related/100")
    assert resp.status_code == 503


def test_subgraph_returns_nodes_and_links(monkeypatch):
    monkeypatch.setattr("backend.app.api.v1.graph.get_graph_store", lambda: FakeGraphStore())
    with TestClient(app) as client:
        resp = client.get("/api/v1/graph/subgraph/100")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pmid"] == "100"
    assert body["nodes"][0]["id"] == "paper:100"
    assert body["links"][0]["type"] == "AUTHORED"


def test_subgraph_when_store_unconfigured(monkeypatch):
    monkeypatch.setattr("backend.app.api.v1.graph.get_graph_store", lambda: None)
    with TestClient(app) as client:
        resp = client.get("/api/v1/graph/subgraph/100")
    assert resp.status_code == 503
