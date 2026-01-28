---
name: paper-summarize
description: "Generate or regenerate summary for a specific paper."
allowed-tools: Read, Write, Bash, Task, Skill
---

# Paper Summarize Command

Generate a structured summary for a paper in your collection.

## Usage

```
/paper-researcher:paper-summarize <paper-id>
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<paper-id>` | Yes | arXiv paper ID (e.g., 2401.12345) |

## Examples

Summarize a specific paper:
```
/paper-researcher:paper-summarize 2401.12345
```

## Workflow

This command invokes the `paper-summarizer` skill which:

1. **Reads paper metadata** from `data/papers/{arxiv_id}/metadata.json`
   - Validates paper exists in collection
   - Extracts title, authors, abstract

2. **Generates structured summary** using Claude
   - Applies structured prompt template
   - Creates Problem, Method, Results, Takeaways sections

3. **Saves summary** to `data/papers/{arxiv_id}/summary.md`
   - Formatted markdown for easy reading
   - Includes paper metadata header

4. **Updates status** using `update_summary_status.py`
   - Sets `has_summary: true` in metadata.json
   - Updates index at `data/index/papers.json`

5. **Displays summary** to user

## Output Format

The generated summary follows this structure:

```markdown
# [Paper Title]

**Authors:** [Author list]
**arXiv:** [ID] | **Published:** [Date]

## Problem
[1-2 sentences describing the problem addressed]

## Method
[2-3 sentences describing the approach]

## Results
[Key findings and metrics]

## Takeaways
- [Actionable insight 1]
- [Actionable insight 2]
- [Actionable insight 3]
```

## Error Handling

- **Paper not found**: Suggests running `/paper-collect` first
- **Invalid paper ID**: Reports expected format (YYMM.NNNNN)
- **Missing abstract**: Skips summarization with warning
- **Summary exists**: Regenerates and overwrites existing summary

## Related Commands

- `/paper-researcher:paper-collect` - Collect papers from arXiv
- `/paper-researcher:paper-search` - Search collected papers
- `/paper-researcher:paper-digest` - Generate digest of recent papers
