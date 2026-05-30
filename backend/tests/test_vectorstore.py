"""Unit tests for the offline vector store + hashing embedder (Phase 9 RAG core).

These exercise :mod:`app.services.vectorstore` directly — no app/client needed.
The embedder is deterministic (md5 hashing trick, L2-normalized), so cosine
similarity is reproducible offline. The ``conftest`` module has already redirected
``WORKSPACE_ROOT`` to a temp dir at import time, so each VectorStore persists into
an isolated ``.state/vectors`` directory under that temp workspace.
"""
from __future__ import annotations

import math

import pytest

from app.core.config import get_settings
from app.services.vectorstore import VectorStore, cosine, embed


def test_embed_dimension_and_unit_norm() -> None:
    vec = embed("hello world")
    assert len(vec) == 256
    norm = math.sqrt(sum(v * v for v in vec))
    assert norm == pytest.approx(1.0)


def test_cosine_self_similarity_is_one() -> None:
    vec = embed("the quick brown fox jumps")
    assert cosine(vec, vec) == pytest.approx(1.0)


def test_unrelated_pair_scores_lower_than_identical_pair() -> None:
    text = "Omnivra orchestrates the CEO and department agents"
    identical = cosine(embed(text), embed(text))
    unrelated = cosine(embed(text), embed("zebra telescope mountain orbit pancake"))
    assert identical == pytest.approx(1.0)
    assert unrelated < identical


def test_store_add_and_search_returns_added_item_as_top_hit() -> None:
    store = VectorStore("test_search", str(get_settings().workspace_path))
    store.clear()
    store.add("LangGraph powers the CEO to department orchestration graph", {"source": "doc"})
    store.add("The frontend uses React Query and Tailwind glass UI", {"source": "doc"})

    hits = store.search("orchestration graph for departments", k=2)
    assert hits, "search over a populated store must return hits"
    top = hits[0]
    assert "orchestration" in top["text"].lower()
    assert top["score"] > 0
    assert top["metadata"]["source"] == "doc"


def test_recent_is_newest_first_and_count_increments() -> None:
    store = VectorStore("test_recent", str(get_settings().workspace_path))
    store.clear()
    assert store.count == 0

    store.add("first memory")
    assert store.count == 1
    store.add("second memory")
    store.add("third memory")
    assert store.count == 3

    recent = store.recent(2)
    assert [r["text"] for r in recent] == ["third memory", "second memory"]
