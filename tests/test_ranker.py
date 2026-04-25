"""
Tests for the rule-based re-ranker.
"""

import pytest

from src.models import Recommendation, SessionProfile, Song
from src.ranker import compute_feature_score, rank


def make_song(id, energy=0.5, language="english", acousticness=0.5):
    return Song(
        id=id,
        title=f"Song {id}",
        artist="Artist",
        language=language,
        genre="pop",
        mood_tags=["chill"],
        energy=energy,
        tempo_bpm=120.0,
        valence=0.5,
        danceability=0.5,
        acousticness=acousticness,
        year=2020,
        description="A test song.",
    )


def test_rank_returns_top_k():
    songs = [make_song(i) for i in range(1, 7)]
    candidates = [(s, 0.8) for s in songs]
    profile = SessionProfile(raw_query="music")
    results = rank(candidates, profile, top_k=3)
    assert len(results) == 3


def test_rank_returns_recommendation_objects():
    songs = [make_song(i) for i in range(1, 4)]
    candidates = [(s, 0.7) for s in songs]
    profile = SessionProfile(raw_query="music")
    results = rank(candidates, profile, top_k=3)
    for r in results:
        assert isinstance(r, Recommendation)
        assert isinstance(r.song, Song)


def test_feature_score_monotonic_in_energy_fit():
    profile = SessionProfile(raw_query="high energy", energy_hint=0.9)
    close = make_song(1, energy=0.9)
    far = make_song(2, energy=0.1)
    assert compute_feature_score(close, profile) > compute_feature_score(far, profile)


def test_rank_output_sorted_descending():
    songs = [make_song(i) for i in range(1, 6)]
    # Different retrieval scores so combined scores differ
    candidates = [(s, 1.0 - i * 0.15) for i, s in enumerate(songs)]
    profile = SessionProfile(raw_query="music")
    results = rank(candidates, profile, top_k=5)
    scores = [r.ranking_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_tie_breaking_is_deterministic():
    songs = [make_song(i) for i in range(1, 4)]
    candidates = [(s, 0.7) for s in songs]  # identical retrieval scores
    profile = SessionProfile(raw_query="music")
    run1 = [r.song.id for r in rank(candidates, profile, top_k=3)]
    run2 = [r.song.id for r in rank(candidates, profile, top_k=3)]
    assert run1 == run2


def test_emphasis_raises_acoustic_song_above_non_acoustic():
    profile = SessionProfile(
        raw_query="acoustic music",
        emphasis={"acousticness": 0.9},
    )
    acoustic = make_song(1, acousticness=0.9)
    electronic = make_song(2, acousticness=0.1)
    assert compute_feature_score(acoustic, profile) > compute_feature_score(electronic, profile)


def test_neutral_score_when_no_profile_hints():
    profile = SessionProfile(raw_query="anything")
    song = make_song(1)
    score = compute_feature_score(song, profile)
    assert score == 0.5
