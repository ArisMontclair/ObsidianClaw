# Token Cost Analysis

## Current Approach: MEMORY.md in Context

### Setup
- MEMORY.md loaded at session start (~5000-8000 tokens)
- Stays in context for every turn
- Processed on every response generation

### Per-session calculation

| Component | Calculation | Tokens |
|---|---|---|
| MEMORY.md | Loaded once | 6,000 (avg) |
| Processed per turn | 6,000 × 30 turns | 180,000 |
| Total | 180,000 + 6,000 | 186,000 |

### Cost (OpenRouter, 32K context)

| Component | Rate | Cost |
|---|---|---|
| Input tokens | $0.15/1M | $0.028 |
| Output tokens | $0.60/1M | $0.018 |
| **Total** | | **$0.046 per session** |

*Note: This is just the MEMORY.md overhead, not the full session cost.*

---

## Auto-Retrieve Approach

### Setup
- MEMORY.md NOT loaded at session start
- Each user message triggers vector search
- Top 3 results injected (~1500 tokens)
- Retrieved snippets fade from context (buried by conversation)

### Per-session calculation

| Component | Calculation | Tokens |
|---|---|---|
| Search queries | 30 turns × 200 tokens | 6,000 |
| Retrieved results | 30 turns × 1500 tokens | 45,000 |
| Results fade | Buried after 5-10 turns | 0 (context management) |
| **Total** | | **51,000** |

### Cost (OpenRouter)

| Component | Rate | Cost |
|---|---|---|
| Embedding queries | $0.13/1M | $0.0008 |
| Search result tokens | $0.15/1M | $0.0068 |
| **Total** | | **$0.0076 per session** |

---

## Comparison

### Token Usage

| Approach | Tokens per 30-turn session | Savings |
|---|---|---|
| MEMORY.md in context | 186,000 | — |
| Auto-retrieve | 51,000 | **72.6%** |

### Dollar Cost

| Approach | Cost per session | Monthly (30 sessions) | Annual |
|---|---|---|---|
| MEMORY.md in context | $0.046 | $1.38 | $16.56 |
| Auto-retrieve | $0.008 | $0.24 | $2.88 |
| **Savings** | **$0.038** | **$1.14** | **$13.68** |

### Context Window Impact

| Approach | Context used | Available for conversation |
|---|---|---|
| MEMORY.md in context | 6,000 tokens (19-25% of 32K) | 26,000 tokens |
| Auto-retrieve | 1,500 tokens (buried) | 30,500 tokens |
| **More room** | | **+4,500 tokens** |

---

## Scaling Analysis

### At 56 notes (current Obsidian vault)

| Approach | Tokens | Cost | Feasibility |
|---|---|---|---|
| Load everything | 50,000+ | $0.50+ per session | Possible but wasteful |
| Auto-retrieve | 51,000 | $0.008 per session | ✅ Optimal |

### At 1,000 notes

| Approach | Tokens | Cost | Feasibility |
|---|---|---|---|
| Load everything | 900,000+ | $9+ per session | ❌ Impossible |
| Auto-retrieve | 51,000 | $0.008 per session | ✅ Scales |

### At 100,000 notes

| Approach | Tokens | Cost | Feasibility |
|---|---|---|---|
| Load everything | 90,000,000+ | $900+ per session | ❌ Impossible |
| Auto-retrieve | 51,000 | $0.008 per session | ✅ Scales linearly |

*Auto-retrieve cost is independent of knowledge base size because it only retrieves the top N results per query.*

---

## Why Auto-Retrieve is Cheaper AND Better

### Lower token usage
- MEMORY.md is always processed (fixed overhead)
- Auto-retrieve only processes what's relevant (variable, but always less)
- Retrieved snippets fade from context (don't accumulate)

### Better quality
- Relevant context instead of entire MEMORY.md (signal vs noise)
- Results are fresh (what's relevant NOW, not what was relevant when MEMORY.md was written)
- Context window is cleaner (more room for conversation)

### Scales
- MEMORY.md grows with knowledge → eventually impossible to load
- Auto-retrieve cost is constant regardless of knowledge size
- At 100K notes, auto-retrieve is the ONLY option

---

## Caveats

1. **Embedding cost:** Auto-retrieve requires embedding the knowledge base initially (~$0.02 for 56 notes). One-time cost.
2. **Query embedding:** Each search requires embedding the query (~$0.0002 per query). Negligible.
3. **Graph traversal:** If we add graph traversal, there's a small cost for reading and following links. Minimal compared to vector search.
4. **Scope limitation:** Auto-retrieve only applies to sessions where it's enabled (e.g., DMs, not groups). Reduces cost further.
