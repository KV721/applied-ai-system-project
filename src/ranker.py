"""
Rule-based re-ranker: combines retrieval score with audio-feature fit score.
"""

from collections import deque

from src.models import Recommendation, SessionProfile, Song

RETRIEVAL_WEIGHT = 0.6
FEATURE_WEIGHT = 0.4

# Feature score sub-weights. EMPHASIS_WEIGHT > ENERGY_WEIGHT intentionally:
# emphasis values come from explicit user correction in a refinement turn, so
# they should override the initial energy guess from turn 1.
ENERGY_WEIGHT = 1.0
EMPHASIS_WEIGHT = 1.5
# Language soft bonus: applied only when exactly one language is preferred
# (non-strict). With multiple languages the bonus is equal for every song
# in the catalog, so it has no discriminatory power — use diversification instead.
LANGUAGE_SOFT_BONUS = 0.3

_FEATURE_MAP_KEYS = {
    "energy": "energy",
    "acousticness": "acousticness",
    "acoustic": "acousticness",
    "valence": "valence",
    "danceability": "danceability",
}


def rank(
    candidates: list[tuple[Song, float]],
    profile: SessionProfile,
    top_k: int = 5,
) -> list[Recommendation]:
    """Combine retrieval score with audio-feature fit score, return top_k."""
    scored = []
    for song, retrieval_score in candidates:
        feature_score = compute_feature_score(song, profile)
        combined = RETRIEVAL_WEIGHT * retrieval_score + FEATURE_WEIGHT * feature_score
        scored.append((song, retrieval_score, feature_score, combined))

    # Primary sort: combined score descending; tiebreaker: song.id ascending
    scored.sort(key=lambda x: (-x[3], x[0].id))

    # When the user requests a mix of languages (≥2, non-strict), interleave
    # songs from each language so no single language dominates the top-k.
    if len(profile.languages) >= 2 and not profile.language_strict:
        scored = _diversify_by_language(scored, profile.languages, top_k)

    return [
        Recommendation(
            song=song,
            retrieval_score=retrieval_score,
            ranking_score=combined,
        )
        for song, retrieval_score, _, combined in scored[:top_k]
    ]


def _diversify_by_language(
    scored: list[tuple],
    languages: list[str],
    top_k: int,
) -> list[tuple]:
    """Round-robin interleave songs by language so all requested languages appear."""
    queues: dict[str, deque] = {
        lang: deque(x for x in scored if x[0].language == lang)
        for lang in languages
    }
    active = list(languages)
    result: list[tuple] = []
    i = 0

    while len(result) < top_k and active:
        lang = active[i % len(active)]
        if queues[lang]:
            result.append(queues[lang].popleft())
            i += 1
        else:
            active.remove(lang)

    return result


def compute_feature_score(song: Song, profile: SessionProfile) -> float:
    """Score how well a song's audio features match the profile. Returns 0.0–1.0."""
    score = 0.0
    weight = 0.0

    if profile.energy_hint is not None:
        score += (1.0 - abs(song.energy - profile.energy_hint)) * ENERGY_WEIGHT
        weight += ENERGY_WEIGHT

    # Only apply language soft bonus when exactly one language is preferred —
    # with multiple languages every catalog song matches equally, so the bonus
    # adds no signal and wastes weight; use _diversify_by_language instead.
    if len(profile.languages) == 1 and not profile.language_strict:
        bonus = LANGUAGE_SOFT_BONUS if song.language in profile.languages else 0.0
        score += bonus
        weight += LANGUAGE_SOFT_BONUS

    # Emphasis overrides (e.g. {"acousticness": 0.8} from refinement).
    # Weighted higher than the initial energy hint — explicit user correction
    # should dominate the original guess.
    for feat, target in profile.emphasis.items():
        attr = _FEATURE_MAP_KEYS.get(feat)
        if attr is not None:
            val = getattr(song, attr)
            score += (1.0 - abs(val - target)) * EMPHASIS_WEIGHT
            weight += EMPHASIS_WEIGHT

    if weight == 0.0:
        return 0.5  # neutral when no feature signals

    return score / weight
