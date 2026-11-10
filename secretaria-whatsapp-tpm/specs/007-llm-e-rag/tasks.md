# Tasks 007 — LLM + RAG

- [ ] T01 Responder os pontos a esclarecer (consentimento, provedor, volume) e abrir ADR de base legal
- [x] T02 Definir formato do export e escrever teste do parser (RED)
- [x] T03 Parser de exportação WhatsApp → mensagens estruturadas
- [x] T04 Anonimizador (nome, telefone, e-mail, CPF, endereço) com testes de vazamento
- [x] T05 Separar conjunto de avaliação antes de qualquer indexação
- [x] T06 Ferramenta de curadoria (aprovar/rejeitar trechos; aprovador registrado)
- [x] T07 Índice local (data/rag) + migração pgvector (002); só trechos aprovados
- [x] T08 Camada de redação: LLM recebe claims permitidos + trechos de estilo
- [x] T09 Verificador pós-LLM: bloqueia claim sem evidência (preço, horário, cidade, clínico)
- [x] T10 Rodar cenários anti-alucinação com LLM ligado: todos verdes
- [ ] T11 Modo sombra com revisão humana e métricas
- [ ] T12 ADR: fine-tuning necessário ou RAG basta?

## Gate
- [ ] Zero vazamento de dado pessoal no corpus, zero fato inventado nos cenários, sombra aprovado pela dra
