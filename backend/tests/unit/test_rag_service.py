# -*- coding: utf-8 -*-
"""Unit tests for RagService and the /api/v1/rag/query endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.rag import RagQueryOut
from backend.services.rag_service import RagService


class FakeVectorStore:
    def __init__(self, hits=None, fail=False):
        self.hits = hits or []
        self.fail = fail

    def semantic_search(self, query, top_k=10):
        if self.fail:
            raise RuntimeError("qdrant down")
        return self.hits[:top_k]


class FakeLLM:
    def __init__(self, raw):
        self.raw = raw
        self.last_prompt = None

    def _call_llm(self, system, user):
        self.last_prompt = user
        return self.raw


def _hits():
    return [
        {
            "pmid": "100",
            "title": "SEC61G in lung cancer",
            "abstract": "We studied SEC61G expression in lung cancer.",
            "score": 0.91,
        },
        {
            "pmid": "200",
            "title": "SEC61G review",
            "abstract": "A review of SEC61G.",
            "score": 0.82,
        },
    ]


def test_answer_returns_sources_and_answer():
    llm = FakeLLM(raw='{"answer": "SEC61G is upregulated.", "sources": ["100"]}')
    service = RagService(FakeVectorStore(_hits()), llm)
    out = service.answer("What is the role of SEC61G?", top_k=2, language="en")
    assert isinstance(out, RagQueryOut)
    assert out.answer == "SEC61G is upregulated."
    assert [s.pmid for s in out.sources] == ["100", "200"]
    assert out.sources[0].relevance_score == 0.91


def test_answer_tolerates_plain_text_llm_output():
    llm = FakeLLM(raw="Plain text answer without JSON.")
    service = RagService(FakeVectorStore(_hits()), llm)
    out = service.answer("q", top_k=2)
    assert out.answer == "Plain text answer without JSON."


def test_zh_language_instruction_is_passed():
    llm = FakeLLM(raw='{"answer": "中文答案"}')
    service = RagService(FakeVectorStore(_hits()), llm)
    service.answer("q", top_k=2, language="zh")
    assert "Answer in Chinese" in llm.last_prompt


def test_no_vector_store_returns_message():
    service = RagService(None, FakeLLM("ignored"))
    out = service.answer("q")
    assert "not configured" in out.answer
    assert out.sources == []


def test_no_hits_returns_message():
    service = RagService(FakeVectorStore([]), FakeLLM("ignored"))
    out = service.answer("q")
    assert "No relevant articles" in out.answer
    assert out.sources == []


def test_rag_endpoint_returns_answer(monkeypatch):
    service = RagService(FakeVectorStore(_hits()), FakeLLM('{"answer": "ok"}'))
    monkeypatch.setattr("backend.app.api.v1.rag.get_rag_service", lambda: service)
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/rag/query",
            json={"query": "role of SEC61G", "top_k": 2, "language": "en"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "ok"
    assert len(body["sources"]) == 2
