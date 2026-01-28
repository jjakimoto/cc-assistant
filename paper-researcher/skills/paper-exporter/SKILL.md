---
name: paper-exporter
description: "Export collected papers to Markdown, JSON, or CSV formats. This skill should be used when users want to export their paper collection for use in external tools."
---

# Paper Exporter Skill

Export collected papers to various formats for integration with external tools and workflows.

## When to Use

Use this skill when the user wants to:
- Export papers to Markdown for note-taking tools
- Export papers as JSON for programmatic processing
- Export papers as CSV for spreadsheet analysis
- Create backups of their paper collection
- Share paper data with external tools

## Arguments

- `--format` (required): Export format
  - `markdown` - Individual Markdown files per paper
  - `json` - Single JSON file with all papers
  - `csv` - Single CSV file with paper metadata

- Selection (one required):
  - `--all` - Export all papers
  - `--paper-id <id>` - Export single paper by arXiv ID
  - `--query <query>` - Export papers matching search query

- Optional:
  - `--since <timespan>` - Filter by collection date (e.g., 7d, 30d, 1w)
  - `--output <path>` - Custom output directory
  - `--include-summary` - Include full summary content (Markdown, JSON only)

## Workflow

### Step 1: Validate Arguments

Parse and validate all arguments:

1. **Format Validation:**
   - Must be one of: `markdown`, `json`, `csv`
   - If invalid: "Invalid format. Valid formats: markdown, json, csv"

2. **Selection Validation:**
   - Must specify one of: `--all`, `--paper-id`, or `--query`
   - If `--paper-id` specified, validate arXiv ID format (YYMM.NNNNN)

3. **Timespan Validation (if --since provided):**
   - Valid formats: `1d`, `7d`, `14d`, `30d`, `1w`, `24h`
   - If invalid: "Invalid timespan format. Use: 1d, 7d, 14d, 30d, 1w, 24h"

### Step 2: Execute Export

Run the export script from the plugin root directory:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-exporter/scripts/export_papers.py \
    --format markdown \
    --all \
    --data-dir ./data
```

**With options:**
```bash
uv run python skills/paper-exporter/scripts/export_papers.py \
    --format json \
    --query "attention mechanisms" \
    --since 7d \
    --include-summary \
    --output ./my-exports \
    --data-dir ./data
```

**Expected Success Output:**
```json
{
  "success": true,
  "message": "Exported 12 papers as MARKDOWN.",
  "export_count": 12,
  "format": "markdown",
  "output_path": "data/exports/markdown"
}
```

**Expected Empty Output:**
```json
{
  "success": true,
  "message": "No papers match the specified criteria.",
  "export_count": 0,
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

**If export successful:**
```
Exported {export_count} papers as {format}.

Output directory: {output_path}

Files created:
- paper_2401.12345.md
- paper_2401.12346.md
- ...
```

For JSON/CSV:
```
Exported {export_count} papers as {format}.

Output file: {output_path}/papers.{ext}
```

**If no papers to export:**
```
No papers match the specified criteria.

Try:
- Using --all to export all papers
- Adjusting your search query
- Running /paper-collect to collect more papers
```

**If no papers in collection:**
```
No papers in your collection yet.

Run /paper-researcher:paper-collect to collect papers first.

Example:
  /paper-researcher:paper-collect --topic "LLM agents" --days 7
```

## Scripts

### export_papers.py

**Location:** `skills/paper-exporter/scripts/export_papers.py`

**Purpose:** Export papers to Markdown, JSON, or CSV format.

**Usage:**
```bash
python export_papers.py --format <format> [--all | --paper-id <id> | --query <query>] [options]
```

**Arguments:**
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--format` | Yes | - | Export format: markdown, json, csv |
| `--all` | One of these | - | Export all papers |
| `--paper-id` | | - | Export single paper by ID |
| `--query` | | - | Export papers matching query |
| `--since` | No | - | Filter by collection date (e.g., 7d) |
| `--output` | No | `data/exports/{format}/` | Output directory |
| `--include-summary` | No | false | Include summary content |
| `--data-dir` | No | `./data` | Data directory path |

**Processing Steps:**
1. Validate arguments and paper ID format
2. Parse date filter if provided
3. Load paper index from `data/index/papers.json`
4. Filter papers by ID, query, or date range
5. Load full metadata for each paper
6. Optionally load summaries
7. Generate output in specified format
8. Write files atomically to output directory

## Data Storage

**Markdown Output:** `data/exports/markdown/paper_{id}.md`

**JSON Output:** `data/exports/json/papers.json`

**CSV Output:** `data/exports/csv/papers.csv`

## Error Handling

| Error Code | User Message | Action |
|------------|--------------|--------|
| `INDEX_NOT_FOUND` | No papers collected yet | Suggest running /paper-collect |
| `INVALID_PAPER_ID` | Invalid arXiv ID format | Show correct format |
| `INVALID_ARGUMENT` | Invalid format or timespan | Show valid options |
| `INVALID_INDEX` | Paper index is corrupted | Suggest re-running /paper-collect |
| `FILE_ERROR` | Failed to write export files | Check permissions |
| `UNKNOWN_ERROR` | An unexpected error occurred | Report error details |

## Output Format Examples

### Markdown (paper_2401.12345.md)

```markdown
# Paper Title

**arXiv:** [2401.12345](https://arxiv.org/abs/2401.12345)
**Authors:** Author 1, Author 2
**Published:** 2024-01-15
**Categories:** cs.CL, cs.AI

## Abstract

Paper abstract text...

## Summary

Full summary content... (if --include-summary)

---

*Exported on 2026-01-27*
```

### JSON (papers.json)

```json
{
  "exported_at": "2026-01-27T10:00:00Z",
  "count": 12,
  "papers": [
    {
      "id": "2401.12345",
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "abstract": "...",
      "published": "2024-01-15",
      "categories": ["cs.CL", "cs.AI"],
      "pdf_url": "https://...",
      "summary_content": "..." // if --include-summary
    }
  ]
}
```

### CSV (papers.csv)

```csv
"id","title","authors","published","categories","has_summary","pdf_url","collected_at"
"2401.12345","Paper Title","Author 1; Author 2","2024-01-15","cs.CL; cs.AI","true","https://...","2026-01-27T10:00:00Z"
```

## Performance

- Target: < 5 seconds for export of 50 papers
- Loads index once, processes papers in memory
- Atomic file writing to prevent corruption
- Efficient for collections up to 1000 papers

## Related Skills

- `paper-collector` - Collect papers from arXiv
- `paper-summarizer` - Generate summaries for papers
- `paper-searcher` - Search collected papers
- `paper-digest` - Generate digest of recent papers
