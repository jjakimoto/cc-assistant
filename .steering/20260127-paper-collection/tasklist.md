# Task List: Paper Collection Feature

**Feature:** F1: Paper Collection
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Implementation Tasks

### Phase 1: Project Setup

- [x] Create plugin root directory `paper-researcher/`
- [x] Create `.claude-plugin/` directory
- [x] Create `.claude-plugin/plugin.json` with metadata
- [x] Create `pyproject.toml` with dependencies
- [x] Create `.gitignore` file
- [x] Create `README.md` with basic documentation
- [x] Initialize uv environment (`uv venv` and `uv sync`)

### Phase 2: Directory Structure

- [x] Create `commands/` directory
- [x] Create `skills/` directory
- [x] Create `skills/paper-collector/` directory
- [x] Create `skills/paper-collector/scripts/` directory
- [x] Create `tests/` directory
- [x] Create `tests/fixtures/` directory
- [x] Create `data/` directory (runtime, gitignored)
- [x] Create `data/papers/` directory
- [x] Create `data/index/` directory

### Phase 3: Core Script - fetch_arxiv.py

- [x] Create `skills/paper-collector/scripts/fetch_arxiv.py`
- [x] Implement `build_query(topic: str, days: int) -> str` function
- [x] Implement `fetch_with_retry(query: str, max_results: int)` function with exponential backoff
- [x] Implement `parse_response(xml_text: str) -> list[dict]` function using feedparser
- [x] Implement CLI argument parsing (--query, --days, --max, --output)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for network failures
- [x] Add error handling for invalid responses

### Phase 4: Core Script - store_paper.py

- [x] Create `skills/paper-collector/scripts/store_paper.py`
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `save_paper(paper: dict, data_dir: Path) -> bool` function
- [x] Implement duplicate detection logic
- [x] Implement `update_index(index: dict, papers: list[dict], data_dir: Path)` function
- [x] Implement atomic index writing
- [x] Implement CLI argument parsing (--input, --data-dir)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for file I/O failures

### Phase 5: Plugin Integration - Command

- [x] Create `commands/paper-collect.md` with YAML frontmatter
- [x] Document command arguments (--topic, --days, --max)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-collector skill)

### Phase 6: Plugin Integration - Skill

- [x] Create `skills/paper-collector/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (fetch → store → report)
- [x] Add instructions for calling scripts via Bash tool
- [x] Add error handling guidance
- [x] Add output format specification

### Phase 7: Testing Infrastructure

- [x] Create `tests/__init__.py`
- [x] Create `tests/conftest.py` with pytest fixtures
- [x] Create sample arXiv response XML in `tests/fixtures/arxiv_response.xml`
- [x] Set up pytest configuration

### Phase 8: Unit Tests - fetch_arxiv

- [x] Create `tests/test_fetch_arxiv.py`
- [x] Write `test_build_query()` - verify query construction
- [x] Write `test_parse_response()` - verify XML parsing
- [x] Write `test_retry_logic()` - verify exponential backoff
- [x] Write `test_error_handling()` - verify network failure handling
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 9: Unit Tests - store_paper

- [x] Create `tests/test_store_paper.py`
- [x] Write `test_save_paper()` - verify file creation
- [x] Write `test_duplicate_detection()` - verify skip duplicates
- [x] Write `test_load_index()` - verify index loading
- [x] Write `test_update_index()` - verify index atomicity
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 10: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with installation instructions
- [x] Update README.md with usage examples
- [x] Add troubleshooting section to README.md

---

## Completion Checklist

- [x] All tests pass
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is complete
- [x] Command is functional via `/paper-researcher:paper-collect`
- [x] Can fetch papers from arXiv successfully
- [x] Can store papers to local filesystem
- [x] Can handle API failures gracefully
- [x] Duplicate detection works correctly

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Added arXiv ID validation (`validate_arxiv_id` function) to prevent path traversal attacks - this was identified during code review and not in original plan
- Added positive integer validation for `--days` and `--max` CLI arguments - security enhancement identified during validation
- Changed arXiv API URL from HTTP to HTTPS for secure communication
- Updated `pyproject.toml` to use `[dependency-groups]` instead of deprecated `[tool.uv]` format

**Lessons Learned:**
- Code review sub-agents are valuable for identifying security issues (path traversal, input validation) that may be missed during initial implementation
- Type checking with mypy requires explicit handling for untyped libraries (feedparser) - using `# type: ignore[import-untyped]`
- The atomic file write pattern using `tempfile.NamedTemporaryFile` + `replace()` is important for index integrity
- Test fixtures should match actual expected behavior (arXiv IDs are 4 digits + 4-5 digits, not 6)

**Improvement Suggestions:**
- Consider adding integration tests that actually call the arXiv API (with VCR/cassettes for reproducibility)
- Add test coverage for error handling paths in `main()` functions
- Consider restructuring scripts as a proper Python package to eliminate `sys.path.insert()` workarounds in tests
- Add parametrized tests for boundary conditions (days=1, max=1, empty topics)
