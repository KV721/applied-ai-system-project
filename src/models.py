"""
Dataclasses for the Tuneweave runtime data model.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Song:
    id: int
    title: str
    artist: str
    language: str
    genre: str
    mood_tags: list[str]
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    year: Optional[int]
    description: str


@dataclass
class SessionProfile:
    raw_query: str
    languages: list[str] = field(default_factory=list)
    language_strict: bool = False
    mood_descriptors: list[str] = field(default_factory=list)
    energy_hint: Optional[float] = None
    context: Optional[str] = None
    excluded_song_ids: set[int] = field(default_factory=set)
    emphasis: dict[str, float] = field(default_factory=dict)


@dataclass
class Recommendation:
    song: Song
    retrieval_score: float
    ranking_score: float
    explanation: str = ""


@dataclass
class SessionState:
    turn: int
    profile: SessionProfile
    history: list[list[Recommendation]] = field(default_factory=list)
