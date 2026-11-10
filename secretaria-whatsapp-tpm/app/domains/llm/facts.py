"""Detectores de "fatos" que a secretária nunca pode inventar.

Usados em dois lugares:
- treino: mascarar fatos nas respostas reais ({HORARIO}, {PRECO}...) para o modelo aprender o tom, não o dado;
- runtime: o verificador bloqueia qualquer fato na saída do LLM que não estava na resposta-base.
"""

import re
import unicodedata
from typing import Dict, List

from app.infrastructure.config.config_loader import load_clinic


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", (text or "").lower()) if unicodedata.category(c) != "Mn")


_TIME = re.compile(r"\b(?:[01]?\d|2[0-3])(?::[0-5]\d(?:h|hs)?|h(?:[0-5]\d)?|hs|\s?horas?)(?!\w)", re.IGNORECASE)
_DATE = re.compile(
    r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{1,2}\s+de\s+(?:janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b",
    re.IGNORECASE,
)
_WEEKDAY = re.compile(r"\b(?:segunda|ter[cç]a|quarta|quinta|sexta)(?:-feira)?\b|\bs[aá]bado\b|\bdomingo\b|\bamanh[aã]\b|\bdepois de amanh[aã]\b", re.IGNORECASE)
_PRICE = re.compile(r"R\$\s?\d[\d.,]*|\b\d[\d.,]*\s?(?:reais|conto)\b|\b(?:parcel\w+|[àa] vista|pix|desconto|\d+x\b)", re.IGNORECASE)
_PROCEDURE = re.compile(
    r"\b(?:botox|toxina|botul\w*|preenchiment\w*|[aá]cido hialur\w*|bioestimulador\w*|sculptra|radiesse|fios? de pdo|fios? de sustenta\w*|"
    r"lipo\w* de papada|enzima\w*|rinomodela\w*|bichect\w*|skinbooster\w*|peeling\w*|microagulh\w*|harmoniza\w* facial)\b",
    re.IGNORECASE,
)
_CLINICAL = re.compile(
    r"\b(?:tom[ea]r?|tomando|use|usar|passe|passar|aplique|aplicar)\b[^.!?\n]{0,40}\b(?:rem[eé]dio|medica\w*|dipirona|paracetamol|ibuprofeno|anti-?inflamat\w*|antibi[oó]tic\w*|pomada|gelo|compressa|corticoide|antial[eé]rgic\w*)"
    r"|\b(?:[eé] normal|n[aã]o se preocupe|vai passar|deve passar|[eé] esperado)\b",
    re.IGNORECASE,
)
_COMMITMENT = re.compile(r"\b(?:agendad[oa]|marcad[oa]|confirmad[oa]|reservad[oa]|cancelad[oa]|remarcad[oa])\b", re.IGNORECASE)
_CONTACT = re.compile(r"\[(?:TELEFONE|EMAIL|LINK|ENDERECO)\]|\b\d{4,5}-?\d{4}\b|@\w|https?://", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\{[A-Z_]+\}|\[[A-Z_]+\]")


def _city_pattern() -> re.Pattern:
    names = set()
    for unit in load_clinic().get("units", []):
        names.add(unit.get("city", ""))
        names.update(unit.get("aliases", []))
    names = sorted((n for n in names if len(n) > 2), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(n) for n in names) + r")\b", re.IGNORECASE)


def detectors() -> Dict[str, re.Pattern]:
    return {
        "horario": _TIME,
        "data": _DATE,
        "dia": _WEEKDAY,
        "preco": _PRICE,
        "procedimento": _PROCEDURE,
        "cidade": _city_pattern(),
        "conselho_clinico": _CLINICAL,
        "compromisso": _COMMITMENT,
        "contato": _CONTACT,
    }


def find_facts(text: str) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {}
    for name, pattern in detectors().items():
        hits = [m.group(0).strip() for m in pattern.finditer(text or "")]
        if hits:
            found[name] = hits
    return found


# Máscara usada no corpus de treino/RAG. Conselho clínico não é mascarado: o par é bloqueado.
_MASKS = [
    ("preco", "{PRECO}"),
    ("data", "{DATA}"),
    ("horario", "{HORARIO}"),
    ("dia", "{DIA}"),
    ("cidade", "{CIDADE}"),
    ("procedimento", "{PROCEDIMENTO}"),
]


def mask_facts(text: str) -> str:
    out = text or ""
    det = detectors()
    for name, token in _MASKS:
        out = det[name].sub(token, out)
    return out


def has_placeholder(text: str) -> bool:
    return bool(_PLACEHOLDER.search(text or ""))
