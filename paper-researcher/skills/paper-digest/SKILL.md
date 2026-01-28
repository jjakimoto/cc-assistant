---
name: paper-digest
description: "Generate digest of recently collected papers grouped by topic. This skill should be used when users want to review all papers collected in a time period."
---

# Paper Digest Skill

Generate a dated markdown digest of recently collected papers, grouped by topic with summary snippets.

## When to Use

Use this skill when the user wants to:
- Generate a digest of recent papers
- Review papers collected over a time period
- Get an overview of papers by topic
- Create a weekly or daily paper summary

## Arguments

- `--since` (optional, default: "7d"): Time range for papers
  - Formats: `1d`, `7d`, `14d`, `30d`, `1w`, `24h`

## Workflow

### Step 1: Validate Arguments

Parse the `--since` argument if provided, defaulting to "7d".

Valid timespan formats:
- `Nd` - N days (e.g., "7d" = 7 days)
- `Nw` - N weeks (e.g., "1w" = 7 days)
- `Nh` - N hours (e.g., "24h" = 24 hours)

If invalid format:
```
Error: Invalid timespan format: '{value}'.

Use one of: 1d, 7d, 14d, 30d, 1w, 24h
```

### Step 2: Generate Digest

Run the digest script from the plugin root directory:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-digest/scripts/build_digest.py \
    --since 7d \
    --data-dir ./data
```

**Expected Success Output:**
```json
{
  "success": true,
  "message": "Digest generated with 12 papers.",
  "papers_count": 12,
  "topics_count": 4,
  "output_path": "data/digests/2026-01-27.md"
}
```

**Expected Empty Output:**
```json
{
  "success": true,
  "message": "No papers collected in the last 7d.",
  "papers_count": 0,
  "output_path": null
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

**If digest generated:**
```
Digest generated at {output_path}

Included {papers_count} papers from the last {since}, grouped into {topics_count} topics.

View the digest: {output_path}
```

**If no papers in timeframe:**
```
No papers collected in the last {since}.

Try:
- Using a longer time range (e.g., --since 30d)
- Running /paper-collect to collect more papers

Last collection was at: [read from index updated_at]
```

**If no papers in collection:**
```
No papers in your collection yet.

Run /paper-researcher:paper-collect to collect papers first.

Example:
  /paper-researcher:paper-collect --topic "LLM agents" --days 7
```

## Scripts

### build_digest.py

**Location:** `skills/paper-digest/scripts/build_digest.py`

**Purpose:** Generate dated markdown digest of papers grouped by topic.

**Usage:**
```bash
python build_digest.py --since <timespan> [--data-dir ./data] [--output path/to/digest.md]
```

**Arguments:**
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--since` | No | `7d` | Time range for papers (1d, 7d, 14d, 30d, 1w, 24h) |
| `--data-dir` | No | `./data` | Path to data directory |
| `--output` | No | `data/digests/{date}.md` | Output file path |

**Processing Steps:**
1. Parse timespan argument
2. Load paper index from `data/index/papers.json`
3. Filter papers by `collected_at` within date range
4. Group papers by topic (falling back to arXiv category, then "Uncategorized")
5. For each paper, extract snippet from summary (or abstract if no summary)
6. Generate markdown with header, topic sections, and footer
7. Write atomically to `data/digests/{date}.md`

## Data Storage

**Digest Output:** `data/digests/{YYYY-MM-DD}.md`

Example: `data/digests/2026-01-27.md`

## Error Handling

| Error Code | User Message | Action |
|------------|--------------|--------|
| `INDEX_NOT_FOUND` | No papers collected yet | Suggest running /paper-collect |
| `INVALID_ARGUMENT` | Invalid timespan format | Show valid formats |
| `INVALID_INDEX` | Paper index is corrupted | Suggest re-running /paper-collect |
| `FILE_ERROR` | Failed to write digest file | Check permissions |
| `UNKNOWN_ERROR` | An unexpected error occurred | Report error details |

## Performance

- Target: < 10 seconds for digest generation
- Loads index once, iterates papers in memory
- Efficient for collections up to 1000 papers
- Atomic file writing to prevent corruption

## Related Skills

- `paper-collector` - Collect papers from arXiv
- `paper-summarizer` - Generate summaries for papers
- `paper-searcher` - Search collected papers
