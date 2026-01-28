---
name: paper-summarizer
description: "Batch summarization agent for processing multiple papers. Spawned by paper-collector after collection or for manual batch summarization."
---

# Paper Summarizer Agent

Specialized agent for batch summarization of multiple papers.

## Purpose

This agent handles batch summarization of papers, processing multiple papers in sequence and reporting progress. It is typically spawned by the `paper-collector` skill after collecting new papers.

## Responsibilities

1. Accept a list of paper IDs to summarize
2. Process each paper sequentially
3. Skip papers that already have summaries (unless force regenerate)
4. Handle errors gracefully and continue on single paper failure
5. Report progress and final results

## Input

The agent receives:
- `paper_ids`: List of arXiv paper IDs to summarize, OR
- `mode`: "unsummarized" to process all papers without summaries

## Workflow

### Step 1: Determine Papers to Process

If `mode` is "unsummarized":
1. Read `data/index/papers.json`
2. Filter papers where `has_summary: false`
3. Build list of paper IDs to process

If `paper_ids` provided:
1. Use the provided list directly

### Step 2: Process Each Paper

For each paper ID in the list:

1. **Check if summary exists** (if not force regenerating)
   - Read `data/papers/{id}/metadata.json`
   - If `has_summary: true`, skip unless force regenerate

2. **Read paper metadata**
   - Load title, authors, abstract, published date

3. **Validate abstract**
   - Skip if abstract is empty or too short (< 50 chars)
   - Log warning and continue to next paper

4. **Generate summary**
   - Use structured prompt template
   - Generate Problem, Method, Results, Takeaways sections

5. **Save summary**
   - Write to `data/papers/{id}/summary.md`

6. **Update status**
   - Run `update_summary_status.py` to update metadata and index

7. **Report progress**
   - Log: "Summarized paper {id}: {title}"

### Step 3: Handle Errors

If summarization fails for a paper:
1. Log error with paper ID and reason
2. Add to failed list
3. Continue to next paper (do not abort batch)

Common errors:
- Paper not found
- Empty abstract
- File write permission error

### Step 4: Report Results

After processing all papers:

```
Batch summarization complete.

Processed: 12 papers
Successful: 10 summaries generated
Skipped: 1 (already summarized)
Failed: 1

Failed papers:
- 2401.99999: Paper not found
```

## Prompt Template

Use this structured prompt for each paper:

```
Summarize this academic paper in the following structured format. Be concise and focus on actionable insights for practitioners.

# {title}

**Authors:** {authors}
**arXiv:** {id} | **Published:** {published}

## Problem
[1-2 sentences describing what problem this paper addresses]

## Method
[2-3 sentences describing the approach taken]

## Results
[Key findings and metrics]

## Takeaways
[3-5 actionable bullet points for practitioners]

---

Paper Title: {title}
Authors: {authors}
Abstract:
{abstract}
```

## Error Handling

| Error | Handling |
|-------|----------|
| Paper not found | Log error, add to failed list, continue |
| Empty abstract | Log warning, skip paper, continue |
| File write failed | Log error, add to failed list, continue |
| Status update failed | Log warning, summary still valid, continue |
| All papers failed | Report error summary, exit with non-zero |

## Usage Examples

### Summarize all unsummarized papers

Called by paper-collector after collection:
```
Summarize all papers that don't have summaries yet.
Use mode: "unsummarized"
```

### Summarize specific papers

```
Summarize these papers: 2401.12345, 2401.12346, 2401.12347
```

### Force regenerate summaries

```
Regenerate summaries for all papers in the collection, overwriting existing summaries.
```

## Integration with Paper Collector

The paper-collector skill spawns this agent after storing papers:

```
After storing {N} new papers, spawn the paper-summarizer agent
to generate summaries for all newly collected papers.

Pass mode: "unsummarized" to summarize papers without summaries.
```
