"""
CSV loading and validation for the song catalog.
"""

import csv
from src.models import Song


def load_songs(path: str) -> list[Song]:
    songs = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year_str = row.get("year", "").strip()
            song = Song(
                id=int(row["id"]),
                title=row["title"].strip(),
                artist=row["artist"].strip(),
                language=row["language"].strip(),
                genre=row["genre"].strip(),
                mood_tags=[t.strip() for t in row["mood_tags"].split(";") if t.strip()],
                energy=float(row["energy"]),
                tempo_bpm=float(row["tempo_bpm"]),
                valence=float(row["valence"]),
                danceability=float(row["danceability"]),
                acousticness=float(row["acousticness"]),
                year=int(year_str) if year_str else None,
                description=row["description"].strip(),
            )
            songs.append(song)
    return songs


def validate_catalog(songs: list[Song]) -> None:
    """Raises ValueError on missing fields or out-of-range audio features."""
    bounded_fields = ["energy", "valence", "danceability", "acousticness"]
    for song in songs:
        if not song.title:
            raise ValueError(f"Song {song.id}: missing title")
        if not song.artist:
            raise ValueError(f"Song {song.id}: missing artist")
        if not song.language:
            raise ValueError(f"Song {song.id}: missing language")
        if not song.description:
            raise ValueError(f"Song {song.id}: missing description")
        if not song.mood_tags:
            raise ValueError(f"Song {song.id}: missing mood_tags")
        for field_name in bounded_fields:
            val = getattr(song, field_name)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"Song {song.id}: {field_name}={val} out of range [0, 1]"
                )
        if song.tempo_bpm <= 0:
            raise ValueError(f"Song {song.id}: tempo_bpm must be positive")
