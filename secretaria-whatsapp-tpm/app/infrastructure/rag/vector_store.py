"""Índice vetorial local (arquivo JSON, sem dependências). Em produção: pgvector (infra/db/migrations/002)."""

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.infrastructure.config.config_loader import _config_dir


def _resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else _config_dir().parent / path


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class VectorStore:
    def __init__(self, items: Optional[List[Dict]] = None, meta: Optional[Dict] = None):
        self.items = items or []
        self.meta = meta or {}

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        path = _resolve(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data.get("items", []), data.get("meta", {}))

    def save(self, path: str | Path) -> Path:
        path = _resolve(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"meta": self.meta, "items": self.items}, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, pairs: List[Dict], provider, batch: int = 50) -> int:
        self.items = []
        for i in range(0, len(pairs), batch):
            chunk = pairs[i : i + batch]
            vectors = provider.embed([p["patient"] for p in chunk])
            for p, v in zip(chunk, vectors):
                self.items.append({"id": p["id"], "intent": p.get("intent"), "patient": p["patient"], "reply": p["reply"], "vector": v})
        self.meta = {
            "provider": getattr(provider, "name", "?"),
            "embedding_model": getattr(provider, "embedding_model", None),
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(self.items),
        }
        return len(self.items)

    def search(self, vector: List[float], top_k: int = 4, min_score: float = 0.0, intent: Optional[str] = None) -> List[Dict]:
        scored = []
        for item in self.items:
            score = _cosine(vector, item["vector"])
            if intent and item.get("intent") == intent:
                score += 0.05  # leve preferência por exemplos da mesma intenção
            if score >= min_score:
                scored.append({**{k: v for k, v in item.items() if k != "vector"}, "score": round(score, 4)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
