# Papel do TPM neste projeto

Você não digita o código: você decide **o quê, em que ordem e quando está pronto**, e delega aos agentes (Dev, QA, Architect, Voice, Security, DevOps).

## Rotina por fase
1. **Especificar** — `/speckit-specify` + `/speckit-clarify` na spec da fase.
2. **Planejar** — `/speckit-plan`; registre trade-offs em ADR.
3. **Quebrar** — `/speckit-tasks`; cada task vira card (`templates/sprint-card.md`).
4. **Delegar** — um agente por card, com handoff explícito.
5. **Validar** — QA roda os cenários; você confere o gate (`06-phase-gates.md`).
6. **Reportar** — status report por audiência (`templates/status-report.md`) e atualização do RAID.

## Matriz de agentes (de `05-raci.md`)
| Pedido | Agente | Não pode |
|---|---|---|
| Arquitetura, contratos MCP | Architect | pular grounding |
| Implementar | Dev | inventar clínica/horário no prompt |
| Validar | QA | aprovar sem caso de alucinação |
| Tom | Voice | introduzir fatos de agenda |
| LGPD/risco | Security | enfraquecer opt-out |
| Docker/n8n/env | DevOps | commitar `.env` |

## Ritos
- **Semanal:** revisar RAID, backlog priorizado (RICE/WSJF) e previsão de entrega.
- **Fim de fase:** gate + status report + retro curta.
