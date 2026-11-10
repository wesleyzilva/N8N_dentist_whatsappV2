# Guia: treinar a secretária com conversas reais do WhatsApp

Objetivo: a IA aprender o **jeito** da clínica responder, sem aprender (nem inventar) horário, preço ou conselho clínico.
Comando base: `python -m app.interfaces.cli.treino <passo>` (acrescente `--fake` antes do passo para testar sem chave Gemini).

## Antes de começar (TPM)
- [ ] Base legal LGPD para usar as conversas (consentimento ou legítimo interesse documentado) e prazo de retenção
- [ ] Quem aprova as respostas (dra / secretária)
- [ ] `GEMINI_API_KEY` no `.env` e `checar-gemini` ok

## Passo a passo
| # | Passo | Comando | Resultado |
|---|---|---|---|
| 1 | Exportar do WhatsApp | celular → conversa → ⋮ → Mais → **Exportar conversa → Sem mídia** | `.txt` ou `.zip` |
| 2 | Colocar os arquivos | copiar para `data/conversas-brutas/` | pasta fora do git |
| 3 | Ingerir | `ingerir --clinica "Nome da clínica no Zap"` (repita `--clinica` se houver mais de um atendente) | `data/curadoria/pares.jsonl` anonimizado, fatos mascarados, clínico bloqueado, ~10% separado para avaliação |
| 4 | Revisar | `exportar-planilha` → abrir `data/curadoria/revisao.csv` no Excel → status `aprovado`/`rejeitado`, ajustar `reply`, preencher `reviewer` → `importar-planilha` (ou `revisar --revisor "Dra"` no terminal) | só aprovados seguem |
| 5 | Indexar (RAG) | `indexar` | `data/rag/index.json` com embeddings Gemini |
| 6 | Testar uma frase | `testar "tem horário amanhã?"` | template × LLM × verificador |
| 7 | Avaliar em sombra | `avaliar` | `data/avaliacao/relatorio.md` (real × template × LLM, % aprovado) |
| 8 | Sombra no serviço | `LLM_MODE=shadow` no `.env` | paciente recebe template; comparação em `logs/shadow.jsonl` |
| 9 | Ligar | `LLM_MODE=on` só após gate (abaixo) | LLM responde quando o verificador aprova |
| 10 | Fine-tuning (opcional) | `finetune` | `data/finetune/train.jsonl` + `validation.jsonl` (formato Vertex AI) |

## O que o pipeline faz com cada conversa
- **Anonimiza**: nomes dos autores e citados, telefone, e-mail, CPF, RG, CEP, cartão, link e endereço viram `[NOME]`, `[TELEFONE]`... "São Carlos"/"Pato Branco" são preservados.
- **Mascara fatos** na resposta da clínica: `{HORARIO}`, `{DATA}`, `{DIA}`, `{PRECO}`, `{CIDADE}`, `{PROCEDIMENTO}`. A IA aprende o tom; o dado sempre virá da ferramenta.
- **Bloqueia** pares com dor/sintoma ou com orientação clínica ("é normal", "toma dipirona"): nunca viram exemplo.
- **Recusa aprovar** par com dado pessoal remanescente ou sem revisor (auditoria).

## Gate para `LLM_MODE=on`
- [ ] ≥ 50 pares aprovados no treino e relatório de avaliação revisado pela dra
- [ ] ≥ 95% das reescritas aprovadas pelo verificador e nenhuma com fato inventado na leitura humana
- [ ] 1 semana em `shadow` com `logs/shadow.jsonl` revisado
- [ ] `pytest` verde (inclui o teste com LLM adversarial em todos os cenários)

## RAG ou fine-tuning?
Comece só com **RAG** (passos 1–9). Fine-tuning só se a avaliação mostrar que o tom ainda não sai certo **e** houver ≥ 100 exemplos aprovados (o Google recomenda 100–500). O tuning do Gemini é feito no **Vertex AI** (Google Cloud): suba os `.jsonl` no Cloud Storage e crie o job de supervised tuning. Confira o schema atual na documentação antes de subir. Registre a decisão em ADR.

## Material da pós
- `modulo09-.../modulo-01-decision-framework` (RAG × fine-tuning), `modulo-02-preparacao-datasets`, `modulo-05-avaliacao-modelos`, `modulo-03-fine-tuning-via-api`
- `modulo08-.../modulo-04-padroes-ai-especificos/rag-pattern-selector-canvas.md` e `hitl-formalization-canvas.md`
- `modulo10-.../modulo5-seguranca-dados`
