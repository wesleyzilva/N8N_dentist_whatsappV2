"""Verificador pós-LLM: a saída só passa se não trouxer fato que a resposta-base (grounded) não tinha."""

from typing import Dict, List

from app.domains.llm.facts import find_facts, fold, has_placeholder

_ALWAYS_BLOCK = {"conselho_clinico", "contato"}


def check(candidate: str, base: str, max_chars: int = 320) -> Dict:
    problems: List[str] = []
    text = (candidate or "").strip()
    if not text:
        problems.append("vazio")
    if len(text) > max_chars:
        problems.append(f"longo ({len(text)}>{max_chars})")
    if has_placeholder(text):
        problems.append("marcador de dado oculto na saída")
    if "?" in (base or "") and "?" not in text:
        problems.append("perdeu a pergunta da resposta-base")

    base_folded = fold(base)
    base_facts = find_facts(base)
    for kind, hits in find_facts(text).items():
        if kind in _ALWAYS_BLOCK and kind not in base_facts:
            problems.append(f"{kind}: {hits[0]}")
            continue
        novel = [h for h in hits if fold(h) not in base_folded]
        if novel:
            problems.append(f"{kind} inventado: {novel[0]}")
    return {"ok": not problems, "problems": problems}
