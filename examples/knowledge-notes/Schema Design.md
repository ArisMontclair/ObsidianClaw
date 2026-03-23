# Schema Design

## Tables

### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    embedding vector(1536),  -- pgvector column
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Indexes

- HNSW index on `documents.embedding` for [[Vector Search]]
- B-tree index on `documents.title` for text search
- GIN index on `documents.metadata` for JSON queries

## Design principles

- UUIDs for primary keys (globally unique, no conflicts)
- JSONB for flexible metadata (schema-less where needed)
- Timestamps on everything (audit trail)
- Soft deletes where appropriate

## Related

- [[Database Design]] — overall strategy
- [[Migrations]] — how schema changes are versioned
- [[PostgreSQL]] — the database engine
- [[pgvector]] — vector search setup
