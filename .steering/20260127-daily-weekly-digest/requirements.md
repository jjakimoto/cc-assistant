# Requirements: Daily/Weekly Digest Feature

**Feature:** F4: Daily/Weekly Digest
**Priority:** P1 (Nice-to-Have)
**Date:** 2026-01-27
**Status:** Planning

---

## Feature Description

Generate scheduled summaries of newly collected papers, grouped by topic/relevance with summary snippets for each paper.

---

## User Stories

1. As a researcher, I want a weekly digest of new papers so I can review everything at once.
2. As a developer, I want to see papers grouped by relevance so I can quickly focus on the most important ones.

---

## Acceptance Criteria

From PRD (docs/product-requirements.md):
- [ ] Generate digest of papers collected since last digest
- [ ] Group papers by topic/relevance
- [ ] Include summary snippets for each paper
- [ ] Save digest as dated markdown file

Additional derived requirements:
- [ ] Support customizable time range (--since 7d, --since 1d)
- [ ] Store digests in `data/digests/` directory
- [ ] Handle empty collection gracefully (no papers to digest)
- [ ] Include paper count and date range in digest header

---

## Technical Constraints

- Digest must be generated in < 10 seconds (from architecture.md)
- Store digests as `data/digests/{YYYY-MM-DD}.md`
- Read from existing `data/index/papers.json` and `data/papers/{id}/summary.md`

---

## Dependencies

- Requires F1 (Paper Collection) - papers must exist to generate digest
- Requires F2 (Paper Summarization) - summaries needed for snippets

---

## Out of Scope

- Automatic scheduling (cron-like functionality)
- Email delivery of digests
- Custom digest templates
