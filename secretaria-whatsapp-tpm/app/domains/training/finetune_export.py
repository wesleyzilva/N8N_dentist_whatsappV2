"""Dataset de fine-tuning (supervised tuning do Gemini no Vertex AI) a partir dos pares aprovados.

Formato JSONL, um exemplo por linha:
  {"systemInstruction": {"role": "system", "parts": [{"text": ...}]},
   "contents": [{"role": "user", "parts": [{"text": paciente}]},
                {"role": "model", "parts": [{"text": resposta mascarada}]}]}

As respostas mantêm os marcadores ({HORARIO}, {PRECO}...): o modelo aprende o tom, não os dados.
Confira o schema atual na documentação do Vertex AI antes de subir o arquivo.
"""

import json
from pathlib import Path
from typing import Dict, List

from app.domains.training.anonymizer import leaks
from app.domains.training.curation import approved

MIN_RECOMMENDED = 100
MAX_VALIDATION = 256

SYSTEM = (
    "Você é a secretária virtual de um consultório de harmonização orofacial com unidades em Pato Branco e São Carlos. "
    "Responda curto, acolhedor, em português do Brasil. Nunca invente horário, data, preço, procedimento, cidade ou orientação clínica: "
    "quando o dado aparecer como {HORARIO}, {PRECO}, {DATA}, {DIA}, {CIDADE} ou {PROCEDIMENTO}, ele virá de uma ferramenta."
)


def to_example(pair: Dict) -> Dict:
    return {
        "systemInstruction": {"role": "system", "parts": [{"text": SYSTEM}]},
        "contents": [
            {"role": "user", "parts": [{"text": pair["patient"]}]},
            {"role": "model", "parts": [{"text": pair["reply"]}]},
        ],
    }


def export(pairs: List[Dict], out_dir: str | Path) -> Dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train = [p for p in approved(pairs, "treino") if not leaks(p["patient"]) and not leaks(p["reply"])]
    val = [p for p in approved(pairs, "avaliacao") if not leaks(p["patient"]) and not leaks(p["reply"])][:MAX_VALIDATION]
    for name, rows in (("train.jsonl", train), ("validation.jsonl", val)):
        with (out_dir / name).open("w", encoding="utf-8") as fh:
            for p in rows:
                fh.write(json.dumps(to_example(p), ensure_ascii=False) + "\n")
    warnings = []
    if len(train) < MIN_RECOMMENDED:
        warnings.append(f"só {len(train)} exemplos de treino aprovados; o recomendado é pelo menos {MIN_RECOMMENDED}. Prefira RAG até lá.")
    if not val:
        warnings.append("sem exemplos de validação aprovados (split 'avaliacao').")
    return {"train": len(train), "validation": len(val), "out_dir": str(out_dir), "warnings": warnings}
