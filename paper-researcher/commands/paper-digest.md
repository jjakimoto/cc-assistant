---
name: paper-digest
description: "Generate digest of recently collected papers."
allowed-tools: Read, Write, Bash, Skill
---

# Paper Digest Command

Generate a dated digest of recently collected papers, grouped by topic with summary snippets.

## Usage

```
/paper-researcher:paper-digest [--since <timespan>]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--since` | No | `7d` | Time range for papers (e.g., 1d, 7d, 14d, 30d, 1w, 24h) |

## Examples

**Generate weekly digest (default):**
```
/paper-researcher:paper-digest
```

**Generate daily digest:**
```
/paper-researcher:paper-digest --since 1d
```

**Generate bi-weekly digest:**
```
/paper-researcher:paper-digest --since 14d
```

**Generate monthly digest:**
```
/paper-researcher:paper-digest --since 30d
```

## Workflow

This command invokes the `paper-digest` skill which:

1. **Loads paper index** from `data/index/papers.json`
2. **Filters papers** by collection date within the specified range
3. **Groups papers** by topic (or arXiv category if no topics)
4. **Extracts snippets** from summaries (or abstracts as fallback)
5. **Generates markdown** digest and saves to `data/digests/`
6. **Reports** the digest location and paper count

## Output Format

```
Digest generated at data/digests/2026-01-27.md

Included 12 papers from the last 7 days, grouped into 4 topics:
- LLM Agents: 5 papers
- Transformers: 4 papers
- Attention Mechanisms: 2 papers
- Uncategorized: 1 paper

View the digest: data/digests/2026-01-27.md
```

## Digest File Format

```markdown
# Research Paper Digest

**Generated:** 2026-01-27
**Period:** 2026-01-20 to 2026-01-27
**Papers:** 12 (10 with summaries)

---

## LLM Agents

### [2401.12345] Agent Framework for LLM Applications
**Authors:** Smith, Jones, Lee
**Published:** 2026-01-22

> This paper presents a framework for building autonomous LLM agents...

[View Full Summary](../papers/2401.12345/summary.md)

...
```

## Error Handling

| Error | Message |
|-------|---------|
| No papers collected | "No papers in collection. Run /paper-collect first." |
| No papers in timeframe | "No papers collected in the last 7d." |
| Invalid timespan format | "Invalid timespan format. Use: 1d, 7d, 14d, 30d, 1w, 24h" |

## Related Commands

- `/paper-researcher:paper-collect` - Collect papers from arXiv
- `/paper-researcher:paper-search` - Search collected papers
- `/paper-researcher:paper-summarize` - Summarize a specific paper
