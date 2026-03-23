# Vector Search

## How it works

1. Text is converted to a vector embedding (1536 dimensions)
2. Vector is stored in the [[pgvector]] extension
3. Query text is also converted to a vector
4. Similarity search finds the closest vectors (cosine distance)
5. Results are returned with similarity scores

## Embedding model

- Provider: OpenAI
- Model: text-embedding-3-small
- Dimensions: 1536
- Cost: $0.02 per 1M tokens

## Search modes

- **Exact:** Brute-force comparison (slow but accurate)
- **HNSW:** Approximate nearest neighbor (fast, ~99% accuracy)
- **IVF:** Inverted file index (fastest, ~95% accuracy)

## Hybrid search

Combining vector search with keyword search (BM25) for better results:
- Vector search: "what did I write about X?" (semantic)
- Keyword search: "find document ID abc123" (exact)
- Combined: best of both worlds

## Related

- [[pgvector]] — the PostgreSQL extension
- [[Database Design]] — overall strategy
- [[Schema Design]] — table structure
- [[API Architecture]] — how search is exposed via API
