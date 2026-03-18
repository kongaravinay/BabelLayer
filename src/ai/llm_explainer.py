"""
LLM integration for generating human-readable explanations.

Supports two backends:
  - Ollama (local, free, offline)
  - OpenAI (cloud, paid, higher quality)

The backend is chosen in config via LLM_BACKEND.
"""
import requests
import logging
from typing import Optional

from config import LLM_BACKEND, LLM_MODEL, OLLAMA_URL, OPENAI_KEY, OPENAI_MODEL

log = logging.getLogger(__name__)


class Explainer:
    """Wraps an LLM to explain schema mappings and anomalies in plain English."""

    def __init__(self):
        self._backend = LLM_BACKEND
        self._model = LLM_MODEL if self._backend == "ollama" else OPENAI_MODEL

    # -- Public helpers -------------------------------------------------------

    def explain_mapping(self, source: str, target: str, confidence: float) -> Optional[str]:
        prompt = (
            f"Explain why the data field '{source}' maps to '{target}' "
            f"with {confidence:.0%} confidence. Keep it to 1–2 sentences."
        )
        return self._ask(prompt)

    def explain_transformation(self, source: str, target: str, rule: str) -> Optional[str]:
        prompt = (
            f"Explain this data transformation in plain English:\n"
            f"  Source: {source}\n  Target: {target}\n  Rule: {rule}"
        )
        return self._ask(prompt)

    def explain_anomaly(self, field: str, value: str, normal_range: str) -> Optional[str]:
        prompt = (
            f"Why is '{value}' anomalous for the field '{field}'?\n"
            f"Normal range: {normal_range}. One sentence."
        )
        return self._ask(prompt)

    # -- Backend dispatch -----------------------------------------------------

    def _ask(self, prompt: str) -> Optional[str]:
        try:
            if self._backend == "ollama":
                return self._ask_ollama(prompt)
            elif self._backend == "openai":
                return self._ask_openai(prompt)
            else:
                log.error("Unknown LLM backend: %s", self._backend)
                return None
        except Exception as exc:
            log.error("LLM call failed: %s", exc)
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
