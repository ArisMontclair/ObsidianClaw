# ObsidianClaw

**Consciousness-like memory for OpenClaw with an Obsidian interface**

## The Problem

Large Language Models are stateless. Every session starts fresh. Current solutions bolt memory onto the outside — load a markdown file, search a vector store, or embed everything into the context window. None of these are how human memory works.

Human memory is **associative, automatic, and unconscious**. You don't decide to remember something — it surfaces because the context triggered it. Someone says "database schema" and your brain lights up with PostgreSQL, migrations, indexing, performance. You didn't search for those memories. They surfaced because the network of associations connected them.

LLMs have no equivalent. They have:

- **Context windows** — finite, expensive, and dumb. Load everything or load nothing. No relevance weighting.
- **Tool-based retrieval** — explicit search calls that the model has to consciously decide to make. This is not how memory works.
- **RAG pipelines** — vector similarity search that finds semantically similar text. Good for "what did I write about X?" Bad for "what connects to X in unexpected ways?"

The gap between these and human memory is not a scaling problem. It's an **architecture problem**.

## What Human Memory Actually Does

Three mechanisms make human memory feel alive:

### 1. Associative Spreading

Think "apple." Automatically, "red," "tree," "Newton," "phone" activate. Not because you searched. Because the neural network connects them. The entire web of associations lights up at once.

