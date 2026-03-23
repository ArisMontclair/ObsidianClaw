# Auto-Retrieve PR Proposal

## Title

**feat: Add auto-retrieve memory injection for consciousness-like recall**

## Summary

Add a `memorySearch.autoRetrieve` configuration option that automatically runs `memory_search` on every user message and injects results into the model's context before generation. This transforms memory from a tool the model calls to a background process that's always running, mimicking human associative memory.

## Problem

Current OpenClaw memory requires the model to explicitly call `memory_search`. This has several issues:

1. **Conscious decision required:** The model must decide to search, which is not how human memory works
2. **Model doesn't know what it doesn't know:** If the model doesn't think to search, it misses relevant information
3. **Breaks conversation flow:** Having to stop and search disrupts natural dialogue
4. **Higher token usage:** MEMORY.md must be loaded into context at session start, consuming 5000-8000 tokens that are processed on every turn

## Solution

### Architecture

```
User message arrives
         ↓
Gateway intercepts (before model inference)
         ↓
Auto-runs memory_search(message)
         ↓
Returns top N results
         ↓
Injects as system message into context
         ↓
Model sees: [user message] + [relevant memories]
         ↓
Model responds with full context, no tool call needed
```

### Configuration

```json5
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "autoRetrieve": {
          "enabled": false,  // default off
          "maxResults": 3,
          "maxSnippetChars": 500,
          "scope": {
            "default": "deny",
            "rules": [
              { "action": "allow", "match": { "chatType": "direct" } }
            ]
          },
          "cooldown": {
            "enabled": true,
            "minIntervalMs": 5000  // don't search if last search < 5s ago
          }
        }
      }
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|---|---|---|---|
| `enabled` | boolean | `false` | Enable auto-retrieve |
| `maxResults` | number | `3` | Maximum number of results to inject |
| `maxSnippetChars` | number | `500` | Maximum characters per snippet |
| `scope` | object | `{default: "deny"}` | Session scope (same as QMD scope) |
| `cooldown.enabled` | boolean | `true` | Enable cooldown between searches |
| `cooldown.minIntervalMs` | number | `5000` | Minimum interval between searches |

### Implementation Details

1. **Interception point:** In the gateway's message processing pipeline, before model inference
2. **Search execution:** Reuse existing `memory_search` infrastructure (same vector store, same embedding provider)
3. **Injection format:** System message prepended to context:
   ```
   [Relevant memories:
    1. Note Title (score: 0.94): "Snippet text..."
    2. Note Title (score: 0.87): "Snippet text..."]
   ```
4. **Caching:** Cache search results for the same query to avoid duplicate searches
5. **Scope control:** Use existing scope infrastructure to control which sessions get auto-retrieve

### Token Impact

| Approach | Tokens per 30-turn session |
|---|---|
| Current (MEMORY.md in context) | ~155,000 - 248,000 |
| Auto-retrieve | ~45,000 |
| **Savings** | **70-80%** |

### Performance

- **Latency:** ~50-100ms for vector search (sqlite-vec HNSW index)
- **API cost:** ~$0.001 per search (embedding query)
- **Total overhead:** ~$0.03 per 30-turn session

## Examples

### Without Auto-Retrieve

```
User: "What's your take on the database layer approach?"

Model: "I'm not sure I have context on that specific framework. 
Could you remind me what you mean?"
```

### With Auto-Retrieve

```
User: "What's our approach to the database layer?"

[Auto-retrieve injected: 
 1. PostgreSQL + pgvector (0.94): "PostgreSQL with pgvector extension 
    for vector search. Single source of truth..."
 2. Schema Design (0.87): "documents table with vector(1536) column 
    for embeddings, plus standard relational tables..."
 3. Architecture Decision (0.82): "Chosen over separate vector store 
    to avoid sync pipeline complexity..."]

Model: "PostgreSQL with pgvector extension. You chose this over a 
separate vector store to keep a single source of truth — no sync 
pipeline between databases. The tradeoff is slightly slower vector 
queries but much simpler architecture. The schema has a documents 
table with a vector(1536) column for embeddings."
```

## Backward Compatibility

- **Default off:** `autoRetrieve.enabled = false` by default
- **No breaking changes:** Existing memory_search tool continues to work
- **Additive:** Auto-retrieve is an additional layer on top of existing infrastructure
- **Scope control:** Can be limited to specific session types

## Future Extensions

1. **Graph traversal:** Combine with wiki link parsing for associative spreading
2. **Relevance weighting:** Weight results by graph distance, not just vector similarity
3. **Sleep consolidation:** Periodic re-indexing of knowledge base
4. **HippoRAG integration:** Personalized PageRank for deep associative retrieval

## Testing

1. Enable auto-retrieve on a test agent
2. Send messages about topics in the knowledge base
3. Verify relevant memories are injected
4. Verify model responds with context
5. Verify token usage is lower than MEMORY.md approach
6. Verify scope control works (groups don't get auto-retrieve)

## Files Changed

- `gateway/src/memory/auto-retrieve.ts` (new)
- `gateway/src/memory/index.ts` (modify)
- `gateway/src/config/defaults.ts` (modify)
- `docs/concepts/memory.md` (modify)
- `docs/gateway/configuration-reference.md` (modify)
