# Solutions Comparison

## Overview

Four solutions, ranked by impact and feasibility.

## Solution 1: Vector Search (OpenClaw existing + extraPaths)

### Architecture

```
Obsidian Vault ──→ OpenClaw memory-core ──→ SQLite + sqlite-vec
                                    │
                          memory_search tool
                                    │
                            Model receives snippets
```

### How it works

OpenClaw's existing memory-core already supports indexing markdown files. By adding `extraPaths` pointing to the Obsidian vault, we get:

- Automatic indexing of all Obsidian notes
- Vector similarity search (semantic matching)
- BM25 keyword search (exact token matching)
- Temporal decay (recent notes rank higher)
- MMR diversity (prevents redundant results)
- Embedding cache (avoids re-embedding unchanged text)

### Configuration

```json5
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "provider": "openai",
        "model": "text-embedding-3-large",
        "extraPaths": ["/path/to/obsidian/vault"],
        "query": {
          "hybrid": {
            "enabled": true,
            "vectorWeight": 0.7,
            "textWeight": 0.3,
            "mmr": { "enabled": true, "lambda": 0.7 },
            "temporalDecay": { "enabled": true, "halfLifeDays": 90 }
          }
        }
      }
    }
  }
}
```

### What it gives

| Feature | Status |
|---|---|
| Semantic search | ✅ |
| Keyword search | ✅ |
| Temporal decay | ✅ |
| Diversity filtering | ✅ |
| Auto-indexing | ✅ |
| Graph traversal | ❌ |
| Auto-retrieve | ❌ |
| Associative spreading | ❌ |

### Limitations

- **No graph traversal:** Wiki links are embedded as text, but the system doesn't follow them to find connected notes
- **No auto-retrieve:** Model must call memory_search explicitly
- **Flat:** Treats all notes as independent documents

### Effort

**5 minutes.** Config change only.

---

## Solution 2: Graph Traversal (Backlinks + Script)

### Architecture

```
Obsidian Vault ──→ OpenClaw memory-core ──→ SQLite + sqlite-vec
                                    │
                          memory_search tool
                                    │
                    search_vault.py script
                                    │
                  knowledge-graph.json (parsed wiki links)
                                    │
                    Graph traversal (follow links)
                                    │
                    Scored results with annotations
```

### How it works

After vector search returns initial results, a Python script reads a pre-parsed graph of wiki links and follows connections to expand the result set.

### Two Approaches

#### A: Backlinks in Notes

Add incoming connections to each note using Obsidian's fold syntax:

```markdown
<!-- %% fold %% -->
## Backlinks
- [[Stress Testing Extropy]] - used in stress testing framework
- [[Extropy Engine - AI Alignment]] - foundation of AI alignment proposal
```

When OpenClaw embeds the note, the backlinks become part of the vector. The graph is embedded implicitly.

**Pros:**
- No separate files
- No sync scripts
- Graph is always in sync
- OpenClaw naturally re-indexes on changes

**Cons:**
- Modifies Obsidian notes (adds ~200-500 bytes per note)
- Graph information is implicit in the vector (not explicit for traversal)
- Can't do multi-hop traversal without explicit graph structure

#### B: Graph JSON + Search Script

Parse wiki links into an adjacency list:

```python
# knowledge-graph.json
{
  "Extropy as Happiness": {
    "path": "Foundations/Extropy as Happiness.md",
    "links_to": ["Choice as Prerequisite for Extropy", "Moral Framework"],
    "linked_from": ["Stress Testing Extropy", "Extropy Engine"],
    "connection_count": 18
  }
}
```

A search script does:
1. Vector search (OpenClaw memory_core)
2. Read graph JSON
3. Follow links up to N hops
4. Score results (vector weight + graph distance)
5. Return annotated result set

**Pros:**
- Full control over scoring
- Explicit graph traversal
- Multi-hop connections
- Doesn't modify notes

**Cons:**
- Separate file to maintain
- Needs sync script (nightly cron)
- Model must call the tool explicitly

### Scoring Algorithm

```python
def score_result(vector_score, graph_distance, max_hops=2, decay=0.5):
    if graph_distance == 0:  # Direct vector match
        return vector_score
    else:
        # Graph hops reduce relevance exponentially
        graph_score = decay ** graph_distance
        # Weighted combination
        return 0.7 * vector_score + 0.3 * graph_score
```

