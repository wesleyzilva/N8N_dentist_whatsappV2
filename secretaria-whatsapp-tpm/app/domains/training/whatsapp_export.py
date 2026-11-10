"""Parser da exportação de conversa do WhatsApp ("Exportar conversa" → sem mídia).

Formatos aceitos (pt-BR):
  Android:  12/03/2024 14:35 - Maria: oi, tudo bem?
  iOS:      [12/03/2024, 14:35:12] Maria: oi, tudo bem?
Linhas sem cabeçalho são continuação da mensagem anterior.
"""

import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

_ANDROID = re.compile(
    r"^(?P<d>\d{1,2}/\d{1,2}/\d{2,4}),? (?P<t>\d{1,2}:\d{2}(?::\d{2})?)\s*(?:[aApP]\.?\s?[mM]\.?)?\s+-\s+(?P<rest>.*)$"
)
_IOS = re.compile(
    r"^‎?\[(?P<d>\d{1,2}/\d{1,2}/\d{2,4}),? (?P<t>\d{1,2}:\d{2}(?::\d{2})?)\]\s+(?P<rest>.*)$"
)
_MEDIA = re.compile(
    r"^‎?(<m[ií]dia oculta>|<media omitted>|imagem ocultada|[aá]udio ocultado|v[ií]deo omitido|figurinha omitida|"
    r"documento omitido|<anexado: .*>|.*\(arquivo anexado\))$",
    re.IGNORECASE,
)
_DELETED = re.compile(r"(mensagem (foi )?apagada|this message was deleted|voc[eê] apagou esta mensagem)", re.IGNORECASE)
_EDITED = re.compile(r"\s*<mensagem editada>\s*$", re.IGNORECASE)


@dataclass
class ChatMessage:
    when: Optional[datetime]
    author: str
    text: str
    kind: str = "text"  # text | media | deleted
    source: str = ""
    extra: dict = field(default_factory=dict)


def _parse_dt(d: str, t: str) -> Optional[datetime]:
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M"):
        try:
            return datetime.strptime(f"{d} {t}", fmt)
        except ValueError:
            continue
    return None


def parse_lines(lines: Iterable[str], source: str = "") -> List[ChatMessage]:
    messages: List[ChatMessage] = []
    for raw in lines:
        line = raw.rstrip("\r\n").replace(" ", " ")
        match = _IOS.match(line) or _ANDROID.match(line)
        if match:
            rest = match.group("rest")
            if ": " not in rest:
                # linha de sistema ("Fulano entrou", "As mensagens são protegidas...")
                continue
            author, text = rest.split(": ", 1)
            text = _EDITED.sub("", text.strip())
            kind = "media" if _MEDIA.match(text) else ("deleted" if _DELETED.search(text) else "text")
            messages.append(
                ChatMessage(
                    when=_parse_dt(match.group("d"), match.group("t")),
                    author=author.strip().lstrip("‎"),
                    text="" if kind != "text" else text,
                    kind=kind,
                    source=source,
                )
            )
        elif messages and line.strip():
            last = messages[-1]
            if last.kind == "text":
                last.text = f"{last.text}\n{line.strip()}"
    return messages


def read_export(path: str | Path) -> List[ChatMessage]:
    """Lê um .txt ou o .zip que o WhatsApp gera (pega os .txt de dentro)."""
    path = Path(path)
    if path.suffix.lower() == ".zip":
        out: List[ChatMessage] = []
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".txt"):
                    with zf.open(name) as fh:
                        out.extend(parse_lines(io.TextIOWrapper(fh, encoding="utf-8-sig"), source=f"{path.name}:{name}"))
        return out
    with path.open("r", encoding="utf-8-sig") as fh:
        return parse_lines(fh, source=path.name)


def list_exports(folder: str | Path) -> List[Path]:
    folder = Path(folder)
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in {".txt", ".zip"} and p.is_file())
