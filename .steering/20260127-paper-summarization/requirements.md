# Requirements: Paper Summarization Feature

**Feature:** F2: Paper Summarization
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Overview

Generate concise, structured summaries of paper content using Claude. This feature enables users to quickly understand the key insights from collected papers without reading the full text.

## User Stories

1. **As a researcher**, I want automatic summaries when papers are collected so I don't have to manually request them.
2. **As a developer**, I want structured summaries so I can quickly assess paper relevance.
3. **As a user**, I want to re-summarize a specific paper if the initial summary is not satisfactory.

## Acceptance Criteria

- [ ] Auto-generate summaries for all collected papers
- [ ] Use structured format: title, problem, method, results, takeaways
- [ ] Extract text from PDF or use abstract if PDF unavailable
- [ ] Store summaries as markdown in paper directory
- [ ] Handle summarization errors gracefully
- [ ] Update `has_summary` field in metadata and index after summarization

## Functional Requirements

### FR-1: Summary Generation

- Generate summaries using Claude API via Claude Code's built-in access
- Use structured prompt template to ensure consistent output format
- Process paper abstract as primary text source (PDF parsing is P1)
- Save summary as `data/papers/{arxiv_id}/summary.md`

### FR-2: Summary Format

Use the following structured markdown format:

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
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]
```

### FR-3: Status Tracking

- Update `has_summary: true` in paper's `metadata.json` after successful summarization
- Update `has_summary: true` in `data/index/papers.json` for the paper entry
- Track summarization failures and allow retry

### FR-4: Command Interface

- Slash command: `/paper-researcher:paper-summarize`
- Arguments: `<paper-id>` (required): arXiv ID to summarize
- Output: Display generated summary to user

### FR-5: Batch Summarization (Integration)

- Called automatically after paper collection via `paper-collector` skill
- Process all newly collected papers that don't have summaries
- Report count of summaries generated

## Non-Functional Requirements

- **Performance**: Generate 1 summary in under 5 seconds
- **Reliability**: Mark paper as unsummarized on failure, allow retry
- **Graceful degradation**: Skip papers with missing abstracts

## Constraints

- Uses Claude API via Claude Code (no separate API key management)
- Abstract-only summarization for MVP (PDF parsing is P1 enhancement)
- Local filesystem storage
- Python 3.10+ required

## Dependencies

- F1: Paper Collection (must be completed first)
  - Papers must be collected and stored before summarization
  - Uses `data/papers/{id}/metadata.json` created by paper-collector

## Out of Scope

- PDF text extraction (P1 enhancement)
- Summary regeneration with different parameters
- Multi-language summary support
- Summary quality scoring
