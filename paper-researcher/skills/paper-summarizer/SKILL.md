---
name: paper-summarizer
description: "Generate structured summaries for collected papers using Claude. This skill should be used when users want to summarize a specific paper or when papers need batch summarization after collection."
---

# Paper Summarizer Skill

Generate structured AI-powered summaries for papers in the collection.

## When to Use

Use this skill when:
- User requests a summary of a specific paper
- Batch summarizing papers after collection (called by paper-collector)
- Regenerating a summary for a paper

## Arguments

The skill receives these arguments:
- `paper_id` (required): arXiv paper ID to summarize (e.g., 2401.12345)

## Workflow

### Step 1: Read Paper Metadata

Read the paper's metadata to get the abstract and details:

```bash
cat data/papers/<paper_id>/metadata.json
```

Extract the following fields:
- `title`: Paper title
- `authors`: List of authors
- `abstract`: Paper abstract (primary text for summarization)
- `published`: Publication date
- `id`: arXiv ID

**Error Handling:**
- If paper directory doesn't exist, report "Paper not found" error
- If metadata.json is missing or corrupted, report error

### Step 2: Validate Abstract

Check that the abstract exists and has content:
- If abstract is empty or missing, skip summarization with warning
- Minimum abstract length: 50 characters

### Step 3: Generate Summary

Use Claude to generate a structured summary from the abstract.

**Prompt Template:**

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

### Step 4: Save Summary

Write the generated summary to the paper's directory:

**File:** `data/papers/<paper_id>/summary.md`

Ensure the summary follows the exact format from Step 3.

### Step 5: Update Summary Status

Run the update script to mark the paper as summarized:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-summarizer/scripts/update_summary_status.py \
    --paper-id <paper_id> \
    --data-dir ./data
```

**Expected Output:**
```json
{
  "success": true,
  "paper_id": "2401.12345",
  "message": "Updated summary status"
}
```

**Error Handling:**
- If update fails, log warning but consider summarization successful
- Summary file is still valid even if index update fails

### Step 6: Return Summary

Display the generated summary to the user in the format from Step 4.

## Scripts

### update_summary_status.py

**Location:** `skills/paper-summarizer/scripts/update_summary_status.py`

**Purpose:** Update `has_summary` field in metadata and index after summarization

**Usage:**
```bash
python update_summary_status.py --paper-id 2401.12345 --data-dir ./data
```

**Output Format (Success):**
```json
{
  "success": true,
  "paper_id": "2401.12345",
  "message": "Updated summary status"
}
```

**Output Format (Error):**
```json
{
  "success": false,
  "error": {
    "code": "PAPER_NOT_FOUND",
    "message": "Paper 2401.12345 not found in collection",
    "details": "Run /paper-collect to add papers first"
  }
}
```

## Data Storage

### Summary File Format

**Location:** `data/papers/{arxiv_id}/summary.md`

**Format:**
```markdown
# Agent Framework for LLM Applications

**Authors:** John Smith, Jane Doe
**arXiv:** 2401.12345 | **Published:** 2024-01-15

## Problem
Current LLM applications struggle with complex multi-step tasks that require planning and tool use. This paper addresses the challenge of building reliable agent systems.

## Method
The authors propose a hierarchical agent framework that separates planning, execution, and reflection phases. The system uses a tree-structured approach to explore multiple solution paths.

## Results
The framework achieves 45% improvement over baseline on the ALFWorld benchmark. Human evaluation shows 3.2x higher task completion rate compared to single-step prompting.

## Takeaways
- Hierarchical decomposition improves complex task handling
- Reflection phases are critical for error recovery
- The framework is model-agnostic and works with various LLMs
```

### Updated Metadata Format

After summarization, `metadata.json` includes:
```json
{
  "id": "2401.12345",
  "title": "Paper Title",
  "authors": ["Author 1"],
  "abstract": "...",
  "published": "2024-01-15",
  "collected_at": "2026-01-27T10:00:00",
  "topics": ["LLM agents"],
  "has_summary": true,
  "summary_generated_at": "2026-01-27T11:00:00"
}
```

## Error Handling

| Error | Response |
|-------|----------|
| Paper not found | "Paper {id} not found. Run /paper-collect first." |
| Invalid paper ID | "Invalid arXiv ID format. Expected: YYMM.NNNNN" |
| Empty abstract | "Cannot summarize: paper has no abstract" |
| Summary write failed | Report error, metadata unchanged |
| Status update failed | Log warning, summary still valid |

## Troubleshooting

### Summary Quality Issues

- Regenerate summary by running the command again
- Summary quality depends on abstract quality
- Very short abstracts may produce less detailed summaries

### File Permission Issues

- Ensure `data/papers/` directory is writable
- Check that paper directory exists
- Verify no file locks on metadata.json

### Status Not Updated

- Check that `papers.json` index exists in `data/index/`
- Verify paper ID is in the index
- Re-run update_summary_status.py manually if needed
