# Constituição — Secretária WhatsApp (harmonização orofacial)

Versão 1.0.0 · base: modelo da live de SDD (2026-05-27) adaptado ao domínio.

## Princípios

### I. Grounding acima de simpatia (INEGOCIÁVEL)
Horário, disponibilidade, cidade da dra, preço e procedimento só são afirmados com evidência de MCP ou `config/`. Sem evidência: UNKNOWN + pergunta ou escalonamento.

### II. Test-first
Toda regra de domínio tem teste que falha antes do código. Três testes anti-alucinação sempre: calendário indisponível; presença sem evento; "qualquer horário amanhã" lista só slots da ferramenta.

### III. Fronteira de camadas
n8n orquestra; domínio Python decide; MCP fornece fatos; LLM só redige. Regra de negócio no canvas do n8n é proibida.

### IV. Humano no loop
Risco clínico, jurídico ou financeiro escala para pessoa. Nenhum conselho clínico automático. Mutação de agenda exige confirmação explícita no turno.

### V. LGPD e segredos
Opt-out sempre respeitado e persistido; log de decisão auditável; segredos fora do git.

### VI. Simplicidade (YAGNI)
Implemente só o que a spec da fase atual exige. Fases não se pulam: a seguinte depende da evidência da anterior.

## Governança
Mudança de princípio exige ADR em `docs/tpm/adr/` e bump de versão.
