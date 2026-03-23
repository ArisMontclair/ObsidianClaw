# PostgreSQL

## Why PostgreSQL

Chosen for [[Database Design]] because:
- Mature, battle-tested
- pgvector extension available
- Full ACID compliance
- Great tooling ecosystem

## Configuration

- Connection pooling: PgBouncer
- Max connections: 100
- Shared buffers: 256MB
- Work memory: 4MB

## Extensions

- **pgvector:** Vector search for [[Vector Search]] capability
- **pg_stat_statements:** Query performance monitoring
- **uuid-ossp:** UUID generation

## Related

- [[Database Design]] — overall database strategy
- [[pgvector]] — vector extension
- [[Connection Pooling]] — how connections are managed
- [[Performance Tuning]] — query optimization
