"""
Pydantic schemas for LLM JSON outputs and a shared validation helper.
"""

import json
from typing import Optional

from pydantic import BaseModel


class PreferenceSchema(BaseModel):
    languages: list[str] = []
    language_strict: bool = False
    mood_descriptors: list[str] = []
    energy_hint: Optional[float] = None
    context: Optional[str] = None


class EmphasisUpdate(BaseModel):
    """Structured emphasis — avoids dict[str, float] which Gemini rejects as additionalProperties."""
    energy: Optional[float] = None
    acousticness: Optional[float] = None
    valence: Optional[float] = None
    danceability: Optional[float] = None


class RefinementSchema(BaseModel):
    excluded_song_ids: list[int] = []
    emphasis: EmphasisUpdate = EmphasisUpdate()
    languages: Optional[list[str]] = None
    language_strict: Optional[bool] = None
    mood_descriptors: Optional[list[str]] = None
    energy_hint: Optional[float] = None
    context: Optional[str] = None


class SongExplanation(BaseModel):
    song_id: int
    explanation: str


class BatchExplanationSchema(BaseModel):
    explanations: list[SongExplanation]


def validate_json(text: str, schema: type[BaseModel]) -> BaseModel:
    """Parse JSON string and validate against schema. Raises on failure."""
    data = json.loads(text)          # raises json.JSONDecodeError on bad JSON
    return schema.model_validate(data)  # raises ValidationError on bad structure
