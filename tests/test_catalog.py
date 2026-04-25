"""
Tests for catalog loading and validation.
"""

import dataclasses
from pathlib import Path

import pytest

from src.catalog import load_songs, validate_catalog
from src.models import Song

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_CSV = FIXTURES / "sample_songs.csv"
REAL_CSV = Path(__file__).parent.parent / "data" / "songs.csv"


def test_load_songs_returns_correct_count():
    songs = load_songs(str(SAMPLE_CSV))
    assert len(songs) == 6


def test_all_songs_have_required_fields():
    songs = load_songs(str(SAMPLE_CSV))
    for song in songs:
        assert isinstance(song, Song)
        assert song.id > 0
        assert song.title
        assert song.artist
        assert song.language
        assert song.description
        assert song.mood_tags


def test_mood_tags_are_split_correctly():
    songs = load_songs(str(SAMPLE_CSV))
    for song in songs:
        assert isinstance(song.mood_tags, list)
        for tag in song.mood_tags:
            assert ";" not in tag
            assert tag == tag.strip()


def test_audio_features_in_valid_range():
    songs = load_songs(str(SAMPLE_CSV))
    for song in songs:
        assert 0.0 <= song.energy <= 1.0
        assert 0.0 <= song.valence <= 1.0
        assert 0.0 <= song.danceability <= 1.0
        assert 0.0 <= song.acousticness <= 1.0
        assert song.tempo_bpm > 0


def test_validate_catalog_passes_on_valid_data():
    songs = load_songs(str(SAMPLE_CSV))
    validate_catalog(songs)  # should not raise


def test_validate_catalog_raises_on_bad_range():
    songs = load_songs(str(SAMPLE_CSV))
    bad = dataclasses.replace(songs[0], energy=1.5)
    with pytest.raises(ValueError, match="energy"):
        validate_catalog([bad] + songs[1:])


def test_validate_catalog_raises_on_missing_description():
    songs = load_songs(str(SAMPLE_CSV))
    bad = dataclasses.replace(songs[0], description="")
    with pytest.raises(ValueError, match="description"):
        validate_catalog([bad] + songs[1:])


def test_validate_catalog_raises_on_empty_mood_tags():
    songs = load_songs(str(SAMPLE_CSV))
    bad = dataclasses.replace(songs[0], mood_tags=[])
    with pytest.raises(ValueError, match="mood_tags"):
        validate_catalog([bad] + songs[1:])


def test_real_catalog_loads_and_validates():
    songs = load_songs(str(REAL_CSV))
    assert len(songs) >= 60
    validate_catalog(songs)
