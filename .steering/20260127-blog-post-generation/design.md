# Design: Blog Post Generation Feature

**Feature:** F6: Blog Post Generation
**Priority:** P1
**Date:** 2026-01-27
**Status:** Draft

---

## Implementation Approach

Follow existing plugin patterns established in F1-F5.

---

## Components to Create

### 1. Command
- `commands/paper-blog.md`
- Arguments: `<paper-id>` (required)
- Invokes `paper-blogger` skill

### 2. Skill
- `skills/paper-blogger/SKILL.md`
- Workflow: read metadata → read summary → generate blog post → save
- Uses Claude prompt for transformation

### 3. Script
- `skills/paper-blogger/scripts/save_blog_post.py`
- Validates paper ID
- Creates blog post directory
- Saves blog post markdown
- Updates metadata with `has_blog_post: true`
- Updates index

---

## Data Flow

```
User → /paper-blog <id>
  → Command invokes skill
  → Skill reads metadata.json
  → Skill reads summary.md
  → Skill generates blog post via Claude prompt
  → Skill calls save_blog_post.py
  → Script saves to data/blog-posts/{id}.md
  → Script updates metadata and index
```

---

## File Structure Changes

```
data/
├── blog-posts/              # NEW: Blog post output directory
│   └── 2401.12345.md
├── papers/
│   ├── 2401.12345/
│   │   ├── metadata.json    # Updated: has_blog_post field
│   │   └── summary.md
│   └── ...
└── index/
    └── papers.json          # Updated: has_blog_post field
```

---

## Blog Post Template

```markdown
# [Engaging Title Based on Paper]

*A deep dive into [topic] and what it means for [audience]*

## The Problem

[Hook - why should readers care?]
[Context from paper's problem section]

## The Approach

[Technical explanation made accessible]
[Key methodology points]

## What They Found

[Key results and metrics]
[Significance of findings]

## Why This Matters

[Practical implications]
[Who should pay attention]

## Key Takeaways

1. [Takeaway 1]
2. [Takeaway 2]
3. [Takeaway 3]

---

*Paper: [Title] by [Authors]*
*arXiv: [link]*
```

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Paper not found | Return error: "Paper {id} not found in collection" |
| Summary not found | Return error: "Paper {id} has no summary. Run /paper-summarize first" |
| Blog post exists | Regenerate and overwrite (no confirmation in skill mode) |

---

## Testing Strategy

- Unit tests for `save_blog_post.py`
- Test validation, file creation, metadata update
- Follow existing test patterns from F1-F5
