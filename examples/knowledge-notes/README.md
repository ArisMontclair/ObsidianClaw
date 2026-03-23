# Example Knowledge Notes

This directory contains example Obsidian notes demonstrating the wiki link graph structure.

Each note has `[[wiki links]]` to related notes. These links create a knowledge graph that ObsidianClaw can traverse for associative memory retrieval.

## The Graph

```
Database Design ──→ PostgreSQL ──→ pgvector
       │                                │
       ▼                                ▼
  Schema Design ──→ Migrations ──→ Vector Search
       │                                │
       ▼                                ▼
  API Architecture ──→ Auth Design ──→ JWT
```

## How it works

1. You write a note: "Database Design"
2. You link to related notes: `[[PostgreSQL]]`, `[[Schema Design]]`
3. ObsidianClaw parses these links into a graph
4. When you search for "database," it finds "Database Design" AND follows the links to "PostgreSQL" and "Schema Design"
5. Even if "PostgreSQL" doesn't mention the word "database" directly, it surfaces because it's connected in the graph

## Example search flow

**Query:** "database"

**Vector search finds:**
1. Database Design (score: 0.95) — directly mentions database
2. PostgreSQL (score: 0.87) — mentions database in context

**Graph traversal follows:**
- Database Design → links to → Schema Design (hop 1)
- Schema Design → links to → Migrations (hop 2)
- Migrations → links to → Deployment Strategy (hop 2)

**Combined results:**
- Database Design (vector + graph)
- PostgreSQL (vector)
- Schema Design (graph, hop 1)
- Migrations (graph, hop 2)
- Deployment Strategy (graph, hop 2)

The last two would never surface from vector search alone — they're connected through the graph, not through semantic similarity.
