# Task List: Citation Graph Feature

**Feature:** F5: Citation Graph
**Priority:** P1
**Date:** 2026-01-27
**Status:** Active

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] Create `skills/paper-citation/` directory
- [x] Create `skills/paper-citation/scripts/` directory

### Phase 2: Core Script - fetch_citations.py

- [x] Create `skills/paper-citation/scripts/fetch_citations.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `fetch_with_retry(arxiv_id: str, max_retries: int) -> dict | None` function with exponential backoff
- [x] Implement `extract_arxiv_ids(references: list[dict]) -> list[str]` function
- [x] Implement `filter_in_collection(arxiv_ids: list[str], index: dict) -> list[str]` function
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `update_metadata(paper_id: str, citation_data: dict, data_dir: Path) -> bool` function
- [x] Implement CLI argument parsing (--paper-id, --all, --data-dir)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for API failures
- [x] Add error handling for rate limiting (429)
- [x] Add 3-second delay between requests

### Phase 3: Core Script - build_graph.py

- [x] Create `skills/paper-citation/scripts/build_graph.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `load_paper_metadata(paper_id: str, data_dir: Path) -> dict | None` function
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `build_graph(data_dir: Path) -> dict` function
- [x] Implement `calculate_stats(graph: dict) -> dict` function
- [x] Implement `get_highly_cited(graph: dict, top_n: int) -> list[tuple[str, int]]` function
- [x] Implement `save_index(index: dict, data_dir: Path) -> None` function with atomic write
- [x] Implement CLI argument parsing (--data-dir, --top)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing/corrupted metadata

### Phase 4: Plugin Integration - Command

- [x] Create `commands/paper-citations.md` with YAML frontmatter
- [x] Document command arguments (<paper-id>, --all)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-citation skill)
- [x] Add error handling guidance
- [x] Add related commands section

### Phase 5: Plugin Integration - Skill

- [x] Create `skills/paper-citation/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (fetch → build graph → report)
- [x] Add instructions for calling fetch_citations.py
- [x] Add instructions for calling build_graph.py
- [x] Add output format specification
- [x] Add error handling guidance

### Phase 6: Testing Infrastructure

- [x] Create `tests/test_fetch_citations.py`
- [x] Create `tests/test_build_graph.py`
- [x] Create `tests/fixtures/semantic_scholar_response.json`

### Phase 7: Unit Tests - fetch_citations

- [x] Write `test_validate_arxiv_id()` - verify ID validation
- [x] Write `test_fetch_with_retry_success()` - verify successful fetch
- [x] Write `test_fetch_with_retry_not_found()` - verify 404 handling
- [x] Write `test_fetch_with_retry_rate_limited()` - verify 429 handling
- [x] Write `test_extract_arxiv_ids()` - verify ID extraction
- [x] Write `test_filter_in_collection()` - verify collection filtering
- [x] Write `test_update_metadata()` - verify metadata update
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 8: Unit Tests - build_graph

- [x] Write `test_build_graph()` - verify graph construction
- [x] Write `test_calculate_stats()` - verify statistics calculation
- [x] Write `test_get_highly_cited()` - verify top papers identification
- [x] Write `test_save_index_atomic()` - verify atomic write
- [x] Write `test_empty_collection()` - verify empty input handling
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 9: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with new command documentation

---

## Completion Checklist

- [x] All tests pass
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Command is functional via `/paper-researcher:paper-citations`
- [x] Can fetch citations for single paper
- [x] Can fetch citations for all papers
- [x] Citation graph is built correctly
- [x] Highly-cited papers identified
- [x] Handle API failures gracefully
- [x] Rate limiting is respected

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Original plan closely followed; no major deviations from design
- Added explicit type annotations to test files to satisfy mypy strict mode (not anticipated in plan)
- The `import-not-found` mypy errors for scripts imported from non-package directories are expected and ignored per project conventions

**Lessons Learned:**
1. **API Integration**: Semantic Scholar API provides rich citation data via arXiv ID lookup, making it ideal for this use case since arXiv itself doesn't provide citation data
2. **Pattern Consistency**: Following established patterns from F1-F4 (fetch_arxiv.py, build_digest.py) significantly accelerated implementation
3. **Atomic Writes**: The tempfile + os.replace() pattern used in other scripts works well for index files
4. **Type Annotations**: mypy requires explicit `dict[str, Any]` annotations for dictionary literals in test files to satisfy strict mode

**Improvement Suggestions:**
1. **Extract Shared Utilities**: `validate_arxiv_id()` and `load_index()` are duplicated across 5+ scripts; consider creating `skills/common/validators.py`
2. **API Key Support**: Add optional S2_API_KEY environment variable for higher rate limits
3. **Test Coverage**: The `main()` function in fetch_citations.py has lower coverage (63%); add integration tests for CLI workflows
4. **Structured Logging**: Consider adding extra fields (paper_id, operation, duration) to log entries for better observability

---

## Notes

- Follow existing patterns from F1-F4 for consistency
- Reuse `validate_arxiv_id()` pattern from other scripts
- Ensure atomic file writing for index updates
- Semantic Scholar API: 100 requests per 5 minutes (unauthenticated)
- Use 3-second delay between requests to stay within limits
