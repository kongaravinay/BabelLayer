"""
Text explanation service for mapping and anomaly summaries.

Supports two backends:
    - Ollama (local, free, offline)
    - OpenAI (cloud, paid)

The backend is selected using config value LLM_BACKEND.
"""
import requests
import logging
from typing import Optional

from config import LLM_BACKEND, LLM_MODEL, OLLAMA_URL, OPENAI_KEY, OPENAI_MODEL

log = logging.getLogger(__name__)


class Explainer:
    """Generates concise explanations for mappings and anomalies."""

    def __init__(self):
        self._backend = LLM_BACKEND
        self._model = LLM_MODEL if self._backend == "ollama" else OPENAI_MODEL

    # -- Public helpers -------------------------------------------------------

    def explain_mapping(self, source: str, target: str, confidence: float) -> Optional[str]:
        prompt = (
            f"Explain why the data field '{source}' maps to '{target}' "
            f"with {confidence:.0%} confidence. Keep it to 1–2 sentences."
        )
        response = self._ask(prompt)
        if response:
            return response
        return self._fallback_mapping(source, target, confidence)

    def explain_transformation(self, source: str, target: str, rule: str) -> Optional[str]:
        prompt = (
            f"Explain this data transformation in plain English:\n"
            f"  Source: {source}\n  Target: {target}\n  Rule: {rule}"
        )
        response = self._ask(prompt)
        if response:
            return response
        return self._fallback_transformation(source, target, rule)

    def explain_anomaly(self, field: str, value: str, normal_range: str) -> Optional[str]:
        prompt = (
            f"Why is '{value}' anomalous for the field '{field}'?\n"
            f"Normal range: {normal_range}. One sentence."
        )
        response = self._ask(prompt)
        if response:
            return response
        return self._fallback_anomaly(field, value, normal_range)

    # -- Backend dispatch -----------------------------------------------------

    def _ask(self, prompt: str) -> Optional[str]:
        try:
            if self._backend == "ollama":
                return self._ask_ollama(prompt)
            elif self._backend == "openai":
                return self._ask_openai(prompt)
            else:
                log.error("Unknown explanation backend: %s", self._backend)
                return None
        except Exception as exc:
            log.error("Explanation call failed: %s", exc)
            return None

    def _ask_ollama(self, prompt: str) -> Optional[str]:
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=30,
            )
            if resp.ok:
                return resp.json().get("response", "").strip()
            log.error("Ollama HTTP %d", resp.status_code)
        except requests.ConnectionError:
            log.warning("Ollama not reachable — is it running?")
        return None

    def _ask_openai(self, prompt: str) -> Optional[str]:
        if not OPENAI_KEY:
            log.error("OPENAI_API_KEY not set")
            return None

        import openai
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a concise data-engineering assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()

    @staticmethod
    def _fallback_mapping(source: str, target: str, confidence: float) -> str:
        if confidence >= 0.8:
            level = "high"
        elif confidence >= 0.6:
            level = "moderate"
        else:
            level = "low"

        return (
            f"'{source}' and '{target}' appear semantically related based on token and naming similarity. "
            f"The current match confidence is {confidence:.0%} ({level}), so review field values before finalizing."
        )

    @staticmethod
    def _fallback_transformation(source: str, target: str, rule: str) -> str:
        return (
            f"The transformation copies data from '{source}' into '{target}' and applies rule '{rule}' "
            "to normalize format so downstream reporting stays consistent."
        )

    @staticmethod
    def _fallback_anomaly(field: str, value: str, normal_range: str) -> str:
        return (
            f"Value '{value}' in field '{field}' is flagged because it deviates from the expected range "
            f"({normal_range}) relative to the rest of the dataset."
        )
