"""
Semantic retrieval: embed query, cosine similarity over catalog, apply hard filters.
"""

import numpy as np
from src.embeddings import embed_query
from src.models import SessionProfile, Song


def retrieve(
    profile: SessionProfile,
    songs: list[Song],
    embeddings: np.ndarray,
    embed_model,
    top_k: int = 20,
) -> list[tuple[Song, float]]:
    """Embed query from profile, cosine similarity, apply hard filters, return top_k."""
    query_text = _build_query_text(profile)
    query_vec = embed_query(query_text, embed_model)
    scores = _cosine_similarities(query_vec, embeddings)

    candidates = []
    for song, score in zip(songs, scores):
        if song.id in profile.excluded_song_ids:
            continue
        if profile.language_strict and profile.languages:
            if song.language not in profile.languages:
                continue
        candidates.append((song, float(score)))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:top_k]


def _build_query_text(profile: SessionProfile) -> str:
    parts = [profile.raw_query]
    if profile.mood_descriptors:
        parts.append("mood: " + ", ".join(profile.mood_descriptors))
    if profile.context:
        parts.append("context: " + profile.context)
    if profile.languages and not profile.language_strict:
        parts.append("prefer " + " or ".join(profile.languages))
    return " | ".join(parts)


def _cosine_similarities(query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query)
    emb_norms = np.linalg.norm(embeddings, axis=1)
    denom = emb_norms * query_norm
    denom = np.where(denom == 0, 1e-8, denom)
    return (embeddings @ query) / denom
