"""Transforma conversas em pares (mensagem do paciente → resposta da clínica) para curadoria.

Regras:
- mensagens seguidas do mesmo autor viram um único turno;
- só pareia turno do paciente com a resposta da clínica que vem logo depois (até `max_gap_hours`);
- tudo é anonimizado e os fatos da resposta são mascarados ({HORARIO}, {PRECO}...);
- par com assunto clínico vem como `bloqueado` (a secretária nunca orienta: a equipe assume);
- ~10% dos pares vão para `avaliacao` (fixo por hash) e nunca entram no índice nem no treino.
"""

import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from app.domains.appointments.intent_classifier import classify_intent, is_clinical_text
from app.domains.llm.facts import find_facts, fold, mask_facts
from app.domains.training.anonymizer import anonymize, leaks
from app.domains.training.whatsapp_export import ChatMessage
from app.infrastructure.config.config_loader import load_guardrails

PATIENT = "paciente"
CLINIC = "clinica"


@dataclass
class Turn:
    role: str
    text: str
    when: object
    media: int = 0


def _is_clinic(author: str, clinic_authors: Sequence[str]) -> bool:
    a = fold(author)
    return any(fold(c) and fold(c) in a for c in clinic_authors)


def group_turns(messages: Iterable[ChatMessage], clinic_authors: Sequence[str]) -> List[Turn]:
    turns: List[Turn] = []
    for msg in messages:
        role = CLINIC if _is_clinic(msg.author, clinic_authors) else PATIENT
        if turns and turns[-1].role == role:
            last = turns[-1]
            if msg.kind == "text" and msg.text:
                last.text = f"{last.text}\n{msg.text}".strip()
            elif msg.kind == "media":
                last.media += 1
            last.when = msg.when or last.when
            continue
        turns.append(Turn(role=role, text=msg.text if msg.kind == "text" else "", when=msg.when, media=int(msg.kind == "media")))
    return turns


def _split(pair_id: str, eval_ratio: float) -> str:
    bucket = int(hashlib.sha256(pair_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "avaliacao" if bucket < eval_ratio else "treino"


def build_pairs(
    messages: List[ChatMessage],
    clinic_authors: Sequence[str],
    extra_names: Sequence[str] = (),
    max_gap_hours: float = 12.0,
    eval_ratio: float = 0.1,
    source: str = "",
) -> List[Dict]:
    patient_names = {m.author for m in messages if not _is_clinic(m.author, clinic_authors)}
    names = list(patient_names) + list(clinic_authors) + list(extra_names)
    keywords = load_guardrails().get("guardrails", {}).get("clinical_escalate_keywords", [])
    turns = group_turns(messages, clinic_authors)
    pairs: List[Dict] = []
    for prev, nxt in zip(turns, turns[1:]):
        if prev.role != PATIENT or nxt.role != CLINIC:
            continue
        if not prev.text.strip() or not nxt.text.strip():
            continue
        if prev.when and nxt.when and (nxt.when - prev.when).total_seconds() > max_gap_hours * 3600:
            continue
        patient = anonymize(prev.text, names)
        reply_anon = anonymize(nxt.text, names)
        facts = find_facts(reply_anon)
        clinical = is_clinical_text(patient, keywords) or "conselho_clinico" in facts
        pid = hashlib.sha256(f"{source}|{prev.when}|{patient}|{reply_anon}".encode()).hexdigest()[:16]
        pairs.append(
            {
                "id": pid,
                "source": source,
                "when": prev.when.isoformat() if prev.when else None,
                "patient": patient,
                "reply_original": reply_anon,
                "reply": mask_facts(reply_anon),
                "intent": classify_intent(patient)["intent"],
                "facts": sorted(facts),
                "flags": sorted(
                    set(["clinico"] if clinical else [])
                    | (set(["dado_pessoal"]) if leaks(patient) or leaks(reply_anon) else set())
                    | (set(["midia"]) if prev.media or nxt.media else set())
                ),
                "split": _split(pid, eval_ratio),
                "status": "bloqueado" if clinical else "pendente",
                "reviewer": None,
                "reviewed_at": None,
                "note": "assunto clínico: a secretária não orienta, só encaminha" if clinical else None,
            }
        )
    return pairs


def dedupe(pairs: Iterable[Dict], existing_ids: Optional[set] = None) -> List[Dict]:
    seen = set(existing_ids or ())
    out = []
    for p in pairs:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        out.append(p)
    return out
