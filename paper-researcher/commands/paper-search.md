---
name: paper-search
description: "Search collected papers by keyword or natural language query."
allowed-tools: Read, Bash, Skill
---

# Paper Search Command

Search your collected papers by keyword or question.

## Usage

```
/paper-researcher:paper-search "<query>"
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<query>` | Yes | Search keywords or natural language question |

## Examples

**Search by keyword:**
```
/paper-researcher:paper-search "attention mechanisms"
```

**Search by topic:**
```
/paper-researcher:paper-search "transformer"
```

**Natural language query:**
```
/paper-researcher:paper-search "papers about LLM agents for coding"
```

## Workflow

This command invokes the `paper-searcher` skill which:

1. **Loads paper index** from `data/index/papers.json`
2. **Searches across** titles, abstracts, and summaries
3. **Ranks results** by relevance score
4. **Displays top matches** with excerpts

## Output Format

```
Found 5 papers matching "attention mechanisms":

1. [2401.12345] "Attention is All You Need Revisited" - Smith et al.
   Score: 8.5
   > "...novel attention mechanism that improves on the original..."

2. [2401.12346] "Multi-Head Attention Patterns" - Jones et al.
   Score: 6.0
   > "...analyzing attention patterns across layers..."

No more results.
```

## Error Handling

| Error | Message |
|-------|---------|
| No papers collected | "No papers collected yet. Run /paper-collect first." |
| No matches found | "No papers found matching '<query>'. Try different keywords." |
| Empty query | "Query cannot be empty." |

## Related Commands

- `/paper-researcher:paper-collect` - Collect papers from arXiv
- `/paper-researcher:paper-summarize` - Summarize a specific paper
- `/paper-researcher:paper-digest` - Generate digest of recent papers
