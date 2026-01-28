# Task List: Daily/Weekly Digest Feature

**Feature:** F4: Daily/Weekly Digest
**Priority:** P1
**Date:** 2026-01-27
**Status:** Active

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] Create `skills/paper-digest/` directory
- [x] Create `skills/paper-digest/scripts/` directory

### Phase 2: Core Script - build_digest.py

- [x] Create `skills/paper-digest/scripts/build_digest.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `parse_timespan(timespan: str) -> timedelta` function
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `filter_papers(papers: dict, since: datetime) -> list` function
- [x] Implement `group_by_topic(papers: list) -> dict[str, list]` function
- [x] Implement `load_summary_snippet(paper_id: str, data_dir: Path, max_chars: int) -> str` function (named `extract_snippet`)
- [x] Implement `build_digest_content(grouped: dict, since: datetime, until: datetime, data_dir: Path) -> str` function
- [x] Implement CLI argument parsing (--since, --data-dir, --output)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing index
- [x] Add error handling for invalid timespan
- [x] Add error handling for file I/O

### Phase 3: Plugin Integration - Command

- [x] Create `commands/paper-digest.md` with YAML frontmatter
- [x] Document command arguments (--since)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-digest skill)
- [x] Add error handling guidance
- [x] Add related commands section

### Phase 4: Plugin Integration - Skill

- [x] Create `skills/paper-digest/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (filter → group → generate → save)
- [x] Add instructions for calling build_digest.py
- [x] Add output format specification
- [x] Add error handling guidance

### Phase 5: Testing Infrastructure

- [x] Create `tests/test_build_digest.py`
- [x] ~~Add test fixtures to `tests/conftest.py`~~ (Reason: Using existing fixtures from conftest.py)

### Phase 6: Unit Tests - build_digest

- [x] Write `test_parse_timespan()` - verify timespan parsing
- [x] Write `test_filter_papers()` - verify date filtering
- [x] Write `test_group_by_topic()` - verify topic grouping
- [x] Write `test_load_summary_snippet()` - verify snippet extraction (named `test_extract_snippet`)
- [x] Write `test_build_digest_content()` - verify markdown generation
- [x] Write `test_empty_collection()` - handle empty index
- [x] Write `test_no_matching_papers()` - handle no papers in timeframe
- [x] Write `test_missing_summary()` - handle papers without summaries
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 7: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with new command documentation

---

## Completion Checklist

- [x] All tests pass (136 tests)
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Command is functional via `/paper-researcher:paper-digest`
- [x] Can generate digest for specified time range
- [x] Papers grouped by topic
- [x] Summary snippets included
- [x] Handles empty collection gracefully
- [x] Performance meets target (< 10 seconds)

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Added `load_metadata()` function to load full paper metadata for topic fallback - not explicitly planned but necessary for robust topic grouping
- Changed function name from `load_summary_snippet` to `extract_snippet` for clarity - snippet extraction is about formatting, not loading
- Added `ensure_ascii=False` to JSON output for consistency with other scripts - identified during code review
- Fixed duplicate metadata loading in `group_by_topic()` - code review identified performance issue
- Added additional tests for `load_metadata` and `load_summary` functions - code review identified missing test coverage

**Lessons Learned:**
- Code review sub-agents are valuable for identifying performance issues (duplicate I/O) and missing test coverage
- The existing patterns from F1-F3 scripts provided excellent templates for consistent implementation
- Test fixtures from conftest.py were sufficient - no new fixtures needed
- The atomic file write pattern with `tempfile.NamedTemporaryFile` + `replace()` is now well-established across all scripts

**Improvement Suggestions:**
- Consider extracting shared utility functions (`validate_arxiv_id`, `load_index`, `load_summary`) into a common module to reduce duplication
- Add TypedDict for paper data structures to improve type safety
- Consider adding `--dry-run` option for previewing digest contents without writing file
- Add arXiv links directly in digest output for quick access to original papers

---

## Notes

- Follow existing patterns from F1-F3 for consistency
- Reuse `validate_arxiv_id()` pattern from other scripts
- Ensure atomic file writing for digest output
