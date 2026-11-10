# Secretária WhatsApp — Harmonização orofacial (gestão TPM + IA com RAG)

Secretária digital no WhatsApp do consultório de **harmonização orofacial** (Pato Branco DDD 46 · São Carlos DDD 16).
Código migrado do projeto original (todos os testes verdes) + **Fase 7: LLM Gemini + RAG treinado com conversas reais do Zap**.
Você atua como **TPM**: especifica, prioriza, delega aos agentes e valida gates.

## Comece aqui
1. [`docs/tpm/00-papel-do-tpm.md`](docs/tpm/00-papel-do-tpm.md) — rotina e responsabilidades
2. [`docs/tpm/01-trilha-de-reconstrucao.md`](docs/tpm/01-trilha-de-reconstrucao.md) — fases 0–7 e estado atual
3. [`docs/tpm/07-guia-treino-conversas.md`](docs/tpm/07-guia-treino-conversas.md) — **passo a passo para treinar com suas conversas**
4. [`docs/tpm/02-mapa-pos-projeto.md`](docs/tpm/02-mapa-pos-projeto.md) — material da pós por fase
5. [`specs/`](specs/) — spec/plan/tasks por fase (Spec-Driven Development)

## Rodar
```bash
pip install -r requirements-dev.txt
copy .env.example .env            # preencha GEMINI_API_KEY quando for usar a IA
pytest                            # 373 testes (inclui pipeline de treino e LLM adversarial)
npm run console                   # TPM Console em http://localhost:4173
python -m app.interfaces.cli.treino --help   # pipeline de conversas → RAG → fine-tuning
```

## Como a IA entra (sem alucinar)
```
WhatsApp → n8n → /turn ─► regras + grounding (fatos só de config/calendário) ─► resposta-base (template)
                                                                                    │
                    LLM_MODE=off ───────────────────────────────────────────────────┤ (padrão)
                    LLM_MODE=shadow → Gemini reescreve, paciente recebe o template, comparação em logs/shadow.jsonl
                    LLM_MODE=on     → Gemini reescreve no tom das conversas aprovadas (RAG);
                                      verificador barra horário/preço/cidade/procedimento/conselho inventado → senão template
```
Escalonamento clínico, pedido de humana e opt-out **nunca** passam pelo LLM.

## Estrutura
```
app/domains/        intenção, unidade, grounding, voz, llm/ (redator + verificador), training/ (pipeline)
app/infrastructure/ config, calendário, memória, observabilidade, llm/ (Gemini REST + fake), rag/ (índice)
app/interfaces/     http (/turn, /meta/webhook), n8n, cli/treino.py
config/             clinic, guardrails, voz, sessão, llm.json
data/               conversas e artefatos de treino (fora do git — LGPD)
specs/ .specify/    SDD: constituição e specs 001–007
docs/tpm/           trilha, mapa da pós, backlog, RAID, RACI, gates, guia de treino, ADRs
docs/governance/    status.json, layout.json (lidos pelo TPM Console)
console/ workflows/ infra/ mcp/ tests/ scripts/
```

## Regra de ouro
Nenhum agente — nem o LLM — afirma disponibilidade, preço ou cidade da dra sem evidência de MCP/config. UNKNOWN + pergunta ou escalonamento vence um chute educado.
