---
name: paper-export
description: "Export collected papers to Markdown, JSON, or CSV formats."
allowed-tools: Read, Write, Bash, Skill
---

# Paper Export Command

Export collected papers to various formats for integration with external tools and workflows.

## Usage

```
/paper-researcher:paper-export --format <format> [--all | --paper-id <id> | --query <query>] [options]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--format` | Yes | - | Export format: `markdown`, `json`, or `csv` |
| `--all` | One of | - | Export all papers in collection |
| `--paper-id` | these | - | Export single paper by arXiv ID |
| `--query` | three | - | Export papers matching search query |
| `--since` | No | - | Filter by collection date (e.g., 7d, 30d, 1w) |
| `--output` | No | `data/exports/{format}/` | Output directory path |
| `--include-summary` | No | false | Include full summary (Markdown, JSON only) |

## Examples

**Export all papers as Markdown:**
```
/paper-researcher:paper-export --format markdown --all
```

**Export all papers as JSON with summaries:**
```
/paper-researcher:paper-export --format json --all --include-summary
```

**Export papers as CSV:**
```
/paper-researcher:paper-export --format csv --all
```

**Export single paper:**
```
/paper-researcher:paper-export --format markdown --paper-id 2401.12345
```

**Export papers matching query:**
```
/paper-researcher:paper-export --format json --query "attention mechanisms"
```

**Export recent papers:**
```
/paper-researcher:paper-export --format markdown --all --since 7d
```

**Export to custom directory:**
```
/paper-researcher:paper-export --format json --all --output ./my-exports
```

## Workflow

This command invokes the `paper-exporter` skill which:

1. **Loads paper index** from `data/index/papers.json`
2. **Filters papers** by ID, query, or date range
3. **Loads full metadata** for each paper
4. **Optionally loads summaries** if `--include-summary` is set
5. **Generates output** in the specified format
6. **Writes files** to the output directory
7. **Reports** export count and location

## Output Formats

### Markdown

Individual paper files: `paper_{arxiv_id}.md`

```markdown
# Paper Title

**arXiv:** [2401.12345](https://arxiv.org/abs/2401.12345)
**Authors:** Author 1, Author 2
**Published:** 2024-01-15
**Categories:** cs.CL, cs.AI

## Abstract

Paper abstract text...

## Summary (if --include-summary)

Full summary content...

---

*Exported on 2026-01-27*
```

### JSON

Collection file: `papers.json`

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

### CSV

Collection file: `papers.csv`

```csv
"id","title","authors","published","categories","has_summary","pdf_url","collected_at"
"2401.12345","Paper Title","Author 1; Author 2","2024-01-15","cs.CL; cs.AI","true","https://...","2026-01-27T10:00:00Z"
```

## Error Handling

| Error | Message |
|-------|---------|
| No papers collected | "No papers in collection. Run /paper-collect first." |
| Paper not found | "Paper {id} not found in collection." |
| No matching papers | "No papers match the specified criteria." |
| Invalid format | "Invalid format. Valid formats: markdown, json, csv" |
| Invalid paper ID | "Invalid arXiv ID format: {id}" |
| Invalid timespan | "Invalid timespan format. Use: 1d, 7d, 14d, 30d, 1w, 24h" |

## Related Commands

- `/paper-researcher:paper-collect` - Collect papers from arXiv
- `/paper-researcher:paper-search` - Search collected papers
- `/paper-researcher:paper-digest` - Generate digest of recent papers
- `/paper-researcher:paper-summarize` - Summarize a specific paper
