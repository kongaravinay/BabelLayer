import numpy as np
import logging
import os
from difflib import SequenceMatcher
from sklearn.metrics.pairwise import cosine_similarity

from config import EMBEDDING_MODEL, MAPPING_MIN_CONFIDENCE, USE_EMBEDDINGS

log = logging.getLogger(__name__)


class FieldMatcher:
    """Matches field names across datasets using semantic or lexical similarity."""

    def __init__(self, model_name: str | None = None):
        self.model = None
        self.using_embeddings = False

        # Try to load semantic embeddings if available
        if self._can_use_embeddings():
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                model_to_load = model_name or EMBEDDING_MODEL
                log.info("Loading embedding model: %s", model_to_load)
                self.model = SentenceTransformer(model_to_load)
                self.using_embeddings = True
            except Exception as e:
                log.warning("Could not load embeddings (%s); using text-based matching", e)
        else:
            log.info("Embeddings disabled; using text-based field matching")

    @staticmethod
    def _can_use_embeddings() -> bool:
        """Check if embeddings should be used on this system."""
        if USE_EMBEDDINGS in {"1", "true", "yes", "on"}:
            return True
        if USE_EMBEDDINGS in {"0", "false", "no", "off"}:
            return False
        # Don't use on Windows by default due to torch dependency issues
        return os.name != "nt"

    # -- Core API -------------------------------------------------------------

    def suggest_mappings(
        self,
        source_fields: list[str],
        target_fields: list[str],
        threshold: float | None = None,
    ) -> list[dict]:
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

    def _similarity_matrix(self, source_fields: list[str], target_fields: list[str]) -> np.ndarray:
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
    def _tokenize(value: str) -> list[str]:
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value))
        text = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
        return [t for t in text.split() if t]

    @staticmethod
    def _canonical_tokens(value: str) -> list[str]:
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
        for token in FieldMatcher._tokenize(value):
            out.append(synonyms.get(token, token))
        return out