### What it gives

| Feature | Status |
|---|---|
| Semantic search | ✅ |
| Keyword search | ✅ |
| Temporal decay | ✅ |
| Diversity filtering | ✅ |
| Auto-indexing | ✅ |
| Graph traversal | ✅ |
| Auto-retrieve | ❌ |
| Associative spreading | ✅ (limited — manual tool call) |

### Limitations

- **No auto-retrieve:** Model must call the search script explicitly
- **Manual:** Each search requires a tool call
- **Slower:** Graph traversal adds latency

### Effort

**1-2 days** for the script + nightly cron for sync.

---

## Solution 3: Auto-Retrieve (Gateway Feature)

### Architecture

```
User message
     ↓
Gateway intercepts
     ↓
Auto-runs memory_search(message)
     ↓
Injects results into system context
     ↓
Model sees: [user message] + [relevant memories]
     ↓
Model responds with full context
```

### How it works

The OpenClaw gateway automatically runs vector search on every user message and injects the top results into the model's context before it generates a response.

### Configuration

```json5
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "autoRetrieve": {
          "enabled": true,
          "maxResults": 3,
          "maxSnippetChars": 500,
          "scope": "direct",  // DMs only, not groups
          "query": {
            "hybrid": {
              "enabled": true,
              "vectorWeight": 0.7,
              "textWeight": 0.3
            }
          }
        }
      }
    }
  }
}
```

### What it gives

| Feature | Status |
|---|---|
| Semantic search | ✅ |
| Keyword search | ✅ |
| Temporal decay | ✅ |
| Diversity filtering | ✅ |
| Auto-indexing | ✅ |
| Graph traversal | ❌ (needs Solution 2) |
| Auto-retrieve | ✅ |
| Associative spreading | Partial (via auto-retrieve + vector) |

### Why this is THE solution

Auto-retrieve transforms memory from a tool the model calls to a background process that's always running. This is how human memory works — memories surface automatically based on context.

Without auto-retrieve, memory is a filing cabinet the model has to consciously search.
With auto-retrieve, memory is a brain that surfaces relevant information automatically.

### Token Savings

See [token-analysis.md](token-analysis.md) for detailed calculations.

### Effort

**1-2 weeks.** Gateway PR to OpenClaw core.

---

## Solution 4: Full HippoRAG Integration

### Architecture

```
Obsidian Vault ──→ Entity extraction (LLM)
                        │
              Knowledge Graph construction
                        │
              Personalized PageRank
                        │
              Multi-hop associative retrieval
```

### How it works

HippoRAG mimics the human hippocampus:
1. LLM extracts entities and relationships from notes
2. Builds a knowledge graph
3. Query triggers Personalized PageRank on the graph
4. Activation spreads to connected concepts
5. Multi-hop retrieval finds indirect connections

### What it gives

| Feature | Status |
|---|---|
| Semantic search | ✅ |
| Keyword search | ✅ |
| Temporal decay | ✅ |
| Diversity filtering | ✅ |
| Auto-indexing | ✅ |
| Graph traversal | ✅ (deep, multi-hop) |
| Auto-retrieve | ❌ (needs Solution 3) |
| Associative spreading | ✅ (full, automatic) |

### Why not start here

- Complex integration (entity extraction, graph construction, PageRank)
- Higher cost (LLM calls for entity extraction)
- Overkill for 56 notes (better for 10K+ notes)
- Can be added later as an upgrade to Solution 2

### Effort

**2-4 weeks.** Significant research integration.

---

## Recommended Path

### Phase 1: Now (5 minutes)
- Enable `extraPaths` in OpenClaw memory config
- Get 80% of human-like memory quality

### Phase 2: This week (1-2 days)
- Build backlinks generator for Obsidian notes
- Build search script with graph traversal
- Get 90% of human-like memory quality

### Phase 3: PR to OpenClaw (1-2 weeks)
- Implement auto-retrieve in gateway
- Get 95% of human-like memory quality
- Saves 70-80% tokens vs current approach

### Phase 4: Future (when scale demands)
- HippoRAG integration for 10K+ notes
- Sleep consolidation for knowledge maintenance
- Get 99% of human-like memory quality
