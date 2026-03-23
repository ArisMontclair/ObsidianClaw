#!/usr/bin/env python3
"""
Search Obsidian vault with vector search + graph traversal.

Combines OpenClaw's memory-core vector search with wiki link graph traversal
for consciousness-like associative memory retrieval.

Usage:
    python3 search-vault.py "query text" [--vault /path/to/vault] [--hops 2] [--decay 0.5]

Options:
    --vault PATH        Path to Obsidian vault root
    --hops N            Maximum graph hops (default: 2)
    --decay N           Hop decay factor (default: 0.5)
    --max-results N     Maximum results to return (default: 5)
    --graph-json PATH   Path to knowledge-graph.json
    --vector-weight N   Weight for vector similarity (default: 0.7)
    --graph-weight N    Weight for graph distance (default: 0.3)
"""

import os
import re
import json
import math
import argparse
from pathlib import Path
from collections import defaultdict


def parse_wiki_links(content: str) -> list[str]:
    """Extract wiki links from markdown content."""
    pattern = r'\[\[([^]|]+?)(?:\|[^]]*)?\]\]'
    return [link.strip() for link in re.findall(pattern, content)]


def load_graph(graph_path: str) -> dict:
    """Load pre-computed graph from JSON file."""
    with open(graph_path, 'r') as f:
        return json.load(f)


def build_graph(vault_path: str) -> dict:
    """Build graph from vault on-the-fly."""
    vault = Path(vault_path)
    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    all_notes = {}
    
    for md_file in vault.rglob("*.md"):
        title = md_file.stem
        rel_path = md_file.relative_to(vault)
        all_notes[title] = str(rel_path)
        
        content = md_file.read_text(encoding="utf-8")
        links = parse_wiki_links(content)
        
        for link in links:
            outgoing[title].add(link)
            incoming[link].add(title)
    
    graph = {}
    for title in all_notes:
        graph[title] = {
            "path": all_notes[title],
            "links_to": sorted(list(outgoing.get(title, set()))),
            "linked_from": sorted(list(incoming.get(title, set()))),
            "connection_count": len(outgoing.get(title, set())) + len(incoming.get(title, set()))
        }
    
    return graph


def vector_search_simulation(query: str, vault_path: str, top_k: int = 5) -> list[dict]:
    """
    Simulate vector search (in production, this calls OpenClaw memory_search).
    
    For now, does keyword matching as a stand-in.
    In production: use OpenClaw's memory_search tool or sqlite-vec.
    """
    vault = Path(vault_path)
    results = []
    query_lower = query.lower()
    
    for md_file in vault.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8").lower()
        
        # Simple keyword scoring (replace with actual vector search)
        query_words = query_lower.split()
        score = sum(1 for word in query_words if word in content)
        
        if score > 0:
            # Extract snippet around first match
            first_match = content.find(query_words[0])
            start = max(0, first_match - 200)
            end = min(len(content), first_match + 400)
            snippet = content[start:end].strip()
            
            results.append({
                "title": md_file.stem,
                "path": str(md_file.relative_to(vault)),
                "score": score / len(query_words),
                "snippet": snippet,
                "distance": 0  # Direct match
            })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def graph_traverse(start_notes: list[str], graph: dict, max_hops: int = 2, decay: float = 0.5) -> dict:
    """
    Traverse graph from starting notes, following wiki links.
    
    Returns expanded set of notes with scores based on:
    - Graph distance (hops from starting notes)
    - Connection count (how many notes link to this one)
    """
    visited = {}
    queue = [(note, 0, 1.0) for note in start_notes]  # (note, distance, score)
    
    while queue:
        note, distance, score = queue.pop(0)
        
        if note in visited and visited[note]["score"] >= score:
            continue
        
        if distance > max_hops:
            continue
        
        visited[note] = {
            "distance": distance,
            "score": score,
            "source": "graph" if distance > 0 else "vector"
        }
        
        # Follow outgoing links
        note_data = graph.get(note, {})
        for linked_note in note_data.get("links_to", []):
            if linked_note in graph:
                new_score = score * decay
                queue.append((linked_note, distance + 1, new_score))
        
        # Follow incoming links
        for linked_note in note_data.get("linked_from", []):
            if linked_note in graph:
                new_score = score * decay
                queue.append((linked_note, distance + 1, new_score))
    
    return visited


