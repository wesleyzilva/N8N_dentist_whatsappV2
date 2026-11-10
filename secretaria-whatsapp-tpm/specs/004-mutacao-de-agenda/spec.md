# Spec 004 — Mutação de agenda

**Problemas cobertos:** P6
**Status:** não iniciada

## Objetivo
Confirmar, reagendar e cancelar com confirmação explícita do paciente, com rollback documentado.

## Histórias de usuário
- Como paciente, só tenho consulta alterada se eu confirmar explicitamente.

## Critérios de aceite
- [ ] Gate: Nenhuma mutação sem CONFIRM explícito no turno; rollback documentado.
- [ ] Cenários da fase passam em `tests/scenarios/`
- [ ] Nenhuma claim sem evidência (constituição I)

## Fora de escopo
Qualquer item de fases posteriores.

## Pontos a esclarecer (/speckit-clarify)
- [ ] (preencha antes do plan)
