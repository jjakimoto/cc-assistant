# Task List: Multi-format Export Feature

**Feature:** F7: Multi-format Export
**Priority:** P2
**Date:** 2026-01-27
**Status:** Completed

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] Create `skills/paper-exporter/` directory
- [x] Create `skills/paper-exporter/scripts/` directory
- [x] ~~Create `data/exports/` directory structure (gitignored)~~ (Reason: Created dynamically at runtime)

### Phase 2: Core Script - export_papers.py

- [x] Create `skills/paper-exporter/scripts/export_papers.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `parse_timespan(timespan: str) -> timedelta` function
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `load_paper(paper_id: str, data_dir: Path) -> dict | None` function
- [x] Implement `load_summary(paper_id: str, data_dir: Path) -> str | None` function
- [x] Implement `filter_papers(papers: dict, query: str | None, since: datetime | None) -> list` function
- [x] Implement `export_markdown(papers: list, output_dir: Path, include_summary: bool, data_dir: Path) -> int` function
- [x] Implement `export_json(papers: list, output_dir: Path, include_summary: bool, data_dir: Path) -> int` function
- [x] Implement `export_csv(papers: list, output_dir: Path) -> int` function
- [x] Implement CLI argument parsing (--format, --paper-id, --all, --query, --since, --output, --include-summary, --data-dir)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing papers
- [x] Add error handling for invalid format
- [x] Add error handling for file I/O failures

### Phase 3: Plugin Integration - Command

- [x] Create `commands/paper-export.md` with YAML frontmatter
- [x] Document command arguments (--format, --paper-id, --all, --query, etc.)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-exporter skill)
- [x] Add error handling guidance
- [x] Add related commands section

### Phase 4: Plugin Integration - Skill

- [x] Create `skills/paper-exporter/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (filter → export → report)
- [x] Add instructions for calling export_papers.py
- [x] Add output format specification
- [x] Add error handling guidance

### Phase 5: Testing Infrastructure

- [x] Create `tests/test_export_papers.py`

### Phase 6: Unit Tests - export_papers

- [x] Write `test_validate_format()` - verify format validation
- [x] Write `test_filter_papers()` - verify filtering logic
- [x] Write `test_export_markdown()` - verify Markdown output
- [x] Write `test_export_json()` - verify JSON output
- [x] Write `test_export_csv()` - verify CSV output
- [x] Write `test_single_paper_export()` - verify single paper export
- [x] Write `test_include_summary()` - verify summary inclusion
- [x] Write `test_date_filter()` - verify date filtering
- [x] Write `test_empty_collection()` - verify empty handling
- [x] Write `test_invalid_paper_id()` - verify error handling
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 7: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with new command documentation

---

## Completion Checklist

- [x] All tests pass (254 tests total, 46 new for this feature)
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Command is functional via `/paper-researcher:paper-export`
- [x] Can export single paper
- [x] Can export all papers
- [x] Can export with query filter
- [x] Can export with date filter
- [x] Markdown format works correctly
- [x] JSON format works correctly
- [x] CSV format works correctly
- [x] Include summary option works
- [x] Handles empty collection gracefully
- [x] Handles missing papers gracefully

---

## Notes

- Follow existing patterns from F1-F6 for consistency
- Reuse `validate_arxiv_id()` pattern from other scripts
- Reuse `parse_timespan()` from build_digest.py
- Use atomic file writing for all outputs

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Removed `MIN_QUERY_LENGTH` and `MAX_QUERY_LENGTH` constants after code review identified them as unused
- Data exports directory is created dynamically at runtime rather than as part of initial setup (consistent with other skills)
- Added `tokenize()` function for query matching, reusing pattern from `search_index.py`
- Used `summary_content` field in JSON export instead of `summary` - this is an intentional distinction to differentiate from the `has_summary` boolean flag

**Lessons Learned:**
1. **Pattern Consistency**: Following established patterns from F1-F6 significantly accelerated implementation. The atomic write pattern, validation functions, and error handling format were all reused successfully.
2. **Code Review Value**: The code-reviewer and implementation-validator sub-agents identified unused constants that were copied but not needed, preventing code smell.
3. **Mutually Exclusive Arguments**: Using argparse's mutually exclusive groups (`--all`, `--paper-id`, `--query`) provides clear UX and simplifies validation logic.
4. **Test Coverage**: Writing comprehensive tests (46 total) upfront caught the unused import issue during the lint phase.
5. **Ruff Format**: Running `ruff format` after implementation ensures consistent code style across the project.

**Improvement Suggestions:**
1. **Extract Shared Utilities**: Functions like `validate_arxiv_id()`, `load_index()`, `parse_timespan()`, and `tokenize()` are duplicated across 7+ scripts. Consider creating `skills/common/utils.py` to reduce duplication.
2. **Progress Logging**: For large exports (100+ papers), add periodic progress logging (e.g., "Exported 50/100 papers...")
3. **Batch Export for JSON**: Consider adding `--single-file` option for JSON to export individual JSON files per paper (matching markdown behavior).
4. **Dry-run Option**: Add `--dry-run` flag to preview what would be exported without writing files.
5. **Integration Tests**: Add end-to-end integration tests that test the full skill workflow from command invocation through file output.
