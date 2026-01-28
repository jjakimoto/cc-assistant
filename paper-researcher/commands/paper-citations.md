---
name: paper-citations
description: "Fetch citation data and build citation graph for collected papers."
allowed-tools: Read, Write, Edit, Bash, Skill
---

# Paper Citations

Fetch citation data from Semantic Scholar and build a citation graph for your collected papers. Identifies highly-cited papers in your collection and tracks relationships between papers.

## Arguments

- `<paper-id>` (optional): Fetch citations for a specific paper by arXiv ID
- `--all` (flag): Fetch citations for all papers in your collection

**Note:** One of `<paper-id>` or `--all` is required.

## Examples

### Fetch citations for a single paper

```
/paper-researcher:paper-citations 2401.12345
```

### Fetch citations for all papers

```
/paper-researcher:paper-citations --all
```

## Workflow

1. Invoke the `paper-citation` skill
2. The skill will:
   - Fetch citation data from Semantic Scholar API
   - Update paper metadata with citation information
   - Build the citation graph
   - Identify highly-cited papers
3. Display results including:
   - Number of papers processed
   - Papers found/not found in Semantic Scholar
   - Top cited papers in your collection
   - Path to the citation graph index

## Output

```
Fetched citations for 45/50 papers
5 papers not found in Semantic Scholar

Top cited papers in your collection:
1. [2301.54321] "Paper Title" - 15 citations
2. [2312.98765] "Another Paper" - 12 citations
3. [2310.11111] "Third Paper" - 8 citations

Citation graph saved to data/index/citations.json
```

## Error Handling

- **Paper not in collection**: Shows error message with available papers
- **Invalid paper ID**: Shows expected format (YYMM.NNNNN)
- **API rate limited**: Automatically waits and retries
- **Network errors**: Retries up to 3 times with exponential backoff
- **Paper not in Semantic Scholar**: Marked as unavailable, processing continues

## Related Commands

- `/paper-researcher:paper-collect` - Collect papers first before fetching citations
- `/paper-researcher:paper-search` - Search papers (results can be boosted by citation count)
- `/paper-researcher:paper-digest` - Generate digest (can include highly-cited papers)