def combine_results(vector_results: list[dict], graph_results: dict, 
                   vector_weight: float = 0.7, graph_weight: float = 0.3) -> list[dict]:
    """
    Combine vector search and graph traversal results.
    
    Scoring:
    - Vector results: vector_weight * vector_score + graph_weight * graph_score
    - Graph-only results: graph_weight * graph_score (vector_score = 0)
    """
    combined = {}
    
    # Add vector results
    for result in vector_results:
        title = result["title"]
        combined[title] = {
            "title": title,
            "path": result["path"],
            "snippet": result["snippet"],
            "vector_score": result["score"],
            "graph_score": 0,
            "distance": result["distance"],
            "source": "vector"
        }
    
    # Add graph results
    for title, data in graph_results.items():
        if title in combined:
            # Update graph score for existing vector result
            combined[title]["graph_score"] = data["score"]
            combined[title]["distance"] = min(combined[title]["distance"], data["distance"])
            combined[title]["source"] = "both"
        else:
            # New graph-only result
            combined[title] = {
                "title": title,
                "path": graph_results.get(title, {}).get("path", ""),
                "snippet": "",
                "vector_score": 0,
                "graph_score": data["score"],
                "distance": data["distance"],
                "source": "graph"
            }
    
    # Calculate final score
    for title, data in combined.items():
        data["final_score"] = (
            vector_weight * data["vector_score"] + 
            graph_weight * data["graph_score"]
        )
    
    # Sort by final score
    results = sorted(combined.values(), key=lambda x: x["final_score"], reverse=True)
    return results


def format_results(results: list[dict], max_results: int = 5) -> str:
    """Format results for display."""
    output = []
    
    for i, result in enumerate(results[:max_results], 1):
        output.append(f"{i}. {result['title']}")
        output.append(f"   Score: {result['final_score']:.3f} (vector: {result['vector_score']:.3f}, graph: {result['graph_score']:.3f})")
        output.append(f"   Source: {result['source']}, Distance: {result['distance']} hops")
        if result["snippet"]:
            snippet = result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"]
            output.append(f"   Snippet: {snippet}")
        output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Search Obsidian vault with vector + graph traversal")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault root")
    parser.add_argument("--hops", type=int, default=2, help="Maximum graph hops")
    parser.add_argument("--decay", type=float, default=0.5, help="Hop decay factor")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum results")
    parser.add_argument("--graph-json", help="Path to pre-computed graph JSON")
    parser.add_argument("--vector-weight", type=float, default=0.7, help="Vector similarity weight")
    parser.add_argument("--graph-weight", type=float, default=0.3, help="Graph distance weight")
    
    args = parser.parse_args()
    vault_path = Path(args.vault)
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return
    
    # Load or build graph
    if args.graph_json and os.path.exists(args.graph_json):
        print(f"Loading graph from {args.graph_json}...")
        graph = load_graph(args.graph_json)
    else:
        print(f"Building graph from {vault_path}...")
        graph = build_graph(str(vault_path))
    
    print(f"Graph: {len(graph)} notes, {sum(len(v['links_to']) for v in graph.values())} links")
    
    # Vector search
    print(f"\nVector search: '{args.query}'...")
    vector_results = vector_search_simulation(args.query, str(vault_path), top_k=args.max_results)
    print(f"Found {len(vector_results)} vector results")
    
    # Graph traversal
    print(f"Graph traversal: {args.hops} hops, decay={args.decay}...")
    start_notes = [r["title"] for r in vector_results]
    graph_results = graph_traverse(start_notes, graph, max_hops=args.hops, decay=args.decay)
    print(f"Found {len(graph_results)} graph results")
    
    # Combine results
    final_results = combine_results(
        vector_results, graph_results,
        vector_weight=args.vector_weight,
        graph_weight=args.graph_weight
    )
    
    # Display
    print(f"\n{'='*60}")
    print(f"Results for: '{args.query}'")
    print(f"{'='*60}\n")
    print(format_results(final_results, max_results=args.max_results))


if __name__ == "__main__":
    main()
