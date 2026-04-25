"""
Tuneweave CLI entry point.
Run with: python -m src.main
"""

import sys
from pathlib import Path


def _banner():
    print("\n" + "=" * 60)
    print("  Tuneweave — cross-lingual music recommender")
    print("=" * 60)


def _print_recommendations(recs, turn: int) -> None:
    print(f"\n── Turn {turn} picks ─────────────────────────────────────────")
    for i, rec in enumerate(recs, 1):
        s = rec.song
        tags = ", ".join(s.mood_tags[:3])
        print(f"\n  {i}. {s.title}  —  {s.artist}")
        print(f"     [{s.language} · {s.genre} · {s.year or '?'}]  |  mood: {tags}")
        print(f"     ↳ {rec.explanation}")
    print()


def main() -> None:
    """
    1. Load .env, init LLMClient, load catalog + embeddings.
    2. Prompt: "What are you in the mood for?"
    3. Run Session.start, print results.
    4. Loop up to 2 more turns: prompt for refinement, run Session.refine.
    5. On exit, print session summary.
    """
    from dotenv import load_dotenv
    load_dotenv()

    from src.catalog import load_songs
    from src.embeddings import load_embeddings
    from src.llm_client import LLMClient
    from src.logger import save_session, setup_logger
    from src.session import Session

    setup_logger()
    _banner()

    catalog_path = Path("data/songs.csv")
    embeddings_path = Path("data/embeddings.pkl")

    if not embeddings_path.exists():
        print(
            "\n[ERROR] data/embeddings.pkl not found.\n"
            "Build it first:\n"
            "  python scripts/build_embeddings.py\n"
        )
        sys.exit(1)

    print("\nLoading catalog and embeddings...")
    catalog = load_songs(str(catalog_path))
    embeddings = load_embeddings(str(embeddings_path))

    from sentence_transformers import SentenceTransformer
    from src.config import EMBED_MODEL_NAME
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    client = LLMClient()
    session = Session(catalog, embeddings, embed_model, client)

    # ── Turn 1 ────────────────────────────────────────────────────────────────
    print(f"\n{len(catalog)} songs loaded.\n")
    print("What are you in the mood for?")
    print("(e.g. 'chill Telugu songs for studying', 'only Hindi romantic', 'upbeat workout music')\n")

    try:
        query = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        return

    if not query:
        print("No input — goodbye!")
        return

    print("\nSearching...\n")
    recs = session.start(query)
    _print_recommendations(recs, turn=1)

    transcript = [{"turn": 1, "input": query, "picks": [r.song.title for r in recs]}]

    # ── Refinement loop ───────────────────────────────────────────────────────
    while not session.is_complete():
        print("Want to refine? (Enter to skip / 'quit' to exit)")
        print("e.g. 'more acoustic', 'not #1', 'only Telugu', 'something sadder'\n")
        try:
            feedback = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not feedback or feedback.lower() in {"quit", "q", "exit", "done", "no"}:
            break

        print("\nRefining...\n")
        recs = session.refine(feedback)
        turn = session.state().turn
        _print_recommendations(recs, turn=turn)
        transcript.append({"turn": turn, "input": feedback, "picks": [r.song.title for r in recs]})

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=" * 60)
    print("  Session complete. Enjoy the music!")
    print("=" * 60 + "\n")

    save_session({"initial_query": query, "turns": transcript})


if __name__ == "__main__":
    main()
