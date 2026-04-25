"""
LLM-based grounded explanation generation per recommended song.
"""

import sys
import traceback

from src.llm_client import LLMClient
from src.models import SessionProfile, Song
from src.prompts import BATCH_EXPLAINER_SYSTEM, EXPLAINER_SYSTEM
from src.validators import BatchExplanationSchema, validate_json


def explain_batch(
    songs: list[Song], profile: SessionProfile, client: LLMClient
) -> dict[int, str]:
    """
    Generate grounded explanations for all songs in a single LLM call.
    Returns a dict mapping song_id → explanation string.
    Falls back to song.description for any song missing from the response,
    or for all songs if the call itself fails.
    """
    fallback = {song.id: song.description for song in songs}

    mood_str = (
        ", ".join(profile.mood_descriptors) if profile.mood_descriptors else "not specified"
    )
    songs_section = "\n".join(
        f'  id={song.id}: "{song.title}" by {song.artist} — {song.description}'
        for song in songs
    )
    user_msg = (
        f'User request: "{profile.raw_query}"\n'
        f"Mood descriptors: {mood_str}\n"
        f"Context: {profile.context or 'not specified'}\n\n"
        f"Songs:\n{songs_section}"
    )

    try:
        raw = client.call(
            system=BATCH_EXPLAINER_SYSTEM,
            user=user_msg,
            schema=BatchExplanationSchema,
            prompt_type="explainer_batch",
            max_tokens=1500,
        )
        result = validate_json(raw, BatchExplanationSchema)
        mapping = {item.song_id: item.explanation for item in result.explanations}
        for song in songs:
            if song.id not in mapping:
                mapping[song.id] = song.description
        return mapping
    except Exception as e:
        print(f"[explain_batch] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return fallback


def explain(song: Song, profile: SessionProfile, client: LLMClient) -> str:
    """
    Generate a grounded explanation for a single song.
    Falls back to the song's own description on LLM failure.
    """
    mood_str = (
        ", ".join(profile.mood_descriptors) if profile.mood_descriptors else "not specified"
    )
    user_msg = (
        f'User request: "{profile.raw_query}"\n'
        f"Mood descriptors: {mood_str}\n"
        f"Context: {profile.context or 'not specified'}\n\n"
        f"Song: {song.title} by {song.artist}\n"
        f"Description: {song.description}"
    )
    try:
        return client.call(
            system=EXPLAINER_SYSTEM,
            user=user_msg,
            prompt_type="explainer",
            max_tokens=200,
        ).strip()
    except Exception as e:
        print(f"[explain] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return song.description
