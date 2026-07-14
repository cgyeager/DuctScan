
-- 1. Enable the pgvector extension (required for the vector column + index)
CREATE EXTENSION IF NOT EXISTS vector;


-- 2. Chunks table
--    One row per chunk produced by the ingestion pipeline.
--    EMBEDDING_DIMENSION must match EMBEDDING_DIMENSION in .env (default 1024).
CREATE TABLE IF NOT EXISTS chunks (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  TEXT        NOT NULL,
    content      TEXT        NOT NULL,
    embedding    vector(1024),            -- voyage-3-large default dimension
    source_path  TEXT        NOT NULL,
    page         INTEGER,                 -- 1-based page number (nullable for non-PDF)
    section      TEXT,                    -- heading / section label (nullable)
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- 3. Vector similarity index (IVFFlat — good for ≤1 M rows)
--    For larger datasets consider HNSW: USING hnsw (embedding vector_cosine_ops)
--    lists = sqrt(row_count) is a common starting point; tune after you have data.
-- CREATE INDEX IF NOT EXISTS chunks_embedding_idx
--     ON chunks
--     USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100); -- or lists = rows / 1000


-- 4. Scalar indexes for fast document-level lookups / deletes
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id);
CREATE INDEX IF NOT EXISTS chunks_created_at_idx  ON chunks (created_at);


-- 5. match_chunks — called by ChunkStore.similarity_search()
--    Returns the top-k chunks whose cosine similarity exceeds match_threshold,
--    ordered closest-first.
--
--    NOTE: If you change EMBEDDING_DIMENSION in .env, update the vector(N)
--    type here AND in the table definition above, then re-run this migration.
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding  vector(1024),
    match_threshold  float   DEFAULT 0.20,
    match_count      integer DEFAULT 5
)
RETURNS TABLE (
    id           UUID,
    document_id  TEXT,
    content      TEXT,
    source_path  TEXT,
    page         INTEGER,
    section      TEXT,
    similarity   float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.document_id,
        c.content,
        c.source_path,
        c.page,
        c.section,
        -- cosine similarity = 1 − cosine distance
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding   -- ascending distance = descending similarity
    LIMIT match_count;
END;
$$;
