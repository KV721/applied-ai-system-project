"""
Tests for preference and refinement parsing using cached LLM responses.
Tests the validator logic, not the live Gemini API.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.validators import PreferenceSchema, RefinementSchema, validate_json

FIXTURES = Path(__file__).parent / "fixtures"


def _cache():
    with open(FIXTURES / "cached_llm_responses.json") as f:
        return json.load(f)


# ── Preference parsing ────────────────────────────────────────────────────────

def test_preference_schema_parses_cached_response():
    for entry in _cache()["preference_responses"]:
        result = validate_json(entry["output"], PreferenceSchema)
        assert isinstance(result, PreferenceSchema)


def test_language_field_present_in_parsed_profile():
    for entry in _cache()["preference_responses"]:
        result = validate_json(entry["output"], PreferenceSchema)
        assert hasattr(result, "languages")
        assert isinstance(result.languages, list)


def test_mood_descriptors_nonempty_for_mood_query():
    # All cached queries contain explicit mood words
    for entry in _cache()["preference_responses"]:
        result = validate_json(entry["output"], PreferenceSchema)
        assert len(result.mood_descriptors) >= 1


def test_language_strict_true_when_only_specified():
    # cache[1] is "only hindi romantic songs"
    result = validate_json(_cache()["preference_responses"][1]["output"], PreferenceSchema)
    assert result.language_strict is True
    assert "hindi" in result.languages


def test_language_strict_false_for_soft_preference():
    # cache[0] is "chill telugu" — not "only telugu"
    result = validate_json(_cache()["preference_responses"][0]["output"], PreferenceSchema)
    assert result.language_strict is False


def test_energy_hint_within_valid_range():
    for entry in _cache()["preference_responses"]:
        result = validate_json(entry["output"], PreferenceSchema)
        if result.energy_hint is not None:
            assert 0.0 <= result.energy_hint <= 1.0


def test_no_language_when_none_specified():
    # cache[2] is "something upbeat and energetic" — no language
    result = validate_json(_cache()["preference_responses"][2]["output"], PreferenceSchema)
    assert result.languages == []


# ── Refinement parsing ────────────────────────────────────────────────────────

def test_refinement_schema_parses_exclusion_feedback():
    for entry in _cache()["refinement_responses"]:
        result = validate_json(entry["output"], RefinementSchema)
        assert isinstance(result, RefinementSchema)
        assert isinstance(result.excluded_song_ids, list)


def test_refinement_emphasis_is_valid():
    from src.validators import EmphasisUpdate
    for entry in _cache()["refinement_responses"]:
        result = validate_json(entry["output"], RefinementSchema)
        assert isinstance(result.emphasis, EmphasisUpdate)
        # At least one feature is set when the cached feedback requests audio changes
        set_values = [v for v in result.emphasis.model_dump().values() if v is not None]
        assert len(set_values) >= 1


def test_refinement_exclusion_ids_populated():
    # cache refinement[1] excludes [1,2,3,4,5]
    result = validate_json(_cache()["refinement_responses"][1]["output"], RefinementSchema)
    assert len(result.excluded_song_ids) == 5


# ── Validator error handling ──────────────────────────────────────────────────

def test_validate_json_raises_on_malformed_input():
    with pytest.raises(json.JSONDecodeError):
        validate_json("{not valid json", PreferenceSchema)


def test_validate_json_raises_on_type_violation():
    with pytest.raises((ValidationError, ValueError)):
        validate_json('{"energy_hint": "not-a-number"}', PreferenceSchema)
