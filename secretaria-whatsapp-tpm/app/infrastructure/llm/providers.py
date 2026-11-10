"""Provedores de LLM/embeddings. Gemini via REST (sem SDK) e um provedor falso para testes offline."""

import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.request
from typing import List, Optional, Protocol

from app.infrastructure.config.config_loader import load_json

_BASE = "https://generativelanguage.googleapis.com/v1beta"


class LLMError(RuntimeError):
    pass


class LLMProvider(Protocol):
    name: str

    def generate(self, system: str, prompt: str, temperature: float = 0.3) -> str: ...

    def embed(self, texts: List[str]) -> List[List[float]]: ...


def load_llm_config() -> dict:
    cfg = load_json("llm.json")
    cfg["mode"] = os.getenv("LLM_MODE", cfg.get("mode", "off")).lower()
    cfg["model"] = os.getenv("GEMINI_MODEL", cfg.get("model"))
    cfg["embedding_model"] = os.getenv("GEMINI_EMBEDDING_MODEL", cfg.get("embedding_model"))
    cfg["provider"] = os.getenv("LLM_PROVIDER", cfg.get("provider", "gemini")).lower()
    return cfg


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, embedding_model: str, timeout: float = 8.0):
        if not api_key:
            raise LLMError("GEMINI_API_KEY não configurada")
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model
        self.timeout = timeout

    def _post(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(
            f"{_BASE}/{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise LLMError(f"Gemini HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMError(f"Gemini indisponível: {exc}") from exc

    def generate(self, system: str, prompt: str, temperature: float = 0.3) -> str:
        data = self._post(
            f"models/{self.model}:generateContent",
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": 256},
            },
        )
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"resposta sem texto: {str(data)[:200]}") from exc
        return "".join(p.get("text", "") for p in parts).strip()

    def embed(self, texts: List[str]) -> List[List[float]]:
        model = f"models/{self.embedding_model}"
        data = self._post(
            f"{model}:batchEmbedContents",
            {
                "requests": [
                    {"model": model, "content": {"parts": [{"text": t}]}, "taskType": "SEMANTIC_SIMILARITY"}
                    for t in texts
                ]
            },
        )
        return [e["values"] for e in data.get("embeddings", [])]

    def list_models(self) -> List[str]:
        req = urllib.request.Request(f"{_BASE}/models?pageSize=200", headers={"x-goog-api-key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            raise LLMError(f"Gemini indisponível: {exc}") from exc
        return [m.get("name", "").replace("models/", "") for m in data.get("models", [])]


class FakeProvider:
    """Offline e determinístico. `generate` devolve a RESPOSTA-BASE (ou `script`, para testes adversariais)."""

    name = "fake"

    def __init__(self, script: Optional[str] = None, dim: int = 256):
        self.script = script
        self.dim = dim
        self.calls: List[str] = []

    def generate(self, system: str, prompt: str, temperature: float = 0.3) -> str:
        self.calls.append(prompt)
        if self.script is not None:
            return self.script
        match = re.search(r"RESPOSTA-BASE:\n(.*?)\n(?:\n|$)", prompt, re.DOTALL)
        return match.group(1).strip() if match else ""

    def embed(self, texts: List[str]) -> List[List[float]]:
        out = []
        for text in texts:
            vec = [0.0] * self.dim
            words = re.findall(r"\w+", text.lower())
            grams = words + [f"{a}_{b}" for a, b in zip(words, words[1:])]
            for g in grams:
                h = int(hashlib.md5(g.encode()).hexdigest(), 16)
                vec[h % self.dim] += 1.0 if (h >> 8) & 1 else -1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out


def build_provider(cfg: Optional[dict] = None) -> LLMProvider:
    cfg = cfg or load_llm_config()
    if cfg.get("provider") == "fake":
        return FakeProvider()
    if cfg.get("provider") != "gemini":
        raise LLMError(f"provedor não suportado: {cfg.get('provider')}")
    return GeminiProvider(
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "",
        model=cfg["model"],
        embedding_model=cfg["embedding_model"],
        timeout=float(cfg.get("timeout_seconds", 8)),
    )
