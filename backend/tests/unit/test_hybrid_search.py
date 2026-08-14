# -*- coding: utf-8 -*-
"""Unit tests for HybridSearcher Qdrant integration and fallback paths."""

from __future__ import annotations

import pytest

from backend.services.hybrid_search import EmbeddingClient, HybridSearcher
from backend.tools.pubmed_tool import PubMedArticle, PubMedSearchResult


class FakePubMedTool:
    """Returns a fixed pool of articles for any query."""

    def __init__(self, articles):
        self.articles = articles

    def search(self, query, max_results=20):
        return PubMedSearchResult(
            query=query,
            total_count=len(self.articles),
            articles=self.articles[:max_results],
        )


class FakeEmbeddingClient(EmbeddingClient):
    """Stub embedding client (no network)."""

    def __init__(self):
        self.embedded = []

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]

    def embed_documents(self, texts):
        self.embedded.append(list(texts))
        return [[1.0, 0.0, 0.0]] * len(texts)


class FakeVectorStore:
    """Records calls and returns configurable semantic hits."""

    def __init__(self, hits=None, fail=False):
        self.hits = hits or []
        self.fail = fail
        self.upserted = []
        self.queries = []

    def upsert_articles(self, articles):
        if self.fail:
            raise RuntimeError("qdrant down")
        self.upserted.append(list(articles))

    def semantic_search(self, query, top_k=10):
        if self.fail:
            raise RuntimeError("qdrant down")
        self.queries.append(query)
        return self.hits[:top_k]


def _article(pmid):
    return PubMedArticle(pmid=pmid, title=f"Title {pmid}", abstract=f"Abstract {pmid}")


ARTICLES = [_article("1"), _article("2"), _article("3")]


def test_uses_vector_store_for_semantic_search():
    store = FakeVectorStore(
        hits=[{"pmid": "3", "score": 0.9}, {"pmid": "1", "score": 0.7}]
    )
    embed = FakeEmbeddingClient()
    searcher = HybridSearcher(FakePubMedTool(ARTICLES), embed, vector_store=store)
    result = searcher.search("SEC61G", top_k=3, keyword_k=5)

    assert store.upserted and len(store.upserted[0]) == 3
    assert store.queries == ["SEC61G"]
    pmids = [a.pmid for a in result.articles]
    assert set(pmids) == {"1", "2", "3"}
    # semantic-only PMIDs stay in the pool; keyword order anchors the fusion
    assert result.total_count == 3


def test_vector_store_failure_falls_back_to_in_batch_embedding():
    store = FakeVectorStore(fail=True)
    embed = FakeEmbeddingClient()
    searcher = HybridSearcher(FakePubMedTool(ARTICLES), embed, vector_store=store)
    result = searcher.search("SEC61G", top_k=3, keyword_k=5)

    assert embed.embedded, "in-batch embedding fallback should have run"
    assert len(result.articles) == 3


def test_keyword_only_when_no_embed_and_no_store():
    searcher = HybridSearcher(FakePubMedTool(ARTICLES), embed_client=None)
    result = searcher.search("SEC61G", top_k=3, keyword_k=5)
    assert [a.pmid for a in result.articles] == ["1", "2", "3"]


def test_backward_compatible_positional_embed_client():
    embed = FakeEmbeddingClient()
    searcher = HybridSearcher(FakePubMedTool(ARTICLES), embed)
    result = searcher.search("SEC61G", top_k=2, keyword_k=5)
    assert len(result.articles) == 2


def test_empty_keyword_pool_returns_empty():
    searcher = HybridSearcher(FakePubMedTool([]), embed_client=None)
    result = searcher.search("nothing", top_k=3, keyword_k=5)
    assert result.articles == []
