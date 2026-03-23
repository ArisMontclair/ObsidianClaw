# Performance Tuning

## Database

- **Indexing:** B-tree for exact matches, GIN for JSON, HNSW for [[Vector Search]]
- **Query optimization:** EXPLAIN ANALYZE slow queries
- **Connection pooling:** [[Connection Pooling]] with PgBouncer
- **Vacuum:** Regular autovacuum to reclaim space

## API

- **Caching:** Redis for frequently accessed data
- **Compression:** gzip for responses > 1KB
- **Pagination:** Cursor-based, not offset-based
- **Batch operations:** Bulk inserts instead of row-by-row

## Monitoring

- Query time: p99 < 100ms target
- Connection pool: < 80% utilization
- Memory: < 80% of available
- Disk I/O: < 70% of capacity

## Tools

- pg_stat_statements: Query performance
- pgBadger: Log analysis
- New Relic: Application monitoring
- Grafana: Dashboards

## Related

- [[PostgreSQL]] — database engine
- [[Database Design]] — architecture
- [[Connection Pooling]] — connection management
- [[API Architecture]] — API layer
