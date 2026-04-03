"""
Command line runner for the Music Recommender Simulation.
"""

from .recommender import load_songs, recommend_songs


def print_recommendations(recommendations, user_prefs: dict, k: int) -> None:
    genre = user_prefs.get("genre", "?")
    mood  = user_prefs.get("mood", "?")
    energy = user_prefs.get("energy", "?")

    print()
    print("=" * 60)
    print("  MUSIC RECOMMENDER SIMULATION")
    print("=" * 60)
    print(f"  Profile  :  genre={genre}  |  mood={mood}  |  energy={energy}")
    print(f"  Showing  :  top {k} recommendations")
    print("=" * 60)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        bar_len = int(score * 20)
        bar = "#" * bar_len + "-" * (20 - bar_len)

        print()
        print(f"  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Genre: {song['genre']:<14}  Mood: {song['mood']:<12}  Energy: {song['energy']:.2f}  BPM: {int(song['tempo_bpm'])}")
        print(f"       Score: {score:.4f}  [{bar}]")
        print(f"       Why  : {explanation}")

    print()
    print("=" * 60)
    print()


PROFILES = [
    # --- Standard profiles ---
    {
        "label":          "High-Energy Pop",
        "genre":          "pop",
        "mood":           "happy",
        "energy":         0.85,
        "likes_acoustic": False,
    },
    {
        "label":          "Chill Lofi",
        "genre":          "lofi",
        "mood":           "chill",
        "energy":         0.38,
        "likes_acoustic": True,
    },
    {
        "label":          "Deep Intense Rock",
        "genre":          "rock",
        "mood":           "intense",
        "energy":         0.90,
        "likes_acoustic": False,
    },
    # --- Adversarial / edge case profiles ---
    {
        "label":          "Conflicting: High Energy + Melancholic Mood",
        "genre":          "alternative",
        "mood":           "melancholic",
        "energy":         0.92,
        "likes_acoustic": False,
    },
    {
        "label":          "Ghost Genre: Genre Not in Catalog",
        "genre":          "k-pop",
        "mood":           "happy",
        "energy":         0.80,
        "likes_acoustic": False,
    },
    {
        "label":          "Extremes: Maximum Acoustic + Peaceful Ambient",
        "genre":          "ambient",
        "mood":           "peaceful",
        "energy":         0.15,
        "likes_acoustic": True,
    },
    {
        "label":          "Contradictory Acoustic: Likes Acoustic + Metal Genre",
        "genre":          "metal",
        "mood":           "intense",
        "energy":         0.95,
        "likes_acoustic": True,
    },
]


def main() -> None:
    songs = load_songs("data/songs.csv")
    k = 5
    for profile in PROFILES:
        user_prefs = {k: v for k, v in profile.items() if k != "label"}
        label = profile["label"]
        print(f"\n{'#' * 60}")
        print(f"  PROFILE: {label}")
        recommendations = recommend_songs(user_prefs, songs, k=k)
        print_recommendations(recommendations, user_prefs, k)


if __name__ == "__main__":
    main()
