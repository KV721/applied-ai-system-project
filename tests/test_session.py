"""
Tests for multi-turn session state transitions.
Uses a mock LLM client — no live API calls.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from src.catalog import load_songs
from src.session import Session

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURES / "sample_songs.csv"
EMB_DIM = 8


class _MockEmbedModel:
    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        return np.ones((len(texts), EMB_DIM), dtype=np.float32)


class _MockLLMClient:
    """
    Stateful mock: tracks how many times refinement has been called so that
    each turn can return distinct exclusion IDs — letting accumulation tests pass.
    """

    def __init__(self):
        self._refine_calls = 0

    def reset_turn_counter(self):
        pass

    def call(self, system, user, schema=None, json_mode=False, max_tokens=1024, prompt_type="unknown") -> str:
        if prompt_type == "preference_parser":
            return json.dumps({
                "languages": [],
                "language_strict": False,
                "mood_descriptors": ["chill"],
                "energy_hint": 0.4,
                "context": None,
            })
        elif prompt_type == "refinement_parser":
            self._refine_calls += 1
            # 1st refine excludes [1], 2nd excludes [2], etc.
            return json.dumps({
                "excluded_song_ids": [self._refine_calls],
                "emphasis": {"acousticness": 0.8} if self._refine_calls == 1 else {},
                "languages": None,
                "language_strict": None,
                "mood_descriptors": ["happy"] if self._refine_calls == 1 else None,
                "energy_hint": None,
                "context": None,
            })
        else:  # explainer
            return "This track fits your request well."


@pytest.fixture
def songs():
    return load_songs(str(SAMPLE_CSV))


@pytest.fixture
def embeddings(songs):
    return np.ones((len(songs), EMB_DIM), dtype=np.float32)


@pytest.fixture
def session(songs, embeddings):
    return Session(songs, embeddings, _MockEmbedModel(), _MockLLMClient())


def test_turn_counter_increments_on_refine(session):
    session.start("chill music")
    assert session.state().turn == 1
    session.refine("more acoustic")
    assert session.state().turn == 2


def test_exclusions_accumulate_across_turns(session):
    session.start("chill music")
    session.refine("not the first one")   # mock excludes [1]
    assert 1 in session.state().profile.excluded_song_ids
    session.refine("still not right")     # mock excludes [2]
    assert 1 in session.state().profile.excluded_song_ids  # still present
    assert 2 in session.state().profile.excluded_song_ids  # newly added


def test_is_complete_after_three_turns(session):
    session.start("chill")
    assert not session.is_complete()
    session.refine("more acoustic")
    assert not session.is_complete()
    session.refine("a bit sadder")
    assert session.is_complete()


def test_profile_updates_apply_on_refinement(session):
    session.start("something chill")
    session.refine("make it happier")  # mock returns mood_descriptors: ["happy"]
    assert "happy" in session.state().profile.mood_descriptors


def test_start_returns_recommendations(session):
    recs = session.start("chill music")
    assert len(recs) > 0
    for rec in recs:
        assert rec.song is not None
        assert rec.explanation != ""


def test_history_grows_each_turn(session):
    session.start("chill")
    assert len(session.state().history) == 1
    session.refine("more acoustic")
    assert len(session.state().history) == 2