LLMs can simulate this through **knowledge graphs** — nodes connected by edges, where one query activates connected nodes. HippoRAG (NeurIPS'24) demonstrated this using Personalized PageRank on knowledge graphs, achieving multi-hop retrieval that flat vector search cannot.

### 2. Context-Dependent Priming

Your environment primes relevant memories. Walk into a kitchen → cooking memories activate. Talk about a project → all project-related knowledge activates. The brain pre-loads relevant context without conscious decision.

For LLMs, this means **auto-retrieval** — automatically searching memory when a user message arrives, injecting results into the model's context before it generates a response. No tool call needed. The memories are just there.

### 3. Sleep Consolidation

During sleep, the brain replays the day's experiences, extracts patterns, strengthens important connections, and forgets noise. This is not passive storage — it's active processing.

For LLMs, this means **periodic re-indexing** — processing conversation logs, extracting key decisions, updating the knowledge base, and pruning noise. SleepGate (arXiv:2603.14517, March 2026) demonstrated 99.5% retrieval accuracy using this approach.

## Current OpenClaw Memory Architecture

OpenClaw already has a memory system:

### What exists

| Component | Status | Description |
|---|---|---|
| `memory_search` | Working | Vector similarity search over MEMORY.md + memory/*.md |
| `memory_get` | Working | Read specific memory files by path |
| `memory-core` plugin | Working | SQLite + sqlite-vec for vector storage |
| `extraPaths` | Working | Index additional directories beyond default memory |
| Hybrid search | Working | Vector + BM25 keyword matching |
| Temporal decay | Working | Exponential decay based on file age |
| MMR re-ranking | Working | Diversity filtering to prevent redundant results |
| Embedding cache | Working | Caches embeddings to avoid re-indexing unchanged text |
| Auto-retrieve | **Missing** | No automatic context injection on user messages |
| Graph traversal | **Missing** | No wiki link parsing or graph structure |

### What it does well

- Indexes markdown files with vector embeddings
- Supports multiple embedding providers (OpenAI, Gemini, Voyage, Ollama, local)
- Hybrid search (semantic + keyword) for both natural language and exact token matching
- Temporal decay so recent memories rank higher
- MMR diversity so results aren't redundant

### What it can't do

- **Automatic retrieval**: The model has to decide to call `memory_search`. This is like a human having to consciously decide to remember something. It defeats the purpose.
- **Graph traversal**: No parsing of wiki links, no graph edges, no multi-hop associative spreading. Flat vector search only.
- **Associative spreading**: A query about "authentication" will never surface "deployment strategy" — they're connected through 3 hops in a knowledge graph, but vector search can't follow those connections.

## The Obsidian Interface

[Obsidian](https://obsidian.md) is a knowledge management tool that stores notes as local markdown files. Its killer feature: **wiki links** (`[[Note Name]]`) that create bidirectional connections between notes.

Obsidian's graph view visualizes these connections. It's a natural interface for human knowledge — you write notes, link them together, and see the web of associations.

**Obsidian is already a knowledge graph.** The wiki links ARE edges. The notes ARE nodes. The graph structure already exists in the markdown files. What's missing is a system that can traverse this graph automatically and inject relevant results into the LLM's context.

## Solutions (Ranked by Impact)

### Solution 1: Vector Search (OpenClaw existing + extraPaths)

**What it is:** Point OpenClaw's existing `memory_search` at the Obsidian vault using `extraPaths`.

**How it works:**
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

**What it gives:**
- Semantic search across all Obsidian notes
- Hybrid keyword + vector matching
- Temporal decay (recent notes rank higher)
- MMR diversity (no redundant results)
- Automatic indexing on file changes
- No custom code needed

**What it's missing:**
- No graph traversal (wiki links aren't followed)
- No auto-retrieve (model must call memory_search explicitly)
- ~80% of human-like memory quality

**Effort:** Config change. 5 minutes.

---

### Solution 2: Graph Traversal (Backlinks + Script)

**What it is:** Parse wiki links from Obsidian notes into a graph structure, then traverse it after vector search to expand results.

**Two approaches:**

#### Approach A: Backlinks in Notes

Add incoming connections to each note using Obsidian's fold syntax:

```markdown
<!-- %% fold %% -->
## Backlinks
- [[Auth Design]] - used in API architecture
- [[Deployment Strategy]] - foundation of infrastructure decisions
```

When OpenClaw embeds the note, the backlinks become part of the vector. The graph is embedded implicitly.

**Pros:** No separate files, no sync scripts, graph is always in sync.
**Cons:** Modifies Obsidian notes, adds ~200-500 bytes per note, graph information is implicit in the vector (not explicit for traversal).

#### Approach B: Graph JSON + Search Script

Parse wiki links into an adjacency list, store as JSON, query after vector search:

```python
# knowledge-graph.json structure
{
  "Auth Design": {
    "path": "architecture/Auth Design.md",
    "links_to": ["JWT Implementation", "API Security"],
    "linked_from": ["Deployment Strategy", "API Architecture"],
    "connection_count": 18
  }
}
```

A search script (`search_vault.py`) does:
1. Vector search (OpenClaw memory_core)
2. Read graph JSON
3. Follow links up to N hops
4. Score results (vector weight + graph distance)
5. Return annotated result set

**Pros:** Full control over scoring, explicit graph traversal, doesn't modify notes.
**Cons:** Separate file to maintain, needs sync script (nightly cron), model must call the tool.

**Effort:** 1-2 days for the script, nightly cron for sync.

---

### Solution 3: Auto-Retrieve (Gateway Feature — THE PR)

**What it is:** OpenClaw gateway automatically runs `memory_search` on every user message and injects results into the model's context.

**How it would work:**

```
User sends: "tell me about the database architecture"
         ↓
Gateway intercepts
         ↓
Auto-runs memory_search("database architecture")
         ↓
Finds: Auth Design (0.94)
       API Security (0.87)
       JWT Implementation (0.82)
         ↓
Injects as system message:
  [Relevant memories: Auth Design: "Stateless authentication with 
   JWT tokens. Session management via Redis..." | API Security: "..."]
         ↓
Model sees context automatically
         ↓
Model responds with full knowledge, no tool call needed
```

**Config:**
```json5
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "autoRetrieve": {
          "enabled": true,
          "maxResults": 3,
          "maxSnippetChars": 500,
          "scope": "direct"  // DMs only, not groups
        }
      }
    }
  }
}
```

**What it gives:**
- Memories surface automatically (no conscious decision to search)
- Context-dependent priming (relevant memories injected based on conversation)
- Lower token usage (see analysis below)
- Human-like memory recall

**Effort:** Gateway PR. 1-2 weeks.

---

### Solution 4: Full HippoRAG Integration

**What it is:** Integrate HippoRAG's Personalized PageRank algorithm into OpenClaw's memory search.

**How it works:**
- LLM extracts entities and relationships from Obsidian notes
- Builds a knowledge graph
- Query triggers PageRank on the graph → spreads activation to connected concepts
- Multi-hop retrieval: "How does auth connect to the caching strategy?" → traverses the graph

**What it gives:**
- True associative spreading
- Multi-hop retrieval
- Automatic connection discovery (finds hidden relationships)

**Effort:** Significant. Requires integrating HippoRAG, knowledge graph construction, and PageRank computation.

## Token Cost Analysis

### Current Approach (MEMORY.md in context)

| Component | Tokens per session |
|---|---|
| MEMORY.md loaded at start | 5,000 - 8,000 |
| Processed on every turn (30 turns) | 150,000 - 240,000 |
| **Total per session** | **~155,000 - 248,000** |

### Auto-Retrieve Approach

| Component | Tokens per session |
|---|---|
| MEMORY.md NOT loaded | 0 |
| Search per turn (30 turns × ~1,500) | 45,000 |
| Retrieved snippets fade from context | 0 (buried) |
| **Total per session** | **~45,000** |

**Savings: 70-80% fewer tokens.** And the quality is BETTER because:
- Relevant context instead of entire MEMORY.md (signal vs noise)
- Cleaner context window (more room for conversation)
- Results are fresh (what's relevant NOW, not what was relevant when MEMORY.md was written)

## Examples: What Auto-Retrieve Would Sound Like

### Without Auto-Retrieve (Current)

**User:** "What's your take on the project timeline?"

**Model:** "I'm not sure I have context on that specific project. Could you remind me what you mean?"

*The model doesn't remember. It has to be told. Every time.*

### With Auto-Retrieve (Proposed)

**User:** "What's your take on the project timeline?"

**Model:** "You estimated 3 weeks for the MVP, but last Tuesday you realized the auth module needs a refactor that adds 4 days. You also noted that the design review on Friday flagged API versioning as a blocker. So realistically, 4 weeks. You mentioned wanting to parallelize the frontend work with the backend once the API contracts are locked."

*The model remembers. It connects concepts. It sounds alive.*

### Without Auto-Retrieve

**User:** "Remember what we decided about the database schema?"

**Model:** "I don't have specific recall of that conversation. Can you give me more context?"

### With Auto-Retrieve

**User:** "Remember what we decided about the database schema?"

**Model:** "You went with PostgreSQL with vector extensions instead of a separate vector store. The decision was driven by wanting a single source of truth — no separate sync pipeline. You discussed this on March 15th, decided it was worth the tradeoff of slightly slower vector queries for simpler architecture. This connects to your earlier note about preferring 'boring technology that works' over 'exciting technology that breaks.'"

*The model remembers the conversation, the reasoning, and the connections.*

## Research Papers

| Paper | Year | Key Contribution |
|---|---|---|
| [HippoRAG](https://arxiv.org/abs/2405.14831) | NeurIPS'24 | Knowledge graph + Personalized PageRank for associative spreading |
| [HippoRAG 2](https://arxiv.org/abs/2502.14802) | ICML'25 | Non-parametric continual learning, improved associativity |
| [MemGPT](https://arxiv.org/abs/2310.08560) | 2024 | OS-inspired virtual memory for LLMs, self-managed paging |
| [SleepGate](https://arxiv.org/abs/2603.14517) | 2026 | Sleep-inspired memory consolidation, 99.5% retrieval accuracy |
| [Memory Mechanisms Survey](https://arxiv.org/abs/2504.15965) | 2025 | Comprehensive survey mapping human memory to AI memory |

## Related Projects

| Project | Description |
|---|---|
| [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections) | Obsidian plugin for local embeddings |
| [MotherDuck Obsidian RAG](https://github.com/sspaeti/obsidian-note-taking-assistant) | DuckDB vector search + wiki link traversal |
| [HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) | Neurobiologically inspired RAG |
| [MemGPT/Letta](https://github.com/cpacker/MemGPT) | OS-inspired virtual memory |

## Repository Structure

```
ObsidianClaw/
├── README.md                    # This file
├── docs/
│   ├── problem.md               # Deep dive into the memory problem
│   ├── solutions.md             # Detailed solution comparison
│   ├── architecture.md          # Technical architecture
│   ├── token-analysis.md        # Token cost analysis
│   ├── examples.md              # Before/after examples
│   └── research.md              # Paper references and findings
├── scripts/
│   ├── generate-backlinks.py    # Add backlinks to Obsidian notes
│   ├── search-vault.py          # Vector search + graph traversal
│   ├── index-vault.py           # Index Obsidian vault to SQLite
│   └── knowledge-graph.py       # Parse wiki links → adjacency list
├── config/
│   ├── openclaw-memory.json     # OpenClaw memory configuration
│   └── vault-memory.json        # Vault memory configuration
├── pr/
│   ├── auto-retrieve.md         # PR proposal for auto-retrieve feature
│   └── graph-traversal.md       # PR proposal for graph traversal
└── examples/
    ├── before-after.md          # Example conversations
    └── association-demo.md      # Association strength demonstration
```

## Contributing

This project is a working prototype and a proposal for OpenClaw integration. Contributions welcome:

1. **Scripts** — Build the Python tools for backlinks, graph traversal, vault indexing
2. **Testing** — Test with your own Obsidian vault
3. **PR preparation** — Help prepare the auto-retrieve PR for OpenClaw core
4. **Documentation** — Improve explanations, add examples

## License

MIT
