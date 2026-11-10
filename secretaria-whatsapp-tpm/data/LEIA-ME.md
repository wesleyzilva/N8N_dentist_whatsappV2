# Dados de treino (NÃO versionar — LGPD)

Tudo aqui, exceto este arquivo, está no `.gitignore`.

| Pasta | Conteúdo |
|---|---|
| `conversas-brutas/` | exports do WhatsApp (`.txt`/`.zip`). Nunca envie o bruto a um LLM. |
| `curadoria/` | `pares.jsonl` (anonimizado) e `revisao.csv` (planilha para a dra) |
| `rag/` | `index.json` (embeddings dos pares aprovados) |
| `avaliacao/` | relatório do modo sombra |
| `finetune/` | `train.jsonl` e `validation.jsonl` (Vertex AI) |

Passo a passo: `docs/tpm/07-guia-treino-conversas.md`.
