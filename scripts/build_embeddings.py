"""
One-time script: compute sentence-transformer embeddings for all songs and save to data/embeddings.pkl.
Run after data/songs.csv is finalized.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import EMBED_MODEL_NAME

CATALOG_PATH = Path("data/songs.csv")
EMBEDDINGS_PATH = Path("data/embeddings.pkl")


def main() -> None:
    from src.catalog import load_songs
    from src.embeddings import build_embeddings, save_embeddings

    print(f"Loading catalog from {CATALOG_PATH}...")
    songs = load_songs(str(CATALOG_PATH))
    print(f"Loaded {len(songs)} songs.")

    print(f"Building embeddings with model '{EMBED_MODEL_NAME}'...")
    embeddings = build_embeddings(songs, EMBED_MODEL_NAME)
    print(f"Embeddings shape: {embeddings.shape}")

    save_embeddings(embeddings, str(EMBEDDINGS_PATH))
    print(f"Saved embeddings to {EMBEDDINGS_PATH}.")


if __name__ == "__main__":
    main()
