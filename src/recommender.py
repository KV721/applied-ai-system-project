import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        scored = []
        for song in self.songs:
            song_dict = {
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "genre": song.genre,
                "mood": song.mood,
                "energy": song.energy,
                "tempo_bpm": song.tempo_bpm,
                "valence": song.valence,
                "danceability": song.danceability,
                "acousticness": song.acousticness,
            }
            user_dict = {
                "genre": user.favorite_genre,
                "mood": user.favorite_mood,
                "energy": user.target_energy,
                "likes_acoustic": user.likes_acoustic,
            }
            _, score, _ = _score_song(user_dict, song_dict)
            scored.append((song, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        song_dict = {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "genre": song.genre,
            "mood": song.mood,
            "energy": song.energy,
            "tempo_bpm": song.tempo_bpm,
            "valence": song.valence,
            "danceability": song.danceability,
            "acousticness": song.acousticness,
        }
        user_dict = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        _, _, explanation = _score_song(user_dict, song_dict)
        return explanation


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def _score_song(user: Dict, song: Dict) -> Tuple[Dict, float, str]:
    """
    Scores a single song against a user profile.
    Returns (song, score, explanation).

    Weights (total = 1.0):
      genre_match   0.35  — binary exact match
      mood_match    0.30  — binary exact match
      energy_fit    0.20  — proximity: 1 - |target - song|
      valence_fit   0.10  — inferred target valence from mood
      acoustic_fit  0.05  — direction depends on likes_acoustic
    """
    reasons = []

    # --- genre (0.35) ---
    genre_match = 1.0 if song["genre"] == user["genre"] else 0.0
    if genre_match:
        reasons.append(f"genre matches '{song['genre']}'")

    # --- mood (0.30) ---
    mood_match = 1.0 if song["mood"] == user["mood"] else 0.0
    if mood_match:
        reasons.append(f"mood matches '{song['mood']}'")

    # --- energy fit (0.20) ---
    energy_diff = abs(user["energy"] - song["energy"])
    energy_fit = 1.0 - energy_diff
    if energy_diff <= 0.10:
        reasons.append(f"energy is a close match ({song['energy']:.2f} vs target {user['energy']:.2f})")
    elif energy_diff <= 0.25:
        reasons.append(f"energy is nearby ({song['energy']:.2f} vs target {user['energy']:.2f})")

    # --- valence fit (0.10) — infer target valence from mood ---
    mood_to_valence = {
        "happy": 0.85, "uplifting": 0.80, "playful": 0.78, "romantic": 0.72,
        "relaxed": 0.68, "peaceful": 0.65, "nostalgic": 0.60, "focused": 0.58,
        "chill": 0.55, "moody": 0.45, "dark": 0.30, "melancholic": 0.25,
        "intense": 0.40, "energetic": 0.70,
    }
    target_valence = mood_to_valence.get(user["mood"], 0.55)
    valence_diff = abs(target_valence - song["valence"])
    valence_fit = 1.0 - valence_diff
    if valence_diff <= 0.15:
        reasons.append(f"mood tone (valence {song['valence']:.2f}) fits the '{user['mood']}' vibe")

    # --- acousticness fit (0.05) ---
    if user["likes_acoustic"]:
        acoustic_fit = song["acousticness"]
        if song["acousticness"] >= 0.60:
            reasons.append(f"acoustic texture matches preference (acousticness {song['acousticness']:.2f})")
    else:
        acoustic_fit = 1.0 - song["acousticness"]
        if song["acousticness"] <= 0.30:
            reasons.append(f"produced/electronic sound fits preference (acousticness {song['acousticness']:.2f})")

    score = (genre_match * 0.35
             + mood_match * 0.30
             + energy_fit * 0.20
             + valence_fit * 0.10
             + acoustic_fit * 0.05)

    if not reasons:
        reasons.append("partial match on audio features")

    explanation = "; ".join(reasons)
    return (song, round(score, 4), explanation)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored = [_score_song(user_prefs, song) for song in songs]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
