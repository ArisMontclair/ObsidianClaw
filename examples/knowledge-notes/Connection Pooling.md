# Connection Pooling

## Problem

Every API request needs a database connection. Opening a new connection per request is expensive (~50ms). Under load, you run out of connections.

## Solution

Connection pooler sits between API and [[PostgreSQL]]:
- Pre-opens a pool of connections
- API requests borrow a connection, use it, return it
- No connection creation overhead

## Implementation

Using PgBouncer:
- Pool mode: Transaction (return connection after each transaction)
- Max connections: 100
- Default pool size: 20
- Reserve pool: 5 (for emergencies)

## Configuration

```ini
[databases]
mydb = host=postgres port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20
reserve_pool_size = 5
```

## Related

- [[PostgreSQL]] — the database engine
- [[Database Design]] — overall architecture
- [[API Architecture]] — how API connects to pool
- [[Performance Tuning]] — optimization strategies
