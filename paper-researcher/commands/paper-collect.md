---
name: paper-collect
description: "Fetch new papers from arXiv based on topics/keywords and store locally."
allowed-tools: Read, Write, Edit, Bash, Task, Skill
---

# Paper Collection Command

Collect research papers from arXiv based on search topics/keywords.

## Usage

```
/paper-researcher:paper-collect --topic "<topic>" [--days <N>] [--max <N>]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--topic` | Yes | - | Search topic/keywords (e.g., "LLM agents", "transformer models") |
| `--days` | No | 7 | Number of days to look back for papers |
| `--max` | No | 50 | Maximum number of papers to collect |

## Examples

Collect papers on LLM agents from the past week:
```
/paper-researcher:paper-collect --topic "LLM agents"
```

Collect papers on transformers from the past 30 days:
```
/paper-researcher:paper-collect --topic "transformer attention" --days 30
```

Collect up to 20 papers on vision models:
```
/paper-researcher:paper-collect --topic "vision transformer" --max 20
```

## Workflow

This command invokes the `paper-collector` skill which:

1. **Fetches papers from arXiv API** using `fetch_arxiv.py`
   - Constructs search query from topic
   - Applies date range filter
   - Handles API rate limiting and retries

2. **Stores paper metadata locally** using `store_paper.py`
   - Saves each paper to `data/papers/{arxiv_id}/metadata.json`
   - Updates search index at `data/index/papers.json`
   - Skips duplicate papers already in collection

3. **Reports results** to user
   - Count of new papers collected
   - List of paper titles and arXiv IDs

## Output Format

```
Collected 12 new papers on "LLM agents" (past 7 days)

New papers:
1. [2401.12345] "Agent Framework for LLM Applications" - Smith et al.
2. [2401.12346] "Multi-Agent Collaboration in Language Models" - Jones et al.
...

Summaries generated for all 12 papers.
```

## Error Handling

- **arXiv API unavailable**: Retries up to 3 times with exponential backoff
- **No papers found**: Reports empty result, suggests different keywords
- **Network issues**: Reports error with troubleshooting suggestions

## Related Commands

- `/paper-researcher:paper-search` - Search collected papers
- `/paper-researcher:paper-summarize` - Summarize a specific paper
- `/paper-researcher:paper-digest` - Generate digest of recent papers
