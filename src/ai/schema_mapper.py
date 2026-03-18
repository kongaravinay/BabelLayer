"""
Semantic field mapper — uses sentence-transformer embeddings to find
the best-matching target field for each source field.

The cosine-similarity approach works well for column-name matching because
short, meaningful phrases (like field names) live in a dense embedding space
where semantically similar names cluster together.
"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

from config import EMBEDDING_MODEL, MAPPING_MIN_CONFIDENCE

log = logging.getLogger(__name__)


class SchemaMapper:

    def __init__(self, model_name: str = None):
        name = model_name or EMBEDDING_MODEL
        log.info("Loading embedding model: %s", name)
        self._model = SentenceTransformer(name)

    # -- Core API -------------------------------------------------------------

    def suggest_mappings(self, source_fields, target_fields, threshold=None):
        """
        For each source field, find the best-matching target field.
        Returns a list of dicts: {source_field, target_field, confidence, ai_suggested}.
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
                    "ai_suggested": True,
                })

        log.info("Mapped %d of %d source fields (threshold %.0f%%)",
                 len(suggestions), len(source_fields), threshold * 100)
        return suggestions

    def field_similarity(self, field_a: str, field_b: str) -> float:
        """Cosine similarity between two individual field names."""
        vecs = self._model.encode([field_a, field_b])
        return float(cosine_similarity([vecs[0]], [vecs[1]])[0][0])

    # -- Internals ------------------------------------------------------------

    def _similarity_matrix(self, source_fields, target_fields):
        src_vecs = self._model.encode(source_fields)
        tgt_vecs = self._model.encode(target_fields)
        return cosine_similarity(src_vecs, tgt_vecs)
