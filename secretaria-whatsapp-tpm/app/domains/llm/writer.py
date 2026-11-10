"""Redator LLM + RAG. Entra DEPOIS do turno grounded (process_turn) e só reescreve o tom.

Modos (config/llm.json ou LLM_MODE):
- off:    nada muda.
- shadow: o LLM roda, o paciente recebe o template; comparação em turn["llm"] e no log de sombra.
- on:     o paciente recebe o texto do LLM somente se o verificador aprovar; senão, o template.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.domains.llm import claim_checker
from app.domains.training.anonymizer import anonymize
from app.infrastructure.config.config_loader import _config_dir
from app.infrastructure.llm.providers import LLMError, build_provider, load_llm_config
from app.infrastructure.rag.vector_store import VectorStore

_STORE_CACHE: Dict[str, VectorStore] = {}


def _store(cfg: dict) -> VectorStore:
    path = cfg.get("rag", {}).get("index_path", "data/rag/index.json")
    if path not in _STORE_CACHE:
        _STORE_CACHE[path] = VectorStore.load(path)
    return _STORE_CACHE[path]


def reset_cache() -> None:
    _STORE_CACHE.clear()


def build_prompt(patient_message: str, base_reply: str, examples: List[Dict], intent: str) -> str:
    lines = ["EXEMPLOS REAIS DA CLÍNICA (tom a imitar; dados ocultos entre chaves):"]
    if examples:
        for ex in examples:
            lines.append(f"- Paciente: {ex['patient']}\n  Secretária: {ex['reply']}")
    else:
        lines.append("- (sem exemplos aprovados ainda)")
    lines += [
        "",
        f"INTENÇÃO DETECTADA: {intent}",
        f"MENSAGEM DO PACIENTE (anonimizada): {patient_message}",
        "",
        f"RESPOSTA-BASE:\n{base_reply}",
        "",
        "Reescreva a RESPOSTA-BASE no tom dos exemplos, sem acrescentar nenhum fato.",
    ]
    return "\n".join(lines)


def _eligible(turn: Dict, cfg: dict) -> Optional[str]:
    intent = turn.get("intent")
    if intent in set(cfg.get("never_rewrite", [])):
        return f"intenção {intent} usa texto fixo"
    if (turn.get("escalation") or {}).get("needed"):
        return "escalonamento usa texto fixo"
    if (turn.get("session") or {}).get("opt_out"):
        return "opt-out usa texto fixo"
    if intent not in set(cfg.get("rewrite_intents", [])):
        return f"intenção {intent} fora da lista de reescrita"
    return None


def apply_llm(turn: Dict, message: str, provider=None, store: Optional[VectorStore] = None, cfg: Optional[dict] = None) -> Dict:
    cfg = cfg or load_llm_config()
    mode = cfg.get("mode", "off")
    if mode not in {"shadow", "on"}:
        return turn
    base = turn.get("reply_text") or ""
    info: Dict = {"mode": mode, "used": False, "base_reply": base}
    skip = _eligible(turn, cfg)
    if skip:
        info["skipped"] = skip
        turn["llm"] = info
        return turn

    started = time.monotonic()
    try:
        provider = provider or build_provider(cfg)
        store = store if store is not None else _store(cfg)
        safe_msg = anonymize(message)
        examples: List[Dict] = []
        same_space = store.meta.get("provider") in (None, getattr(provider, "name", None))
        if not same_space:
            info["rag"] = f"índice feito com '{store.meta.get('provider')}', provedor atual '{provider.name}': reindexe"
        if store.items and same_space:
            rag = cfg.get("rag", {})
            vec = provider.embed([safe_msg])[0]
            examples = store.search(vec, top_k=int(rag.get("top_k", 4)), min_score=float(rag.get("min_score", 0.0)), intent=turn.get("intent"))
        prompt = build_prompt(safe_msg, base, examples, turn.get("intent", "UNKNOWN"))
        system = "\n".join(cfg.get("system_rules", []))
        candidate = provider.generate(system, prompt, float(cfg.get("temperature", 0.3)))
    except LLMError as exc:
        info.update(error=str(exc), duration_ms=int((time.monotonic() - started) * 1000))
        turn["llm"] = info
        turn.setdefault("trace", []).append({"step": "llm", "result": "erro", "why": "LLM indisponível: ficou o template"})
        _shadow_log(cfg, turn, message, info)
        return turn

    verdict = claim_checker.check(candidate, base, int(cfg.get("max_output_chars", 320)))
    info.update(
        candidate=candidate,
        check=verdict,
        examples=[{"id": e["id"], "score": e["score"]} for e in examples],
        duration_ms=int((time.monotonic() - started) * 1000),
        provider=getattr(provider, "name", "?"),
    )
    if mode == "on" and verdict["ok"]:
        turn["reply_text"] = candidate
        info["used"] = True
    turn["llm"] = info
    turn.setdefault("trace", []).append(
        {
            "step": "llm",
            "result": "usado" if info["used"] else ("sombra" if mode == "shadow" else "bloqueado"),
            "why": "texto reescrito no tom da clínica e aprovado pelo verificador"
            if info["used"]
            else ("; ".join(verdict["problems"]) or "modo sombra: paciente recebe o template"),
        }
    )
    _shadow_log(cfg, turn, message, info)
    return turn


def _shadow_log(cfg: dict, turn: Dict, message: str, info: Dict) -> None:
    path = cfg.get("shadow_log_path")
    if not path:
        return
    p = Path(path)
    if not p.is_absolute():
        p = _config_dir().parent / p
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "intent": turn.get("intent"),
            "message": anonymize(message),
            "base": info.get("base_reply"),
            "candidate": info.get("candidate"),
            "ok": (info.get("check") or {}).get("ok"),
            "problems": (info.get("check") or {}).get("problems"),
            "used": info.get("used"),
            "error": info.get("error"),
        }
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass
