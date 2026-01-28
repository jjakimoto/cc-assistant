---
name: paper-citation
description: "Fetch citation data from Semantic Scholar and build citation graph."
---

# Paper Citation Skill

Fetches citation data from the Semantic Scholar API and builds a citation graph to track relationships between papers in your collection.

## Overview

This skill:
1. Fetches citation data (references and citations) from Semantic Scholar API
2. Updates paper metadata with citation information
3. Builds a citation graph index
4. Identifies highly-cited papers in your collection

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/fetch_citations.py` | Fetch citation data from Semantic Scholar API |
| `scripts/build_graph.py` | Build citation graph and identify highly-cited papers |

## Workflow

### Step 1: Fetch Citation Data

Run the fetch script to get citation data from Semantic Scholar:

```bash
# For a single paper
uv run python skills/paper-citation/scripts/fetch_citations.py \
    --paper-id 2401.12345 \
    --data-dir ./data

# For all papers
uv run python skills/paper-citation/scripts/fetch_citations.py \
    --all \
    --data-dir ./data
```

**Output:**
```json
{
  "success": true,
  "papers_processed": 50,
  "papers_with_citations": 45,
  "papers_not_found": 5,
  "errors": []
}
```

### Step 2: Build Citation Graph

After fetching citations, build the graph:

```bash
uv run python skills/paper-citation/scripts/build_graph.py \
    --data-dir ./data \
    --top 10
```

**Output:**
```json
{
  "success": true,
  "total_papers": 50,
  "papers_with_citations": 45,
  "total_edges": 150,
  "highly_cited": [
    {"id": "2301.54321", "cited_by_count": 15},
    {"id": "2312.98765", "cited_by_count": 12}
  ]
}
```

### Step 3: Report Results

Format and display results to the user:

```
Fetched citations for 45/50 papers
5 papers not found in Semantic Scholar

Top cited papers in your collection:
1. [2301.54321] "Paper Title" - 15 citations
2. [2312.98765] "Another Paper" - 12 citations
3. [2310.11111] "Third Paper" - 8 citations

Citation graph saved to data/index/citations.json
```

To get paper titles for the highly-cited papers, read their metadata:
- `data/papers/{paper_id}/metadata.json`

## Data Structures

### Paper Metadata (Extended)

After fetching citations, paper metadata includes:

```json
{
  "id": "2401.12345",
  "title": "Paper Title",
  "citation_data": {
    "source": "semantic_scholar",
    "fetched_at": "2026-01-27T12:00:00",
    "citation_count": 42,
    "reference_count": 25,
    "references_in_collection": ["2301.54321"],
    "cited_by_in_collection": ["2402.11111"]
  }
}
```

### Citations Index

The graph is stored at `data/index/citations.json`:

```json
{
  "version": "1.0",
  "updated_at": "2026-01-27T12:00:00",
  "graph": {
    "2401.12345": {
      "references": ["2301.54321"],
      "cited_by": ["2402.11111"]
    }
  },
  "stats": {
    "total_papers": 50,
    "papers_with_citations": 45,
    "total_edges": 150,
    "highly_cited": ["2301.54321", "2312.98765"]
  }
}
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Paper not in Semantic Scholar | Mark as `source: "unavailable"`, continue |
| Rate limited (429) | Wait 60 seconds, retry |
| Network error | Retry 3x with exponential backoff |
| Invalid paper ID | Skip with warning |
| Empty collection | Return success with 0 papers |

## Rate Limiting

The Semantic Scholar API has rate limits:
- **Unauthenticated:** 100 requests per 5 minutes
- **With API key:** Higher limits (optional)

The script includes a 3-second delay between requests to stay within limits.

## Integration Notes

### With Paper Collection

After collecting papers, you can fetch their citations:
```
/paper-researcher:paper-collect --topic "LLM agents"
/paper-researcher:paper-citations --all
```

### With Paper Search

Citation counts can be used to boost search results (future enhancement).

### With Paper Digest

Digests can include a "highly cited" section (future enhancement).
