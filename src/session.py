"""
Session state management: ties together the full retrieval, ranking, and explanation pipeline.
"""

from src.explainer import explain_batch
from src.llm_client import LLMClient
from src.models import Recommendation, SessionProfile, SessionState, Song
from src.parser import parse_preferences, parse_refinement
from src.ranker import rank
from src.retriever import retrieve

MAX_TURNS = 3
TOP_RETRIEVAL = 40  # larger pool so minority-language songs can reach the ranker
TOP_RESULTS = 5


class Session:
    def __init__(
        self,
        catalog: list[Song],
        embeddings,
        embed_model,
        client: LLMClient,
    ):
        self._catalog = catalog
        self._embeddings = embeddings
        self._embed_model = embed_model
        self._client = client
        self._state: SessionState | None = None

    def start(self, initial_query: str) -> list[Recommendation]:
        self._client.reset_turn_counter()
        profile = parse_preferences(initial_query, self._client)
        recs = self._build_recommendations(profile)
        self._state = SessionState(turn=1, profile=profile, history=[recs])
        return recs

    def refine(self, feedback: str) -> list[Recommendation]:
        if self._state is None:
            raise RuntimeError("Call start() before refine()")
        if self.is_complete():
            raise RuntimeError("Session is already complete — max turns reached")

        self._client.reset_turn_counter()
        shown = [r.song for r in self._state.history[-1]]
        updated_profile = parse_refinement(
            feedback, self._state.profile, shown, self._client
        )
        recs = self._build_recommendations(updated_profile)
        self._state.turn += 1
        self._state.profile = updated_profile
        self._state.history.append(recs)
        return recs

    def is_complete(self) -> bool:
        return self._state is not None and self._state.turn >= MAX_TURNS

    def state(self) -> SessionState | None:
        return self._state

    def _build_recommendations(self, profile: SessionProfile) -> list[Recommendation]:
        candidates = retrieve(
            profile,
            self._catalog,
            self._embeddings,
            self._embed_model,
            top_k=TOP_RETRIEVAL,
        )
        ranked = rank(candidates, profile, top_k=TOP_RESULTS)
        songs = [rec.song for rec in ranked]
        explanations = explain_batch(songs, profile, self._client)
        return [
            Recommendation(
                song=rec.song,
                retrieval_score=rec.retrieval_score,
                ranking_score=rec.ranking_score,
                explanation=explanations.get(rec.song.id, rec.song.description),
            )
            for rec in ranked
        ]
