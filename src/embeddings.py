"""
Build, save, and load sentence-transformer embeddings for the song catalog.
"""

import pickle
import numpy as np
from src.models import Song


def build_embeddings(songs: list[Song], model_name: str) -> np.ndarray:
    from sentence_transformers import SentenceTransformer  # lazy: heavy dep
    model = SentenceTransformer(model_name)
    # Prepend language + genre so the embedding space has explicit language signal.
    # Without this, descriptions never mention "Telugu" or "Hindi", so queries
    # like "Telugu chill songs" can't match on language through cosine similarity alone.
    texts = [
        f"{song.language.capitalize()} {song.genre}. {song.description}"
        for song in songs
    ]
    return model.encode(texts, show_progress_bar=True, convert_to_numpy=True)


def save_embeddings(embeddings: np.ndarray, path: str) -> None:
    with open(path, "wb") as f:
        pickle.dump(embeddings, f)


def load_embeddings(path: str) -> np.ndarray:
    with open(path, "rb") as f:
        return pickle.load(f)


def embed_query(text: str, model) -> np.ndarray:
    return model.encode([text], convert_to_numpy=True)[0]
