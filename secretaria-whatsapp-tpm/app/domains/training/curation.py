"""Curadoria humana dos pares. Só `aprovado` entra no índice RAG e no dataset de fine-tuning."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from app.domains.llm.facts import find_facts, mask_facts
from app.domains.training.anonymizer import leaks

STATUSES = {"pendente", "aprovado", "rejeitado", "bloqueado"}
CSV_FIELDS = ["id", "split", "status", "intent", "flags", "patient", "reply", "reviewer", "note"]


def load(path: str | Path) -> List[Dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def save(path: str | Path, pairs: Iterable[Dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for p in pairs:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")


def can_approve(pair: Dict, reply: Optional[str] = None) -> Optional[str]:
    """Devolve o motivo de recusa, ou None se pode aprovar."""
    reply = pair["reply"] if reply is None else reply
    if pair.get("status") == "bloqueado" or "clinico" in (pair.get("flags") or []):
        return "par clínico: não pode virar exemplo de resposta"
    if leaks(pair.get("patient", "")) or leaks(reply):
        return "ainda há dado pessoal; edite antes de aprovar"
    if "conselho_clinico" in find_facts(reply):
        return "a resposta contém orientação clínica"
    return None


def review(pair: Dict, status: str, reviewer: str, reply: Optional[str] = None, note: Optional[str] = None) -> Dict:
    if status not in STATUSES - {"bloqueado"}:
        raise ValueError(f"status inválido: {status}")
    if not reviewer:
        raise ValueError("informe quem revisou (LGPD/auditoria)")
    updated = dict(pair)
    if reply is not None:
        updated["reply"] = mask_facts(reply)
    if status == "aprovado":
        reason = can_approve(updated)
        if reason:
            raise ValueError(reason)
    updated.update(status=status, reviewer=reviewer, reviewed_at=datetime.now().isoformat(timespec="seconds"))
    if note is not None:
        updated["note"] = note
    return updated


def approved(pairs: Iterable[Dict], split: Optional[str] = "treino") -> List[Dict]:
    return [p for p in pairs if p.get("status") == "aprovado" and (split is None or p.get("split") == split)]


def stats(pairs: List[Dict]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for p in pairs:
        out.setdefault(p.get("split", "?"), {}).setdefault(p.get("status", "?"), 0)
        out[p["split"]][p["status"]] += 1
    return out


def export_csv(pairs: Iterable[Dict], path: str | Path) -> int:
    """Planilha para a dra/secretária revisar no Excel (separador ';', UTF-8 com BOM)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, delimiter=";")
        writer.writeheader()
        for p in pairs:
            row = {k: p.get(k) for k in CSV_FIELDS}
            row["flags"] = ",".join(p.get("flags") or [])
            writer.writerow(row)
            n += 1
    return n


def import_csv(pairs: List[Dict], path: str | Path, default_reviewer: str = "") -> Dict[str, int]:
    """Aplica status/resposta editados na planilha. Linhas inválidas são relatadas, não aplicadas."""
    by_id = {p["id"]: i for i, p in enumerate(pairs)}
    result = {"aplicados": 0, "ignorados": 0, "recusados": 0}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            idx = by_id.get(row.get("id", ""))
            status = (row.get("status") or "").strip().lower()
            if idx is None or status not in STATUSES or status == pairs[idx]["status"] and row.get("reply") == pairs[idx]["reply"]:
                result["ignorados"] += 1
                continue
            if status == "bloqueado":
                result["ignorados"] += 1
                continue
            try:
                pairs[idx] = review(
                    pairs[idx],
                    status,
                    (row.get("reviewer") or default_reviewer).strip(),
                    reply=row.get("reply"),
                    note=row.get("note") or None,
                )
                result["aplicados"] += 1
            except ValueError:
                result["recusados"] += 1
    return result
