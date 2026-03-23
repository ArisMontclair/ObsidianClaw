# Migrations

## Approach

All schema changes go through versioned migration files. No manual ALTER TABLE statements in production.

## Tool

Using Alembic (Python) for migration management:
- `alembic revision --autogenerate -m "description"` — generate migration
- `alembic upgrade head` — apply migrations
- `alembic downgrade -1` — rollback one step

## Rules

1. **Never edit a migration after it's been applied** — create a new one
2. **Always include a rollback** — every `upgrade()` needs a `downgrade()`
3. **Test migrations on staging first** — before production
4. **One concern per migration** — don't bundle unrelated changes

## Recent migrations

- 001: Create users table
- 002: Create documents table with pgvector
- 003: Add HNSW index on embeddings

## Related

- [[Schema Design]] — what the schema looks like
- [[Database Design]] — overall strategy
- [[PostgreSQL]] — the database engine
- [[Deployment Strategy]] — how migrations fit into deployment
