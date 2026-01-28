# Task List: Paper Search Feature

**Feature:** F3: Paper Search
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] Create `skills/paper-searcher/` directory
- [x] Create `skills/paper-searcher/scripts/` directory

### Phase 2: Core Script - search_index.py

- [x] Create `skills/paper-searcher/scripts/search_index.py`
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `tokenize(text: str) -> list[str]` function (renamed from tokenize_query for consistency)
- [x] Implement `calculate_relevance(query_terms, paper, summary) -> float` function (enhanced from search_paper)
- [x] Implement `extract_excerpt(query_terms, text, max_length) -> str` function
- [x] Implement `search_papers(query: str, data_dir: Path, limit: int) -> tuple[list, int]` function
- [x] Implement CLI argument parsing (--query, --data-dir, --limit)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing index
- [x] Add error handling for empty query
- [x] Add error handling for invalid data directory
- [x] Add `count_matches()` helper function
- [x] Add `load_summary()` function for loading summary content
- [x] Add `positive_int()` argparse type for validation

### Phase 3: Plugin Integration - Command

- [x] Create `commands/paper-search.md` with YAML frontmatter
- [x] Document command arguments (<query>)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-searcher skill)
- [x] Add error handling guidance
- [x] Add related commands section

### Phase 4: Plugin Integration - Skill

- [x] Create `skills/paper-searcher/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (load index → search → format results)
- [x] Add instructions for calling search_index.py
- [x] Add result formatting instructions
- [x] Add error handling guidance
- [x] Add output format specification

### Phase 5: Testing Infrastructure

- [x] Create `tests/test_search_index.py`
- [x] ~~Create `tests/fixtures/search_index.json`~~ (Reason: Using existing conftest.py fixtures instead)
- [x] ~~Add test fixtures to `tests/conftest.py`~~ (Reason: Existing fixtures sufficient)

### Phase 6: Unit Tests - search_index

- [x] Write `test_load_index()` - verify index loading (TestLoadIndex class)
- [x] Write `test_tokenize()` - verify query tokenization (TestTokenize class)
- [x] Write `test_calculate_relevance()` - verify relevance scoring (TestCalculateRelevance class)
- [x] Write `test_extract_excerpt()` - verify excerpt generation (TestExtractExcerpt class)
- [x] Write `test_search_papers()` - verify end-to-end search (TestSearchPapers class)
- [x] Write `test_empty_query()` - handle empty query
- [x] Write `test_no_results()` - handle no matches
- [x] Write `test_missing_index()` - handle missing index file
- [x] Write `test_cli_arguments()` - verify argument parsing (TestCliArguments class)

### Phase 7: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with new command documentation
- [x] Add paper-search to related commands in other command files (already present)

---

## Completion Checklist

- [x] All tests pass
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Command is functional via `/paper-researcher:paper-search`
- [x] Can search papers by keyword
- [x] Returns ranked results with excerpts
- [x] Handles empty results gracefully
- [x] Handles missing index gracefully
- [x] Performance meets target (< 2 seconds)

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Added `validate_arxiv_id()` function to prevent path traversal attacks - identified during code review as a critical security enhancement
- Added validation in `load_summary()` function to reject malicious paper IDs
- Added validation in main search loop to skip papers with invalid IDs from corrupted index
- Changed `scored_papers` tuple to include summary content to avoid duplicate file I/O (performance optimization)
- Function naming: `tokenize_query` was named `tokenize()` for consistency and reusability
- Function naming: `search_paper` was expanded to `calculate_relevance()` for clarity
- Added additional helper functions: `count_matches()`, `load_summary()`, `positive_int()`

**Lessons Learned:**
- Code review sub-agents are valuable for identifying security issues (path traversal defense) that may be missed during initial implementation
- Following existing patterns (fetch_arxiv.py, store_paper.py) ensures consistency and reduces code review friction
- Storing computed values in tuples (like summary content) during iteration prevents duplicate I/O operations
- Test coverage should include security tests for path traversal and input validation from the start
- The 4-tuple pattern `(score, paper_id, paper, summary)` effectively caches intermediate values during search

**Improvement Suggestions:**
- Consider extracting the arXiv ID validation pattern into a shared module to reduce duplication across scripts
- Add test for query too long (MAX_QUERY_LENGTH) edge case
- Add tests for OSError handling paths in load_summary
- Future: Consider semantic search using embeddings for better natural language query support
- Future: Add support for phrase matching (quoted terms)
- Future: Add filtering by date, author, or category
