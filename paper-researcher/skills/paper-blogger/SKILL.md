---
name: paper-blogger
description: "Transform paper summaries into engaging blog posts for publishing platforms. This skill should be used when users want to generate a blog-style write-up from a paper's structured summary."
---

# Paper Blogger Skill

Transform academic paper summaries into engaging, accessible blog posts suitable for publishing platforms.

## When to Use

Use this skill when:
- User wants to create a blog post from a paper summary
- User wants to share research findings with a broader audience
- User needs content formatted for publishing platforms (Medium, Dev.to, etc.)

## Arguments

The skill receives these arguments:
- `paper_id` (required): arXiv paper ID to generate blog post for (e.g., 2401.12345)

## Workflow

### Step 1: Read Paper Metadata

Read the paper's metadata to get details:

```bash
cat data/papers/<paper_id>/metadata.json
```

Extract the following fields:
- `title`: Paper title
- `authors`: List of authors
- `abstract`: Paper abstract
- `published`: Publication date
- `id`: arXiv ID
- `categories`: Paper categories (for tags)
- `topics`: User-assigned topics
- `has_summary`: Must be true

**Error Handling:**
- If paper directory doesn't exist, report "Paper not found" error
- If metadata.json is missing or corrupted, report error
- If `has_summary` is not true, report "No summary exists" error

### Step 2: Read Paper Summary

Read the existing summary:

```bash
cat data/papers/<paper_id>/summary.md
```

Extract the structured sections:
- Problem section
- Method section
- Results section
- Takeaways section

**Error Handling:**
- If summary.md doesn't exist, suggest running `/paper-summarize` first

### Step 3: Generate Blog Post

Use Claude to transform the summary into an engaging blog post.

**Prompt Template:**

```
Transform this academic paper summary into an engaging blog post for developers and researchers. The blog post should be accessible, informative, and suitable for publishing on Medium or Dev.to.

**Guidelines:**
- Create an engaging, click-worthy title (not the original paper title)
- Write in a conversational but professional tone
- Explain technical concepts without excessive jargon
- Focus on practical implications and why readers should care
- Include a compelling introduction that hooks the reader
- End with actionable takeaways

**Paper Information:**
- Title: {title}
- Authors: {authors}
- Published: {published}
- arXiv ID: {id}
- Categories: {categories}

**Paper Summary:**
{summary_content}

**Output Format:**

Generate the blog post in exactly this format:

---
title: "[Engaging title - different from paper title]"
date: {today_date}
paper_id: {id}
authors: {authors_list}
tags: {tags_from_categories}
---

# [Same engaging title]

*[One-line teaser about the topic and its significance]*

## The Problem

[2-3 paragraphs explaining the problem in accessible terms. Why should the reader care? What's the real-world impact?]

## The Approach

[2-3 paragraphs explaining the method. Use analogies if helpful. Focus on the key insight, not implementation details.]

## What They Found

[2-3 paragraphs on the results. Emphasize the significance. What does this mean in practice?]

## Why This Matters

[1-2 paragraphs on practical implications. Who should pay attention? What might change because of this work?]

## Key Takeaways

1. [First major takeaway - actionable]
2. [Second major takeaway - actionable]
3. [Third major takeaway - actionable]

---

*This post summarizes "[Original Paper Title]" by [Authors].*
*Read the full paper: [arXiv link]*
```

### Step 4: Save Blog Post

Write the generated blog post to a temporary file and call the save script:

1. Save blog content to a temp file
2. Run the save script:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-blogger/scripts/save_blog_post.py \
    --paper-id <paper_id> \
    --content-file /path/to/temp_blog.md \
    --data-dir ./data
```

**Expected Output:**
```json
{
  "success": true,
  "paper_id": "2401.12345",
  "blog_path": "data/blog-posts/2401.12345.md",
  "message": "Blog post saved successfully"
}
```

**Error Handling:**
- If save fails, report error to user
- If status update fails, log warning but consider blog generation successful

### Step 5: Return Blog Post

Display the generated blog post to the user in full.

## Scripts

### save_blog_post.py

**Location:** `skills/paper-blogger/scripts/save_blog_post.py`

**Purpose:** Save blog post file and update `has_blog_post` field in metadata and index

**Usage:**
```bash
python save_blog_post.py --paper-id 2401.12345 --content "..." --data-dir ./data
python save_blog_post.py --paper-id 2401.12345 --content-file /path/to/blog.md --data-dir ./data
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `--paper-id` | Yes | arXiv paper ID |
| `--content` | Yes* | Blog post content as string |
| `--content-file` | Yes* | Path to file with blog content |
| `--data-dir` | No | Data directory (default: ./data) |

*Either `--content` or `--content-file` is required (mutually exclusive).

**Output Format (Success):**
```json
{
  "success": true,
  "paper_id": "2401.12345",
  "blog_path": "data/blog-posts/2401.12345.md",
  "message": "Blog post saved successfully"
}
```

**Output Format (Error):**
```json
{
  "success": false,
  "error": {
    "code": "NO_SUMMARY",
    "message": "Paper 2401.12345 has no summary",
    "details": "Run /paper-summarize first to generate a summary"
  }
}
```

## Data Storage

### Blog Post File Format

**Location:** `data/blog-posts/{arxiv_id}.md`

**Format:**
```markdown
---
title: "How AI Agents Are Learning to Plan"
date: 2026-01-27
paper_id: 2401.12345
authors: ["John Smith", "Jane Doe"]
tags: ["AI", "LLM", "agents"]
---

# How AI Agents Are Learning to Plan

*A deep dive into hierarchical planning and what it means for the future of AI assistants*

## The Problem

[Content...]

## The Approach

[Content...]

## What They Found

[Content...]

## Why This Matters

[Content...]

## Key Takeaways

1. [Takeaway 1]
2. [Takeaway 2]
3. [Takeaway 3]

---

*This post summarizes "Agent Framework for LLM Applications" by John Smith, Jane Doe.*
*Read the full paper: https://arxiv.org/abs/2401.12345*
```

### Updated Metadata Format

After blog generation, `metadata.json` includes:
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
  "summary_generated_at": "2026-01-27T11:00:00",
  "has_blog_post": true,
  "blog_post_generated_at": "2026-01-27T12:00:00"
}
```

## Error Handling

| Error | Response |
|-------|----------|
| Paper not found | "Paper {id} not found. Run /paper-collect first." |
| Invalid paper ID | "Invalid arXiv ID format. Expected: YYMM.NNNNN" |
| No summary exists | "Paper {id} has no summary. Run /paper-summarize first." |
| Blog post write failed | Report error, metadata unchanged |
| Status update failed | Log warning, blog post still valid |

## Troubleshooting

### Blog Post Quality Issues

- Blog quality depends on summary quality
- Regenerate by running the command again
- Consider regenerating the summary first if blog is low quality

### File Permission Issues

- Ensure `data/blog-posts/` directory exists
- Check write permissions
- Verify no file locks on existing blog post

### Status Not Updated

- Check that `papers.json` index exists in `data/index/`
- Verify paper ID is in the index
- Blog post file is still valid even if status update fails
