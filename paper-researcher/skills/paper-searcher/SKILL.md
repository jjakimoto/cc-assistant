---
name: paper-searcher
description: "Search collected papers by keyword or natural language query. This skill should be used when users want to find papers in their collection matching specific topics or questions."
---

# Paper Searcher Skill

Search across collected papers by keyword or question, returning ranked results with relevant excerpts.

## When to Use

Use this skill when the user wants to:
- Search their collected papers
- Find papers on a specific topic
- Answer questions about their paper collection
- Look up papers by keyword

## Arguments

- `query` (required): Search keywords or natural language question

## Workflow

### Step 1: Validate Arguments

Ensure the query argument is provided and non-empty.

If no query provided:
```
Error: Query is required. Please provide search keywords.

Usage: /paper-researcher:paper-search "<query>"
```

### Step 2: Search Papers

Run the search script from the plugin root directory:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-searcher/scripts/search_index.py \
    --query "<query>" \
    --data-dir ./data \
    --limit 10
```

**Expected Success Output:**
```json
{
  "success": true,
  "query": "attention mechanisms",
  "total_papers": 50,
  "match_count": 5,
  "results": [
    {
      "id": "2401.12345",
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "score": 8.5,
      "excerpt": "...matching text excerpt..."
    }
  ]
}
```

**Expected Error Output (to stderr):**
```json
{
  "success": false,
  "error": {
    "code": "INDEX_NOT_FOUND",
    "message": "No papers collected yet. Run /paper-collect first.",
    "details": "..."
  }
}
```

### Step 3: Display Results

Parse the JSON output and format for the user.

**If matches found:**
```
Found {match_count} papers matching "{query}":

1. [{id}] "{title}" - {authors joined by ", "}
   Score: {score}
   > "{excerpt}"

2. [{id}] "{title}" - {authors joined by ", "}
   Score: {score}
   > "{excerpt}"

...

Searched {total_papers} papers in your collection.
```

**If no matches found:**
```
No papers found matching "{query}".

Try:
- Using different keywords
- Searching for broader terms
- Running /paper-collect to add more papers

Searched {total_papers} papers in your collection.
```

**If no papers in collection:**
```
No papers in your collection yet.

Run /paper-researcher:paper-collect to collect papers first.

Example:
  /paper-researcher:paper-collect --topic "LLM agents" --days 7
```

## Scripts

### search_index.py

**Location:** `skills/paper-searcher/scripts/search_index.py`

**Purpose:** Search paper index and return ranked results with excerpts.

**Usage:**
```bash
python search_index.py --query "<query>" [--data-dir ./data] [--limit 10]
```

**Arguments:**
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--query` | Yes | - | Search query (keywords or natural language) |
| `--data-dir` | No | `./data` | Path to data directory |
| `--limit` | No | `10` | Maximum results to return |

**Search Algorithm:**
- Tokenizes query into lowercase keywords
- Searches across title (3x weight), abstract (2x weight), summary (1.5x weight), topics (1x weight)
- Ranks results by total weighted score
- Extracts relevant excerpts showing matched content

## Error Handling

| Error Code | User Message | Action |
|------------|--------------|--------|
| `INDEX_NOT_FOUND` | No papers collected yet | Suggest running /paper-collect |
| `INVALID_QUERY` | Query cannot be empty | Ask user to provide a query |
| `INVALID_INDEX` | Paper index is corrupted | Suggest re-running /paper-collect |
| `UNKNOWN_ERROR` | An unexpected error occurred | Report error details |

## Performance

- Target: < 2 seconds for search results
- In-memory search (loads index once)
- Simple keyword matching (no heavy dependencies)
- Efficient for collections up to 1000 papers

## Related Skills

- `paper-collector` - Collect papers from arXiv
- `paper-summarizer` - Generate summaries for papers
- `paper-digest` - Generate digest of recent papers
