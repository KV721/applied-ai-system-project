"""
Preference and refinement parsers: NL text → SessionProfile via LLM.
"""

import json
import sys
import traceback

from src.llm_client import LLMClient
from src.models import SessionProfile, Song
from src.prompts import PREFERENCE_PARSER_SYSTEM, REFINEMENT_PARSER_SYSTEM
from src.validators import PreferenceSchema, RefinementSchema, validate_json


def parse_preferences(query: str, client: LLMClient) -> SessionProfile:
    """Parse a natural-language query into a SessionProfile. Falls back to minimal profile."""
    sanitized = query[:500]  # guardrail: cap raw input length
    try:
        raw = client.call(
            system=PREFERENCE_PARSER_SYSTEM,
            user=sanitized,
            schema=PreferenceSchema,
            prompt_type="preference_parser",
        )
        parsed = validate_json(raw, PreferenceSchema)
        return SessionProfile(
            raw_query=query,
            languages=parsed.languages,
            language_strict=parsed.language_strict,
            mood_descriptors=parsed.mood_descriptors,
            energy_hint=parsed.energy_hint,
            context=parsed.context,
        )
    except Exception as e:
        print(f"[parse_preferences] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return SessionProfile(raw_query=query)


def parse_refinement(
    feedback: str,
    current_profile: SessionProfile,
    shown_songs: list[Song],
    client: LLMClient,
) -> SessionProfile:
    """Interpret free-form feedback and return an updated SessionProfile."""
    # Include position numbers so the LLM can unambiguously map "#1" / "first one"
    # to the correct catalog id (which is never 1-indexed).
    shown_summary = json.dumps(
        [
            {"position": i + 1, "id": s.id, "title": s.title, "artist": s.artist}
            for i, s in enumerate(shown_songs)
        ],
        ensure_ascii=False,
    )
    user_msg = (
        f"User feedback: {feedback}\n\n"
        f"Current profile:\n"
        f"  Languages: {current_profile.languages}\n"
        f"  Language strict: {current_profile.language_strict}\n"
        f"  Mood: {current_profile.mood_descriptors}\n"
        f"  Energy hint: {current_profile.energy_hint}\n"
        f"  Context: {current_profile.context}\n\n"
        f"Shown songs (position is display order; id is the catalog identifier):\n{shown_summary}"
    )
    try:
        raw = client.call(
            system=REFINEMENT_PARSER_SYSTEM,
            user=user_msg,
            schema=RefinementSchema,
            prompt_type="refinement_parser",
        )
        delta = validate_json(raw, RefinementSchema)
        return SessionProfile(
            raw_query=current_profile.raw_query,  # preserve original intent for retrieval
            languages=(
                delta.languages
                if delta.languages is not None
                else current_profile.languages
            ),
            language_strict=(
                delta.language_strict
                if delta.language_strict is not None
                else current_profile.language_strict
            ),
            mood_descriptors=(
                delta.mood_descriptors
                if delta.mood_descriptors is not None
                else current_profile.mood_descriptors
            ),
            energy_hint=(
                delta.energy_hint
                if delta.energy_hint is not None
                else current_profile.energy_hint
            ),
            context=(
                delta.context
                if delta.context is not None
                else current_profile.context
            ),
            excluded_song_ids=current_profile.excluded_song_ids | set(delta.excluded_song_ids),
            emphasis={
                **current_profile.emphasis,
                **{k: v for k, v in delta.emphasis.model_dump().items() if v is not None},
            },
        )
    except Exception as e:
        print(f"[parse_refinement] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return current_profile  # fallback: no change on LLM failure
