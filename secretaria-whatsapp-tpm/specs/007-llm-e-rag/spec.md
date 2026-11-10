# Spec 007 — LLM + RAG a partir de conversas reais

**Problemas cobertos:** P1, P2, P7, P9
**Status:** MVP implementado (2026-11-03) · provedor: Google Gemini · falta: chave, conversas reais, curadoria · **Depende de:** fases 1 e 6 (grounding e LGPD) concluídas
**Origem:** TPM tem exemplos reais de conversas de WhatsApp para alimentar a IA antes de ir a produção.

## Objetivo
Usar conversas reais (anonimizadas) para (1) montar uma base RAG de respostas aprovadas, (2) avaliar o LLM em modo sombra e (3) só então decidir se vale ajustar o modelo. O LLM apenas **redige**; fatos continuam vindo de config/MCP.

## Histórias de usuário
- Como TPM, importo exportações do WhatsApp e obtenho um corpus limpo e anonimizado.
- Como dra/dona, reviso e aprovo cada resposta antes de ela entrar na base.
- Como paciente, recebo respostas no jeito da clínica sem que o bot invente horário, preço ou conselho clínico.
- Como compliance, garanto que nenhum dado pessoal vai para o LLM ou para a base.

## Critérios de aceite
- [x] Pipeline de ingestão: exportação `.txt/.zip` do WhatsApp → mensagens estruturadas
- [x] Anonimização: nomes, telefones, e-mails, CPF e endereços removidos antes de indexar (teste com amostra)
- [x] Curadoria: só trechos marcados `aprovado` entram no índice
- [x] RAG nunca fornece preço, horário, cidade da dra ou orientação clínica; esses temas continuam com grounding/escalonamento
- [ ] Avaliação: conjunto de teste separado das conversas, com métricas e os 15+ cenários anti-alucinação intactos
- [x] Modo sombra: LLM gera resposta, humana compara; nada vai ao paciente
- [ ] Fine-tuning só se a avaliação mostrar que RAG + prompt não bastam (ADR)

## Fora de escopo
Treinar modelo próprio do zero; enviar dados brutos de pacientes a qualquer provedor.

## Pontos a esclarecer (/speckit-clarify)
- [ ] Paciente consentiu o uso das conversas? Base legal LGPD e prazo de retenção
- [x] Provedor: Google Gemini (redação + embeddings). Fine-tuning: Vertex AI
- [ ] Quantas conversas e de qual período? Formato do export
- [ ] Quem aprova cada resposta (dra, secretária)?

## Onde está no código
- Pipeline: `app/domains/training/` (whatsapp_export, anonymizer, pairs, curation, finetune_export)
- LLM: `app/domains/llm/` (facts, claim_checker, writer) · `app/infrastructure/llm/providers.py` · `app/infrastructure/rag/vector_store.py`
- CLI: `app/interfaces/cli/treino.py` · Config: `config/llm.json` · Testes: `tests/test_training_pipeline.py`, `tests/test_llm_rag.py`
- Guia do TPM: `docs/tpm/07-guia-treino-conversas.md`
