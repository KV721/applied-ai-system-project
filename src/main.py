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


def main() -> None:
    songs = load_songs("data/songs.csv")

    user_prefs = {
        "genre":          "pop",
        "mood":           "happy",
        "energy":         0.78,
        "likes_acoustic": False,
    }

    k = 5
    recommendations = recommend_songs(user_prefs, songs, k=k)
    print_recommendations(recommendations, user_prefs, k)


if __name__ == "__main__":
    main()
