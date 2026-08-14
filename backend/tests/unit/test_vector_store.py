# -*- coding: utf-8 -*-
"""Unit tests for services/vector_store.py (QdrantVectorStore).

A fake qdrant_client package is injected into sys.modules and the module
flag is flipped inside a fixture so the tests run without the real
qdrant-client dependency or network access, regardless of import order.
"""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from backend.services import vector_store as vs
from backend.services.vector_store import QdrantVectorStore, VectorStoreError

# ---------------------------------------------------------------------------
# Fake qdrant_client package
# ---------------------------------------------------------------------------


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class FakeQdrantClient:
    """Minimal in-memory Qdrant client used by the tests."""

    def __init__(self, url, api_key, timeout=30.0):
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.collections = {}
        self.points = {}

    def get_collection(self, name):
        if name not in self.collections:
            raise Exception(f"Collection {name} not found")
        return SimpleNamespace(points_count=len(self.points.get(name, {})))

    def create_collection(self, collection_name, vectors_config):
        self.collections[collection_name] = vectors_config

    def upsert(self, collection_name, points):
        self.points.setdefault(collection_name, {})
        for p in points:
            self.points[collection_name][str(p.id)] = {
                "vector": list(p.vector),
                "payload": dict(p.payload),
            }

    def query_points(self, collection_name, query, limit, with_payload=True):
        scored = []
        for pid, item in self.points.get(collection_name, {}).items():
            scored.append((_dot(query, item["vector"]), pid))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for sim, pid in scored[:limit]:
            out.append(
                SimpleNamespace(
                    payload=dict(self.points[collection_name][pid]["payload"]),
                    score=sim,
                )
            )
        return SimpleNamespace(points=out)


class _PointStruct:
    def __init__(self, id, vector, payload):
        self.id = id
        self.vector = vector
        self.payload = payload


class _Distance:
    COSINE = "Cosine"


def _vector_params(size, distance):
    return {"size": size, "distance": distance}


def _build_fake_modules():
    fake_qdrant = types.ModuleType("qdrant_client")
    fake_models = types.ModuleType("qdrant_client.models")
    fake_models.Distance = _Distance
    fake_models.VectorParams = _vector_params
    fake_models.PointStruct = _PointStruct
    fake_qdrant.models = fake_models
    fake_qdrant.QdrantClient = FakeQdrantClient
    return fake_qdrant, fake_models


@pytest.fixture(scope="module", autouse=True)
def _fake_qdrant_env():
    """Inject the fake qdrant_client package and enable it in the module."""
    fake_qdrant, fake_models = _build_fake_modules()
    orig_qdrant = sys.modules.get("qdrant_client")
    orig_models = sys.modules.get("qdrant_client.models")
    sys.modules["qdrant_client"] = fake_qdrant
    sys.modules["qdrant_client.models"] = fake_models

    orig_available = vs._QDRANT_AVAILABLE
    orig_client_cls = vs.QdrantClient
    vs._QDRANT_AVAILABLE = True
    vs.QdrantClient = FakeQdrantClient

    yield

    vs._QDRANT_AVAILABLE = orig_available
    vs.QdrantClient = orig_client_cls
    if orig_qdrant is not None:
        sys.modules["qdrant_client"] = orig_qdrant
    else:
        sys.modules.pop("qdrant_client", None)
    if orig_models is not None:
        sys.modules["qdrant_client.models"] = orig_models
    else:
        sys.modules.pop("qdrant_client.models", None)


class FakeEmbeddingClient:
    """Returns deterministic embeddings of a fixed dimension."""

    def __init__(self, dim=4):
        self.dim = dim
        self.calls = []

    def embed_documents(self, texts):
        self.calls.append(("documents", list(texts)))
        return [[float(i + 1 + j) for j in range(self.dim)] for i in range(len(texts))]

    def embed_query(self, text):
        self.calls.append(("query", text))
        return [1.0, 0.0, 0.0, 0.0]


def _article_dict(pmid, title="T", abstract="A"):
    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "doi": "",
        "authors": [],
        "journal": "",
        "publish_date": "",
        "publication_type": "",
    }


@pytest.fixture
def store():
    embed = FakeEmbeddingClient()
    return QdrantVectorStore(
        url="http://localhost:6333",
        api_key="test-key",
        collection_name="pubmed_articles",
        embedding_client=embed,
    )


def test_pmid_to_point_id_is_stable():
    first = vs._pmid_to_point_id("12345")
    second = vs._pmid_to_point_id("12345")
    assert first == second
    assert vs._pmid_to_point_id("12345") != vs._pmid_to_point_id("67890")


def test_upsert_articles_creates_collection_and_points(store):
    n = store.upsert_articles([_article_dict("1"), _article_dict("2")])
    assert n == 2
    client = store.client
    assert "pubmed_articles" in client.collections
    assert len(client.points["pubmed_articles"]) == 2


def test_upsert_empty_returns_zero(store):
    assert store.upsert_articles([]) == 0


def test_upsert_requires_embedding_client():
    store = QdrantVectorStore(url="http://x", api_key="k")
    with pytest.raises(VectorStoreError):
        store.upsert_articles([_article_dict("1")])


def test_upsert_accepts_dicts(store):
    store.upsert_articles([_article_dict("7", title="SEC61G", abstract="lung cancer")])
    client = store.client
    payload = list(client.points["pubmed_articles"].values())[0]["payload"]
    assert payload["pmid"] == "7"
    assert payload["title"] == "SEC61G"


def test_semantic_search_returns_payloads_with_scores(store):
    store.upsert_articles(
        [_article_dict("1", title="a"), _article_dict("2", title="b")]
    )
    hits = store.semantic_search("some query", top_k=2)
    assert len(hits) == 2
    assert all("pmid" in h and "score" in h for h in hits)
    assert hits[0]["score"] >= hits[1]["score"]


def test_semantic_search_top_k_zero(store):
    store.upsert_articles([_article_dict("1")])
    assert store.semantic_search("q", top_k=0) == []


def test_count_returns_stored_points(store):
    assert store.count() == 0
    store.upsert_articles([_article_dict("1"), _article_dict("2")])
    assert store.count() == 2


def test_is_ready_after_upsert(store):
    assert store.is_ready() is False
    store.upsert_articles([_article_dict("1")])
    assert store.is_ready() is True


def test_missing_qdrant_package_raises_informative_error(monkeypatch):
    monkeypatch.setattr(vs, "_QDRANT_AVAILABLE", False)
    monkeypatch.setattr(vs, "QdrantClient", None)
    store = QdrantVectorStore(url="http://x", api_key="k")
    with pytest.raises(VectorStoreError, match="qdrant-client is not installed"):
        _ = store.client
