# Mapa: material da pós ↔ projeto

`<POS>` = `C:\EngenharIAsoftware\engenharia-de-software-com-ia-aplicada-main`

| Tema | Onde na pós | Uso neste projeto |
|---|---|---|
| SDD / Spec Kit | `lives/2026-05-27/001-pos-live` (constitution, specs, skills `speckit-*`) | `.specify/` e `specs/` — método de toda a reconstrução |
| Planejamento e escopo (m07-01) | `modulo-01-planejamento-e-escopo` (Requirements Copilot) | Transformar conversas com a dona em backlog estruturado |
| Priorização (m07-02) | `modulo-02-priorizacao-de-backlog/backlog-scorer-prompt.md` | Priorizar A1–A9 com RICE/WSJF |
| Cronograma (m07-03) | `modulo-03-cronograma-e-capacidade/scheduling-prompt.md` | Dependências entre fases e capacidade |
| Estimativas (m07-04) | `modulo-04-estimativas-e-previsoes` (PERT + Monte Carlo) | Previsão P50/P85 de cada fase |
| Riscos (m07-05) | `modulo-05-riscos-e-aiops/risk-monitor-prompt.md` | Manter o `04-raid.md` |
| Reuniões (m07-06) | `modulo-06-reunioes-turbinadas/meeting-digest-prompt.md` | Ata e ações das reuniões com a dona |
| Status report (m07-07) | `modulo-07-status-reports/status-report-prompt.md` | Relato para dona, time técnico e compliance |
| Governança (m07-08) | `modulo-08-governanca-e-compliance` (checklist + Danger) | Gate de PR e checklist da Fase 6 |
| OKRs (m07-10) | `modulo-10-portfolio-e-okrs/okr-aligner-prompt.md` | Metas do produto pós-go-live |
| MCP na prática (m03) | `modulo03-mcp-na-pratica` (05 do zero, 04 skills, 07 segurança) | Contratos `mcp/schemas` e gateways |
| Agentes autônomos (m04) | `modulo04-.../03-function-calling`, `04-memoria`, `07-observabilidade-e-limites-de-autonomia` | Tool use, estado de conversa, limites do bot |
| Arquitetura com IA (m08) | `modulo08-arquitetura-de-sistemas-com-ia` (single/multi-agent, padrões) | Camadas e agentes de runtime |
| Segurança e ética (m10) | `modulo10-seguranca-governanca-ia` | LGPD, opt-out, humano no loop |
| AIOps (m06) | `modulo06-aiops-engenharia-agentica` | Observabilidade e incidentes em produção |
| Dados e fine-tuning (m09) | `modulo09-processamento-de-dados-e-fine-tuning-de-modelos` (decision framework, datasets, avaliação) | Fase 7: RAG vs fine-tuning e preparação das conversas |
