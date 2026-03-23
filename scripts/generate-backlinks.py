#!/usr/bin/env python3
"""
Generate backlinks for Obsidian vault.

Parses wiki links from all .md files, computes the inverse (which notes link TO each note),
and inserts a folded backlinks section at the bottom of each note.

Usage:
    python3 generate-backlinks.py --vault /path/to/obsidian/vault [--dry-run] [--graph-json]

Options:
    --vault PATH        Path to Obsidian vault root
    --dry-run           Show what would be changed without modifying files
    --graph-json        Also output knowledge-graph.json
    --output PATH       Path for graph JSON (default: ./knowledge-graph.json)
"""

import os
import re
import json
import argparse
import hashlib
from collections import defaultdict
from pathlib import Path


def parse_wiki_links(content: str) -> list[str]:
    """Extract wiki links from markdown content."""
    # Match [[Link]] or [[Link|Display Text]]
    pattern = r'\[\[([^]|]+?)(?:\|[^]]*)?\]\]'
    return [link.strip() for link in re.findall(pattern, content)]


def build_graph(vault_path: str) -> dict:
    """
    Build adjacency list from wiki links.
    
    Returns:
        {
            "Note Title": {
                "path": "relative/path/to/note.md",
                "links_to": ["Target1", "Target2"],
                "linked_from": ["Source1", "Source2"],
                "connection_count": 4
            }
        }
    """
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


def has_backlinks_section(content: str) -> bool:
    """Check if content already has a backlinks section."""
    return bool(re.search(r'## Backlinks', content, re.IGNORECASE))


def remove_existing_backlinks(content: str) -> str:
    """Remove existing backlinks section from content."""
    # Match from ## Backlinks to end of file or next ## heading
    pattern = r'\n*## Backlinks.*?(?=\n## |\Z)'
    return re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)


def generate_backlinks_section(title: str, incoming_links: list[str], graph: dict) -> str:
    """Generate the backlinks section for a note."""
    if not incoming_links:
        return ""
    
    lines = ["\n", "<!-- %% fold %% -->", "## Backlinks"]
    
    for source in sorted(incoming_links):
        source_data = graph.get(source, {})
        links_to = source_data.get("links_to", [])
        
        # Find context: what does the source link to in this note?
        # (This is simplified — in practice you'd extract the surrounding context)
        lines.append(f"- [[{source}]]")
    
    return "\n".join(lines)


def update_note_backlinks(note_path: Path, backlinks_section: str, dry_run: bool = False):
    """Insert or update backlinks section in a note."""
    content = note_path.read_text(encoding="utf-8")
    
    # Remove existing backlinks if present
    if has_backlinks_section(content):
        content = remove_existing_backlinks(content)
    
    # Append new backlinks section
    new_content = content.rstrip() + "\n" + backlinks_section + "\n"
    
    if dry_run:
        print(f"  [DRY RUN] Would update: {note_path}")
        print(f"    Backlinks: {backlinks_section.count('- [[')} links")
    else:
        note_path.write_text(new_content, encoding="utf-8")
        print(f"  Updated: {note_path} ({backlinks_section.count('- [[')} backlinks)")


def main():
    parser = argparse.ArgumentParser(description="Generate backlinks for Obsidian vault")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault root")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without modifying files")
    parser.add_argument("--graph-json", action="store_true", help="Also output knowledge-graph.json")
    parser.add_argument("--output", default="./knowledge-graph.json", help="Path for graph JSON")
    
    args = parser.parse_args()
    vault_path = Path(args.vault)
    
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return
    
    print(f"Building graph from {vault_path}...")
    graph = build_graph(str(vault_path))
    
    print(f"\nGraph stats:")
    print(f"  Notes: {len(graph)}")
    print(f"  Total links: {sum(len(v['links_to']) for v in graph.values())}")
    print(f"  Avg connections: {sum(v['connection_count'] for v in graph.values()) / len(graph):.1f}")
    
    print(f"\nMost connected:")
    by_connections = sorted(graph.items(), key=lambda x: x[1]['connection_count'], reverse=True)[:5]
    for title, data in by_connections:
        print(f"  {title}: {data['connection_count']} connections")
    
    # Generate backlinks for each note
    print(f"\nGenerating backlinks...")
    updated = 0
    
    for title, data in graph.items():
        incoming = data["linked_from"]
        if not incoming:
            continue
        
        note_path = vault_path / data["path"]
        if not note_path.exists():
            continue
        
        backlinks_section = generate_backlinks_section(title, incoming, graph)
        if not backlinks_section:
            continue
        
        update_note_backlinks(note_path, backlinks_section, dry_run=args.dry_run)
        updated += 1
    
    print(f"\nDone. Updated {updated} notes.")
    
    # Output graph JSON
    if args.graph_json:
        with open(args.output, 'w') as f:
            json.dump(graph, f, indent=2)
        print(f"Graph saved to {args.output}")


if __name__ == "__main__":
    main()
