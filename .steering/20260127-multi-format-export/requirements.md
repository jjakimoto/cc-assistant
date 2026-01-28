# Requirements: Multi-format Export Feature

**Feature:** F7: Multi-format Export
**Priority:** P2
**Date:** 2026-01-27
**Status:** Draft

---

## Overview

Enable users to export their collected papers and summaries to multiple formats for integration with external tools and workflows.

---

## User Stories

### US1: Markdown Export
As a researcher, I want to export my paper collection as Markdown files so I can integrate them with my note-taking tools.

### US2: JSON Export
As a developer, I want to export paper data as JSON so I can process it programmatically.

### US3: CSV Export
As a researcher, I want to export paper metadata as CSV so I can analyze it in spreadsheet tools.

---

## Acceptance Criteria

### Export Formats

- [ ] Support Markdown export (individual papers or collection)
- [ ] Support JSON export (full metadata)
- [ ] Support CSV export (tabular metadata)

### Export Options

- [ ] Export single paper by ID
- [ ] Export all papers in collection
- [ ] Export papers matching a search query
- [ ] Filter by date range
- [ ] Include/exclude summaries option

### Output

- [ ] Save to specified output directory
- [ ] Use sensible default filenames
- [ ] Report count of exported papers

### Error Handling

- [ ] Handle missing papers gracefully
- [ ] Handle empty collection
- [ ] Handle invalid output directory
- [ ] Handle write permission errors

---

## Constraints

- Reuse existing patterns from F1-F6 for consistency
- No external dependencies beyond what's already in pyproject.toml
- Follow established naming conventions

---

## Out of Scope

- PDF annotations integration (mentioned in PRD but complex)
- Notion export (requires API authentication)
- Obsidian vault integration (mentioned in PRD but requires vault setup)
- Real-time sync with external tools

---

## References

- PRD Section 2.3: F7: Multi-format Export
- Existing export patterns in build_digest.py
