# Spec 003 — Agenda grounded

**Problemas cobertos:** P2, P5
**Status:** não iniciada

## Objetivo
Oferecer horários somente a partir de freebusy real do Google Calendar; se falhar, pedir espera ou escalar.

## Histórias de usuário
- Como paciente, vejo apenas horários realmente livres.
- Como dona, se o Google cair a secretária não chuta horário.

## Critérios de aceite
- [ ] Gate: Se o calendário falhar: pede espera ou escala; zero horários sintéticos.
- [ ] Cenários da fase passam em `tests/scenarios/`
- [ ] Nenhuma claim sem evidência (constituição I)

## Fora de escopo
Qualquer item de fases posteriores.

## Pontos a esclarecer (/speckit-clarify)
- [ ] (preencha antes do plan)
