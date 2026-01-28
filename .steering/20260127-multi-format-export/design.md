# Design: Multi-format Export Feature

**Feature:** F7: Multi-format Export
**Priority:** P2
**Date:** 2026-01-27
**Status:** Draft

---

## Overview

This document defines the implementation design for the Multi-format Export feature, enabling export of collected papers to Markdown, JSON, and CSV formats.

---

## Architecture

### Component Diagram

```
User
  │
  └─► /paper-researcher:paper-export <format> [options]
        │
        └─► skills/paper-exporter/SKILL.md
              │
              └─► skills/paper-exporter/scripts/export_papers.py
                    │
                    ├─► Load index (data/index/papers.json)
                    ├─► Filter papers (by query, date, ID)
                    ├─► Load paper metadata and summaries
                    └─► Write output files
                          │
                          ├─► data/exports/{format}/ (default)
                          └─► custom output directory (optional)
```

---

## Data Flow

1. User invokes `/paper-researcher:paper-export` with format and options
2. Skill invokes `export_papers.py` script
3. Script loads paper index and applies filters
4. Script loads metadata and optional summaries for each paper
5. Script generates output in specified format
6. Script writes to output directory

---

## File Structure

### New Files

```
paper-researcher/
├── commands/
│   └── paper-export.md          # New command
├── skills/
│   └── paper-exporter/
│       ├── SKILL.md              # New skill
│       └── scripts/
│           └── export_papers.py  # New script
├── data/
│   └── exports/                  # Default export directory (gitignored)
│       ├── markdown/
│       ├── json/
│       └── csv/
└── tests/
    └── test_export_papers.py     # New tests
```

---

## Export Formats

### Markdown Export

**Single Paper (`paper_{id}.md`):**
```markdown
# [Paper Title]

**arXiv:** [id]
**Authors:** [author list]
**Published:** [date]
**Categories:** [categories]

## Abstract

[abstract text]

## Summary

[summary if available and --include-summary flag set]

---

*Exported on [date]*
```

**Collection (`papers.md`):**
```markdown
# Paper Collection Export

**Exported:** [date]
**Total Papers:** [count]

---

## Papers

### 1. [Paper Title]
...
```

### JSON Export

**Single Paper (`paper_{id}.json`):**
```json
{
  "id": "2401.12345",
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "...",
  "published": "2024-01-15",
  "categories": ["cs.CL", "cs.AI"],
  "pdf_url": "https://...",
  "collected_at": "2026-01-27T10:00:00Z",
  "summary": "..." // if --include-summary
}
```

**Collection (`papers.json`):**
```json
{
  "exported_at": "2026-01-27T10:00:00Z",
  "count": 12,
  "papers": [...]
}
```

### CSV Export

**Collection (`papers.csv`):**
```csv
id,title,authors,published,categories,has_summary,pdf_url
2401.12345,"Paper Title","Author 1; Author 2",2024-01-15,"cs.CL; cs.AI",true,https://...
```

---

## Script Interface

### export_papers.py

```bash
# Export single paper as Markdown
python export_papers.py --paper-id 2401.12345 --format markdown --output ./export

# Export all papers as JSON
python export_papers.py --all --format json --output ./export

# Export papers matching query as CSV
python export_papers.py --query "attention" --format csv --output ./export

# Export with date filter
python export_papers.py --all --format markdown --since 7d --output ./export

# Include summaries (Markdown and JSON only)
python export_papers.py --all --format markdown --include-summary --output ./export
```

### CLI Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--format` | string | Yes | - | Output format: markdown, json, csv |
| `--paper-id` | string | No | - | Export single paper by ID |
| `--all` | flag | No | - | Export all papers |
| `--query` | string | No | - | Export papers matching query |
| `--since` | string | No | - | Date filter (e.g., "7d", "30d") |
| `--output` | path | No | data/exports/{format}/ | Output directory |
| `--include-summary` | flag | No | False | Include summaries (md, json only) |
| `--data-dir` | path | No | ./data | Data directory |

---

## Functions

### Core Functions

| Function | Purpose |
|----------|---------|
| `validate_arxiv_id(paper_id: str) -> bool` | Validate arXiv ID format |
| `parse_timespan(timespan: str) -> timedelta` | Parse date filter (reuse from digest) |
| `load_index(data_dir: Path) -> dict` | Load paper index |
| `load_paper(paper_id: str, data_dir: Path) -> dict \| None` | Load paper metadata |
| `load_summary(paper_id: str, data_dir: Path) -> str \| None` | Load paper summary |
| `filter_papers(papers: dict, query: str \| None, since: datetime \| None) -> list` | Filter papers |
| `export_markdown(papers: list, output_dir: Path, include_summary: bool) -> int` | Export as Markdown |
| `export_json(papers: list, output_dir: Path, include_summary: bool) -> int` | Export as JSON |
| `export_csv(papers: list, output_dir: Path) -> int` | Export as CSV |

---

## Error Handling

| Error | Response |
|-------|----------|
| Paper not found | Log warning, skip paper |
| Empty collection | Report "No papers to export" |
| Invalid output directory | Create directory if missing |
| Write permission denied | Report error with path |
| Invalid format | Report supported formats |

---

## Testing Strategy

### Unit Tests

- `test_validate_format()` - verify format validation
- `test_filter_papers()` - verify filtering logic
- `test_export_markdown()` - verify Markdown output
- `test_export_json()` - verify JSON output
- `test_export_csv()` - verify CSV output
- `test_single_paper()` - verify single paper export
- `test_include_summary()` - verify summary inclusion
- `test_date_filter()` - verify date filtering
- `test_empty_collection()` - verify empty handling
- `test_invalid_paper_id()` - verify error handling
- `test_cli_arguments()` - verify argument parsing

---

## Dependencies

No new dependencies required. Uses:
- Standard library: `json`, `csv`, `pathlib`, `argparse`, `datetime`
- Existing patterns from F1-F6
