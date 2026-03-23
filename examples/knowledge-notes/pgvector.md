# pgvector

## What it is

PostgreSQL extension for vector similarity search. Stores vector embeddings alongside relational data in the same database.

## Setup

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Usage

```sql
-- Create table with vector column
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    embedding vector(1536)
);

-- Create HNSW index for fast search
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Search by similarity
SELECT id, embedding <=> '[0.1, 0.2, ...]' AS distance
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;
```

## Performance

- HNSW index: ~1-5ms for 100K vectors
- IVF index: ~10-20ms for 1M vectors (faster build, slower query)
- Flat search: ~100ms for 100K vectors (no index)

## Tradeoffs

- **vs Qdrant:** Slower vector queries, but no sync pipeline needed
- **vs Pinecone:** Local, no cloud dependency
- **vs Chroma:** Integrated with relational data, not separate service

## Related

- [[PostgreSQL]] — the database engine
- [[Database Design]] — overall strategy
- [[Vector Search]] — how search works
- [[Schema Design]] — table structure
