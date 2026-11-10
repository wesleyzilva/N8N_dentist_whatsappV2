# Agentes — entrega vs runtime

Você é o time agentic deste repo. Leia `docs/canonical/CANONICAL_MAP.md` antes de qualquer mudança.
Não misture fidelidade/VIPpocket com a secretária WhatsApp. A prática é **harmonização orofacial**, não odontologia geral.

## Roteamento (entrega Cursor)

| Pedido do TPM | Skill | Pode editar | Não pode |
|---|---|---|---|
| Arquitetura, fases, mapa, trade-off | `.cursor/skills/tpm-agentic` | docs de governança, RAID, backlog | código de produção sem handoff ao Dev |
| Desenho técnico, contratos MCP | `.cursor/skills/architect-agentic` | `ARCHITECTURE.md`, `mcp/`, camadas app | pular grounding |
| Implementar | `.cursor/skills/dev-agentic` | `app/`, `workflows/`, tests | inventar clínica/horário no prompt |
| Validar | `.cursor/skills/qa-agentic` | `tests/`, evidências de gate | aprovar sem caso de alucinação |
| Tom da secretária | `.cursor/skills/secretary-voice-agentic` | `config/guardrails.json`, copy | fatos de agenda |
| LGPD / risco | `.cursor/skills/security-agentic` | políticas, logs, secrets hygiene | enfraquecer opt-out |
| Docker / n8n / env | `.cursor/skills/devops-agentic` | compose, scripts, `.env.example` | commitar `.env` |

Stakeholders simulados (dona, secretária humana, paciente, compliance): `docs/governance/PERSONA_AGENTS.md`. Eles opinam; não implementam.

## Runtime (WhatsApp)

Orchestrator, Intent, Location, Presence, Agenda, GuardrailGrounding, SecretaryVoice, Escalation — ver `ARCHITECTURE.md`.

## Regra de ouro

Nenhum agente afirma disponibilidade ou cidade da dra sem evidência de MCP/config. UNKNOWN + pergunta ou escalonamento vence um chute educado.

## Fluxo SDD (obrigatório)
1. Leia `.specify/memory/constitution.md` e a spec da fase em `specs/`.
2. Nada é implementado sem spec → plan → tasks aprovados pelo TPM.
3. Testes antes do código (RED → GREEN → REFACTOR).

## Fase 7 — LLM + RAG (Gemini)
- O LLM **só reescreve** a resposta-base já grounded (`app/domains/llm/writer.py`); o verificador (`claim_checker.py`) barra fato novo.
- Escalonamento, pedido de humana e opt-out nunca passam pelo LLM (`config/llm.json` → `never_rewrite`).
- Conversas reais ficam em `data/` (fora do git). Nada vai ao LLM ou ao índice sem anonimização e aprovação humana.
- Testes de LLM usam `FakeProvider`; nunca dependa de rede no pytest.
