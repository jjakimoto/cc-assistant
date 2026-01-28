# Task List: Paper Summarization Feature

**Feature:** F2: Paper Summarization
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] Create `skills/paper-summarizer/` directory
- [x] Create `skills/paper-summarizer/scripts/` directory
- [x] Create `agents/` directory (if not exists)

### Phase 2: Core Script - update_summary_status.py

- [x] Create `skills/paper-summarizer/scripts/update_summary_status.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `update_metadata(paper_id: str, data_dir: Path) -> bool` function
- [x] Implement `update_index(paper_id: str, data_dir: Path) -> bool` function
- [x] Implement atomic file writing with tempfile
- [x] Implement CLI argument parsing (--paper-id, --data-dir)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing paper
- [x] Add error handling for file I/O failures

### Phase 3: Plugin Integration - Command

- [x] Create `commands/paper-summarize.md` with YAML frontmatter
- [x] Document command arguments (<paper-id>)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-summarizer skill)
- [x] Add error handling guidance
- [x] Add related commands section

### Phase 4: Plugin Integration - Skill

- [x] Create `skills/paper-summarizer/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (read metadata → generate summary → save → update status)
- [x] Add Claude prompt template for summary generation
- [x] Add instructions for reading paper metadata
- [x] Add instructions for writing summary.md
- [x] Add instructions for calling update_summary_status.py
- [x] Add error handling guidance
- [x] Add output format specification

### Phase 5: Plugin Integration - Agent

- [x] Create `agents/paper-summarizer.md`
- [x] Define agent purpose (batch summarization)
- [x] Define agent responsibilities
- [x] Add workflow for processing multiple papers
- [x] Add progress reporting instructions
- [x] Add error handling (continue on single failure)

### Phase 6: Testing Infrastructure

- [x] Create `tests/test_update_summary_status.py`
- [x] Add test fixtures to `tests/conftest.py` for summary testing
- [x] Create `tests/fixtures/sample_summary.md` for expected output

### Phase 7: Unit Tests - update_summary_status

- [x] Write `test_update_metadata()` - verify metadata update
- [x] Write `test_update_index()` - verify index update
- [x] Write `test_paper_not_found()` - handle missing paper
- [x] Write `test_invalid_paper_id()` - handle invalid ID format
- [x] Write `test_atomic_write()` - verify no corruption on failure
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 8: Integration with Paper Collector

- [x] Update `skills/paper-collector/SKILL.md` to call paper-summarizer after collection
- [x] Add step to spawn paper-summarizer agent for batch processing
- [x] Update result reporting to include summary count

### Phase 9: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with new command documentation
- [x] Add paper-summarize to related commands in paper-collect.md

---

## Completion Checklist

- [x] All tests pass
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Command is functional via `/paper-researcher:paper-summarize`
- [x] Can generate summary for single paper
- [x] Summary saved to correct location
- [x] metadata.json updated with has_summary: true
- [x] index updated with has_summary: true
- [x] paper-collector integrates with summarizer

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Added defensive validation inside `update_metadata()` and `update_index()` functions - identified during code review as a security enhancement
- Improved temp file cleanup using proper initialization and `finally` block instead of `if "tmp_path" in locals()` pattern - cleaner and more robust error handling
- Existing `conftest.py` fixtures were sufficient - no additional fixtures needed to be added

**Lessons Learned:**
- Code review sub-agents are valuable for identifying security issues (path traversal defense, race conditions in cleanup) that may be missed during initial implementation
- The atomic file write pattern using `tempfile.NamedTemporaryFile` + `replace()` requires careful variable initialization to handle cleanup properly
- Following existing patterns (fetch_arxiv.py, store_paper.py) ensures consistency and reduces code review friction
- The `finally` block approach for temp file cleanup is more robust than checking `if "tmp_path" in locals()`

**Improvement Suggestions:**
- Consider extracting the atomic JSON update pattern into a shared helper function to reduce duplication between update_metadata and update_index
- Add integration tests that test the full skill workflow (read metadata → generate summary → save → update status)
- Consider adding timezone information to timestamps (use `datetime.now(timezone.utc).isoformat()`)
- Future: add PDF text extraction capability for papers with PDFs available
