# Backlog herdado do projeto original

Priorize com o Backlog Scorer (RICE/WSJF) da pós antes de abrir sprints.

| ID | Prioridade | Problema | Fase | Owner | Ação |
|---|---|---|---|---|---|
| A1 | alta | P10 | 1 | DevOps | Subir stack (docker compose up), importar workflows/intent_workflow.json e validar o webhook no Console (aba Integrações) |
| A2 | alta | P6 | 4 | Architect | Decidir: remover do canvas n8n a triagem/slots/reserva (Code node 'Triagem e Horários Próximos') e mover para app/ conforme regra n8n-workflows |
| A3 | alta | P9 | 6 | Security | Rotacionar a chave da Evolution API que esteve no git (serviço removido; a chave antiga continua no histórico) e exigir N8N_ENCRYPTION_KEY no .env (hoje o compose tem valor padrão) |
| A8 | alta | P10 | 1 | DevOps | Unificar o compose: promover infra/docker/compose.target.yml (postgres com healthcheck, intent-service, n8n sem segredo fixo) (sem Evolution: o WhatsApp é a Meta Cloud API) |
| A4 | media | P4 | 2 | TPM | Obter calendar_id distinto por unidade (hoje Pato Branco e São Carlos usam o mesmo) e endereço real das unidades |
| A5 | media | P5 | 3 | Dev | Implementar GoogleCalendarGateway real (freebusy) atrás do protocolo CalendarGateway; o fluxo OAuth antigo está no git (commit a0048aa, legacy/auth_e_agenda.py) |
| A6 | media | P8 | 5 | Dev | Separar motivos de escalonamento (clinical, human_requested, complaint); hoje pedido de humana sai como 'clinical' |
| A9 | media | P9 | 1 | Architect | Confirmar o modelo de dados: só conversation_state e processed_messages no banco secretaria; o schema 'clinica' (pacientes/agendamentos) foi removido por duplicar a agenda do Google Calendar |
| A7 | baixa | P7 | 5 | Dev | Palavra 'dor' casa por substring (ex.: 'adorei'); trocar por limite de palavra mantendo viés seguro |

## Problemas P1–P10

| ID | Título | Runtime | Fase | Owner |
|---|---|---|---|---|
| P1 | Atendimento humanizado no Zap | SecretaryVoice | 1 | Voice |
| P2 | Não alucinar | GuardrailGrounding | 1 | Dev + QA |
| P3 | Entender unidade (46 vs 16) | Location | 2 | Dev |
| P4 | Onde a dra está agora | Presence | 2 | Architect |
| P5 | Disponibilidade real | Agenda | 3 | Dev + DevOps |
| P6 | Confirmar / reagendar / cancelar | Appointments | 4 | Dev |
| P7 | Dúvida vs emergência vs clínico | Triage | 5 | Dev + Voice |
| P8 | Escalar para humana | Escalation | 5 | Dev + DevOps |
| P9 | LGPD, opt-out, auditoria | Compliance | 6 | Security |
| P10 | Orquestração confiável | Orchestrator (n8n) | 1 | DevOps |
