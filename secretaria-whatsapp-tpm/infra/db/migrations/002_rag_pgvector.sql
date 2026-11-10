-- Fase 7 · RAG em produção (pgvector). Local, o índice fica em data/rag/index.json.
-- Só entram pares APROVADOS e ANONIMIZADOS (spec 007). Nunca texto bruto de paciente.
-- Dimensão: gemini-embedding-001 devolve 3072 por padrão; ajuste se usar outputDimensionality.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS secretaria;

CREATE TABLE IF NOT EXISTS secretaria.rag_examples (
    id            TEXT PRIMARY KEY,           -- id do par (hash)
    intent        TEXT,
    patient_text  TEXT NOT NULL,              -- anonimizado
    reply_text    TEXT NOT NULL,              -- anonimizado e com fatos mascarados ({HORARIO}...)
    reviewer      TEXT NOT NULL,              -- quem aprovou (auditoria)
    reviewed_at   TIMESTAMPTZ NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding     vector(3072) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Busca por similaridade de cosseno. Para muitos exemplos (>10k), use índice HNSW
-- com dimensão <= 2000 (gere embeddings com outputDimensionality=1536, por exemplo).
