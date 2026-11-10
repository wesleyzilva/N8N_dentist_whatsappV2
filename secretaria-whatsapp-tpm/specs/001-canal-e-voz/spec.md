# Spec 001 — Canal e voz

**Problemas cobertos:** P1, P2, P10
**Status:** não iniciada

## Objetivo
Mensagem do WhatsApp entra pelo n8n, passa pelo serviço Python (/turn) e volta com resposta humanizada, sem fatos inventados.

## Histórias de usuário
- Como paciente, mando uma mensagem e recebo resposta no tom de secretária.
- Como dona da clínica, quero que a secretária nunca invente horário, preço ou procedimento.
- Como TPM, quero um webhook estável e observável (log por turno).

## Critérios de aceite
- [ ] Gate: Round-trip webhook → /turn → texto humanizado, sem fatos inventados.
- [ ] Cenários da fase passam em `tests/scenarios/`
- [ ] Nenhuma claim sem evidência (constituição I)

## Fora de escopo
Qualquer item de fases posteriores.

## Pontos a esclarecer (/speckit-clarify)
- [ ] (preencha antes do plan)
