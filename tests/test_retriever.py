"""
Tests for the semantic retriever.
"""

from pathlib import Path

import numpy as np
import pytest

from src.catalog import load_songs
from src.models import SessionProfile
from src.retriever import retrieve

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURES / "sample_songs.csv"
EMB_DIM = 8


class _MockEmbedModel:
    """All-ones embeddings → cosine sim = 1.0 for every song; filters are the differentiator."""

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        return np.ones((len(texts), EMB_DIM), dtype=np.float32)


@pytest.fixture
def songs():
    return load_songs(str(SAMPLE_CSV))


@pytest.fixture
def embeddings(songs):
    return np.ones((len(songs), EMB_DIM), dtype=np.float32)


@pytest.fixture
def embed_model():
    return _MockEmbedModel()


def test_retrieve_returns_correct_k(songs, embeddings, embed_model):
    profile = SessionProfile(raw_query="something chill")
    results = retrieve(profile, songs, embeddings, embed_model, top_k=3)
    assert len(results) == 3


def test_retrieve_respects_top_k_limit(songs, embeddings, embed_model):
    profile = SessionProfile(raw_query="music")
    results = retrieve(profile, songs, embeddings, embed_model, top_k=2)
    assert len(results) <= 2


def test_language_hard_filter_excludes_other_languages(songs, embeddings, embed_model):
    profile = SessionProfile(
        raw_query="telugu songs",
        languages=["telugu"],
        language_strict=True,
    )
    results = retrieve(profile, songs, embeddings, embed_model, top_k=10)
    for song, _ in results:
        assert song.language == "telugu"


def test_excluded_song_ids_are_not_returned(songs, embeddings, embed_model):
    excluded = {songs[0].id, songs[1].id}
    profile = SessionProfile(raw_query="music", excluded_song_ids=excluded)
    results = retrieve(profile, songs, embeddings, embed_model, top_k=10)
    returned_ids = {song.id for song, _ in results}
    assert not (excluded & returned_ids)


def test_no_filter_returns_all_songs(songs, embeddings, embed_model):
    profile = SessionProfile(raw_query="any music")
    results = retrieve(profile, songs, embeddings, embed_model, top_k=100)
    assert len(results) == len(songs)


def test_strict_language_with_no_matches_returns_empty(songs, embeddings, embed_model):
    profile = SessionProfile(
        raw_query="nonexistent language songs",
        languages=["klingon"],
        language_strict=True,
    )
    results = retrieve(profile, songs, embeddings, embed_model, top_k=10)
    assert results == []
