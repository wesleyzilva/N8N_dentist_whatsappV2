# Plan 007 — LLM + RAG

## Fluxo
```
export WhatsApp ──► ingestão ──► anonimização ──► curadoria humana ──► chunks aprovados
                                                                           │
                                         embeddings ──► índice (pgvector) ◄┘
paciente ──► /turn ──► intenção ──► grounding (fatos) ──► RAG (só estilo/FAQ) ──► LLM redige ──► checagem de claims ──► resposta
```

## Etapas
1. **Dados:** ingestão, anonimização, split treino/avaliação. Nunca commitar conversas (`data/` no `.gitignore`).
2. **Índice:** pgvector no Postgres já existente (evita novo serviço); só trechos aprovados.
3. **Redação:** LLM recebe pergunta + claims permitidos + trechos de estilo; proibido criar fatos.
4. **Guarda:** verificador pós-LLM remove/bloqueia claim sem evidência (reaproveita `grounding`).
5. **Avaliação:** cenários anti-alucinação + conjunto real; modo sombra antes de produção.
6. **Decisão de fine-tuning:** só após métricas; registrar em ADR.

## Código existente desta fase
- `app/domains/guardrails/grounding.py`
- `app/domains/secretary/voice.py` e `config/voice.json`
- `app/domains/patients/session.py` (brief mínimo para LLM)
- `tests/scenarios/conversations.json`
- `infra/db/migrations/001_secretaria_fase1.sql`

## Material da pós
- `modulo09-.../modulo-01-decision-framework` (RAG vs fine-tuning)
- `modulo09-.../modulo-02-preparacao-datasets`
- `modulo09-.../modulo-05-avaliacao-modelos`
- `modulo09-.../modulo-03-fine-tuning-via-api` e `modulo-04-lora-e-peft` (só se a avaliação exigir)
- `modulo08-.../modulo-04-padroes-ai-especificos/rag-pattern-selector-canvas.md` e `hitl-formalization-canvas.md`
- `modulo10-.../modulo5-seguranca-dados`
- `modulo04-.../05-gerenciamento-de-contextos`

## Constitution Check
- [ ] I Grounding · [ ] II Test-first · [ ] IV Humano no loop · [ ] V LGPD (anonimizar antes de indexar)
