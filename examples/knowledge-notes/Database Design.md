# Database Design

## Overview

The database layer uses PostgreSQL with the pgvector extension for vector search. This keeps everything in a single database — no separate vector store needed.

## Key decisions

- **Single source of truth:** One database for both relational data and vector embeddings
- **pgvector over Qdrant:** Avoids sync pipeline between databases
- **Schema versioning:** All changes through [[Migrations]]

## Architecture

The database sits behind the [[API Architecture]] layer. [[Auth Design]] handles authentication, which connects to the database through connection pooling.

## Related

- [[PostgreSQL]] — the database engine
- [[Schema Design]] — table structure and relationships
- [[pgvector]] — vector search extension
- [[Migrations]] — schema version control
- [[API Architecture]] — how the API connects to the database
