"""Anonimização LGPD antes de qualquer uso (curadoria, índice RAG, LLM, fine-tuning).

Remove: nomes conhecidos (autores da conversa + lista extra), "meu nome é X", telefones,
e-mails, CPF, RG, CEP, cartão, URLs e endereços. Heurística: a curadoria humana é a segunda barreira.
"""

import re
import unicodedata
from typing import Iterable, List

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CARD = re.compile(r"\b(?:\d{4}[ .-]?){3}\d{4}\b")
_CEP = re.compile(r"\b\d{5}-\d{3}\b")
_RG = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]\b")
_PHONE = re.compile(r"(?:\+?55[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?9?\d{4}[\s.-]?\d{4}\b")
_ADDRESS = re.compile(
    r"\b(?:rua|r\.|av\.?|avenida|travessa|alameda|rodovia|estrada|pra[çc]a)\s+[^\n,;.]{2,60}?(?:,?\s*(?:n[º°o.]?\s*)?\d{1,5})",
    re.IGNORECASE,
)
_MY_NAME = re.compile(
    r"\b((?i:meu nome [ée]|me chamo|aqui [ée] (?:a|o)|sou (?:a|o)|falo com (?:a|o)?))\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wáéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wáéíóúâêôãõç]+){0,3})",
)
_GREETING_NAME = re.compile(
    r"\b((?i:oi|ol[áa]|bom dia|boa tarde|boa noite|obrigad[ao]|tchau))([,!]?\s+)([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,})\b"
)
# Palavras que parecem nome próprio mas não são (início de frase, cidades, títulos).
_NOT_NAMES = {
    "dra", "doutora", "doutor", "dr", "tudo", "sim", "nao", "pode", "meu", "minha", "eu", "voces", "vcs",
    "secretaria", "equipe", "clinica", "consultorio", "amanha", "hoje", "segunda", "terca", "quarta",
    "quinta", "sexta", "sabado", "domingo", "pessoal", "gente", "querida", "querido", "amiga", "amigo",
}


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def name_tokens(names: Iterable[str]) -> List[str]:
    """Quebra 'Maria Silva' em ['Maria Silva', 'Maria', 'Silva'] (só tokens com 3+ letras)."""
    out: List[str] = []
    for name in names:
        name = re.sub(r"[^\wÀ-ÿ\s]", " ", name or "").strip()
        if not name or name.replace(" ", "").isdigit():
            continue
        out.append(name)
        out.extend(t for t in name.split() if len(t) >= 3 and _fold(t) not in _NOT_NAMES)
    return sorted(set(out), key=len, reverse=True)


# Cidades das unidades são protegidas: "Carlos" (nome) some, "São Carlos" (unidade) fica.
_CITIES = re.compile(r"\b(s[ãa]o carlos|pato branco)\b", re.IGNORECASE)


def anonymize(text: str, known_names: Iterable[str] = ()) -> str:
    if not text:
        return text
    cities: List[str] = []

    def _protect(m: re.Match) -> str:
        cities.append(m.group(0))
        return f"\x00{len(cities) - 1}\x00"

    out = _CITIES.sub(_protect, text)
    out = _restore(_anonymize(out, known_names), cities)
    return out


def _restore(text: str, cities: List[str]) -> str:
    return re.sub(r"\x00(\d+)\x00", lambda m: cities[int(m.group(1))], text)


def _anonymize(text: str, known_names: Iterable[str]) -> str:
    out = _URL.sub("[LINK]", text)
    out = _EMAIL.sub("[EMAIL]", out)
    out = _CARD.sub("[CARTAO]", out)
    out = _CPF.sub("[CPF]", out)
    out = _CEP.sub("[CEP]", out)
    out = _ADDRESS.sub("[ENDERECO]", out)
    out = _PHONE.sub(lambda m: "[TELEFONE]" if len(re.sub(r"\D", "", m.group(0))) >= 8 else m.group(0), out)
    out = _RG.sub("[DOCUMENTO]", out)
    out = _MY_NAME.sub(lambda m: f"{m.group(1)} [NOME]", out)
    out = _GREETING_NAME.sub(
        lambda m: m.group(0) if _fold(m.group(3)) in _NOT_NAMES else f"{m.group(1)}{m.group(2)}[NOME]", out
    )
    for token in name_tokens(known_names):
        out = re.sub(rf"(?<![\w\[]){re.escape(token)}(?!\w)", "[NOME]", out, flags=re.IGNORECASE)
    return re.sub(r"(\[NOME\]\s*){2,}", "[NOME] ", out).strip()


_LEAK_PATTERNS = [_EMAIL, _CPF, _CARD, _CEP, _URL]


def leaks(text: str) -> List[str]:
    """Checagem final: devolve o que ainda parece dado pessoal (para teste e para a curadoria)."""
    found = [p.pattern[:20] for p in _LEAK_PATTERNS if p.search(text or "")]
    for m in _PHONE.finditer(text or ""):
        if len(re.sub(r"\D", "", m.group(0))) >= 10:
            found.append("telefone")
    return found
