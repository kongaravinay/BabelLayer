"""
Semantic field mapper for finding the best matching target field for each
source field.

The matcher can use sentence vectors when available, and falls back to a
token-based lexical score when vector dependencies are not available.
"""
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
import re
import os
from difflib import SequenceMatcher

from config import EMBEDDING_MODEL, MAPPING_MIN_CONFIDENCE, USE_EMBEDDINGS

log = logging.getLogger(__name__)


class SchemaMapper:

    def __init__(self, model_name: str = None):
        name = model_name or EMBEDDING_MODEL
        self._model = None
        self._model_name = name
        self._backend = "lexical"

        if not self._should_try_embeddings():
            log.info("Embedding backend disabled; using lexical matcher")
            return

        try:
            # Lazy import keeps the app usable when torch DLLs are unavailable.
            from sentence_transformers import SentenceTransformer  # type: ignore
            log.info("Loading embedding model: %s", name)
            self._model = SentenceTransformer(name)
            self._backend = "embeddings"
        except Exception as exc:
            log.warning(
                "Embedding model unavailable (%s). Falling back to lexical matcher.",
                exc,
            )

    @staticmethod
    def _should_try_embeddings() -> bool:
        if USE_EMBEDDINGS in {"1", "true", "yes", "on"}:
            return True
        if USE_EMBEDDINGS in {"0", "false", "no", "off"}:
            return False
        return os.name != "nt"

    # -- Core API -------------------------------------------------------------

    def suggest_mappings(self, source_fields, target_fields, threshold=None):
        """
        For each source field, find the best-matching target field.
        Returns a list of dicts: {source_field, target_field, confidence, suggested}.
        Only includes matches above the confidence threshold.
        """
        if not source_fields or not target_fields:
            return []

        threshold = threshold or MAPPING_MIN_CONFIDENCE
        sim_matrix = self._similarity_matrix(source_fields, target_fields)

        suggestions = []
        for i, src in enumerate(source_fields):
            best_j = int(np.argmax(sim_matrix[i]))
            score = float(sim_matrix[i, best_j])
            if score >= threshold:
                suggestions.append({
                    "source_field": src,
                    "target_field": target_fields[best_j],
                    "confidence": score,
                    "suggested": True,
                    "ai_suggested": True,
                })

        log.info("Mapped %d of %d source fields (threshold %.0f%%)",
                 len(suggestions), len(source_fields), threshold * 100)
        return suggestions

    def field_similarity(self, field_a: str, field_b: str) -> float:
        """Cosine similarity between two individual field names."""
        if self._model is not None:
            vecs = self._model.encode([field_a, field_b])
            return float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])
        return self._lexical_similarity(field_a, field_b)

    # -- Internals ------------------------------------------------------------

    def _similarity_matrix(self, source_fields, target_fields):
        if self._model is not None:
            src_vecs = self._model.encode(source_fields)
            tgt_vecs = self._model.encode(target_fields)
            return cosine_similarity(src_vecs, tgt_vecs)

        matrix = np.zeros((len(source_fields), len(target_fields)), dtype=float)
        for i, src in enumerate(source_fields):
            for j, tgt in enumerate(target_fields):
                matrix[i, j] = self._lexical_similarity(src, tgt)
        return matrix

    def _lexical_similarity(self, field_a: str, field_b: str) -> float:
        """Score similarity in [0, 1] using token overlap + string ratio."""
        a_tokens = set(self._canonical_tokens(field_a))
        b_tokens = set(self._canonical_tokens(field_b))

        if not a_tokens or not b_tokens:
            token_score = 0.0
        else:
            token_score = len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

        ratio = SequenceMatcher(None, str(field_a).lower(), str(field_b).lower()).ratio()
        return float(0.65 * token_score + 0.35 * ratio)

    @staticmethod
    def _tokenize(value: str):
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value))
        text = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
        return [t for t in text.split() if t]

    @staticmethod
    def _canonical_tokens(value: str):
        synonyms = {
            "client": "customer",
            "customers": "customer",
            "clients": "customer",
            "telephone": "phone",
            "mobile": "phone",
            "mail": "email",
            "addr": "address",
            "qty": "quantity",
            "num": "number",
            "identifier": "id",
        }
        out = []
        for token in SchemaMapper._tokenize(value):
            out.append(synonyms.get(token, token))
        return out
