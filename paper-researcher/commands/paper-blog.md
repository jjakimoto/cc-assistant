---
name: paper-blog
description: "Transform a paper summary into a readable blog post for publishing platforms."
allowed-tools: Read, Write, Bash, Skill
---

# Paper Blog Command

Transform a paper summary into an engaging, readable blog post suitable for publishing platforms.

## Usage

```
/paper-researcher:paper-blog <paper-id>
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `<paper-id>` | Yes | arXiv paper ID (e.g., 2401.12345) |

## Examples

Generate a blog post for a specific paper:
```
/paper-researcher:paper-blog 2401.12345
```

## Workflow

This command invokes the `paper-blogger` skill which:

1. **Reads paper metadata** from `data/papers/{arxiv_id}/metadata.json`
   - Validates paper exists in collection
   - Extracts title, authors, abstract, publication date

2. **Reads paper summary** from `data/papers/{arxiv_id}/summary.md`
   - Validates summary exists
   - Extracts structured content (Problem, Method, Results, Takeaways)

3. **Generates blog post** using Claude
   - Transforms academic summary into accessible narrative
   - Creates engaging introduction and conclusion
   - Formats for publishing platforms

4. **Saves blog post** to `data/blog-posts/{arxiv_id}.md`
   - Includes YAML front matter for static site generators
   - Formatted markdown for publishing

5. **Updates status** using `save_blog_post.py`
   - Sets `has_blog_post: true` in metadata.json
   - Updates index at `data/index/papers.json`

6. **Displays blog post** to user

## Output Format

The generated blog post follows this structure:

```markdown
---
title: "Engaging Title Based on Paper"
date: YYYY-MM-DD
paper_id: arxiv_id
authors: [author1, author2]
tags: [topic1, topic2]
---

# Engaging Title

*A deep dive into [topic] and what it means for [audience]*

## The Problem

[Hook and context - why readers should care]

## The Approach

[Technical explanation made accessible]

## What They Found

[Key results and their significance]

## Why This Matters

[Practical implications and applications]

## Key Takeaways

1. [Takeaway 1]
2. [Takeaway 2]
3. [Takeaway 3]

---

*Based on "[Paper Title]" by [Authors]*
*arXiv: [link]*
```

## Error Handling

- **Paper not found**: Suggests running `/paper-collect` first
- **Invalid paper ID**: Reports expected format (YYMM.NNNNN)
- **No summary exists**: Suggests running `/paper-summarize` first
- **Blog post exists**: Regenerates and overwrites existing blog post

## Related Commands

- `/paper-researcher:paper-collect` - Collect papers from arXiv
- `/paper-researcher:paper-summarize` - Generate paper summaries
- `/paper-researcher:paper-search` - Search collected papers
- `/paper-researcher:paper-digest` - Generate digest of recent papers
