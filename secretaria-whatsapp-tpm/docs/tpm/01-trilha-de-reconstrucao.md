# Trilha de reconstrução

Ordem fixa. Não pule fase.

| Fase | Nome | Problemas | Spec | Gate |
|---|---|---|---|---|
| 0 | Governança | — | `.specify/`, `docs/tpm/` (já neste repo) | TPM abre card P* sem docs órfãos |
| 1 | Canal e voz | P1, P2, P10 | [`specs/001-canal-e-voz`](../../specs/001-canal-e-voz/spec.md) | Round-trip webhook → /turn → texto humanizado, sem fatos inventados. |
| 2 | Unidade e presença | P3, P4 | [`specs/002-unidade-e-presenca`](../../specs/002-unidade-e-presenca/spec.md) | 46, 16, DDD outro e texto vs DDD; 'a dra está em X?' nunca sem ferramenta. |
| 3 | Agenda grounded | P2, P5 | [`specs/003-agenda-grounded`](../../specs/003-agenda-grounded/spec.md) | Se o calendário falhar: pede espera ou escala; zero horários sintéticos. |
| 4 | Mutação de agenda | P6 | [`specs/004-mutacao-de-agenda`](../../specs/004-mutacao-de-agenda/spec.md) | Nenhuma mutação sem CONFIRM explícito no turno; rollback documentado. |
| 5 | Triagem e humana | P7, P8 | [`specs/005-triagem-e-humana`](../../specs/005-triagem-e-humana/spec.md) | Caso clínico não recebe conselho; handoff com resumo factual. |
| 6 | Compliance e produção | P9 | [`specs/006-compliance-e-producao`](../../specs/006-compliance-e-producao/spec.md) | Opt-out, auditoria de decisão, backup do n8n; Security assina. |
| 7 | LLM + RAG | P1, P2, P7, P9 | [`specs/007-llm-e-rag`](../../specs/007-llm-e-rag/spec.md) | Sem dado pessoal no corpus, zero fato inventado, modo sombra aprovado |

## Como reconstruir uma fase
1. Abra `spec.md` da fase e responda os pontos a esclarecer.
2. Leia o código listado em `plan.md` (já migrado do projeto original, 338 testes verdes) e evolua a partir dele.
3. Escreva primeiro os testes (cenários + unitários), depois o código.
4. Marque as tasks, rode o gate e só então abra a próxima fase.

## Estado (2026-11-03)
Fase 0 feita · Fase 1 em andamento (falta ativar o workflow no n8n) · Fase 2 em andamento · Fase 3 bloqueada (sem cliente Google real) · Fases 4–6 planejadas.
Fase 7 (LLM + RAG): código pronto e testado com provedor falso; falta chave Gemini, conversas reais e curadoria. Guia: `07-guia-treino-conversas.md`.
