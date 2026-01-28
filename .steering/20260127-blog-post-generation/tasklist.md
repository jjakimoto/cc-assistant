# Task List: Blog Post Generation Feature

**Feature:** F6: Blog Post Generation
**Priority:** P1
**Date:** 2026-01-27
**Status:** Completed

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] Create `skills/paper-blogger/` directory
- [x] Create `skills/paper-blogger/scripts/` directory
- [x] Create `data/blog-posts/` directory (if not exists, gitignored)

### Phase 2: Core Script - save_blog_post.py

- [x] Create `skills/paper-blogger/scripts/save_blog_post.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `load_metadata(paper_id: str, data_dir: Path) -> dict | None` function
- [x] Implement `update_metadata(paper_id: str, data_dir: Path) -> bool` function
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `update_index(paper_id: str, data_dir: Path) -> bool` function
- [x] Implement `save_blog_post(paper_id: str, content: str, data_dir: Path) -> bool` function
- [x] Implement CLI argument parsing (--paper-id, --content, --data-dir)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing paper
- [x] Add error handling for file I/O failures

### Phase 3: Plugin Integration - Command

- [x] Create `commands/paper-blog.md` with YAML frontmatter
- [x] Document command arguments (<paper-id>)
- [x] Add command description and usage examples
- [x] Add workflow instructions (invoke paper-blogger skill)
- [x] Add error handling guidance
- [x] Add related commands section

### Phase 4: Plugin Integration - Skill

- [x] Create `skills/paper-blogger/SKILL.md`
- [x] Add skill metadata (name, description)
- [x] Document skill workflow (read → transform → save)
- [x] Add Claude prompt template for blog generation
- [x] Add instructions for reading paper metadata and summary
- [x] Add instructions for writing blog post
- [x] Add instructions for calling save_blog_post.py
- [x] Add output format specification
- [x] Add error handling guidance

### Phase 5: Testing Infrastructure

- [x] Create `tests/test_save_blog_post.py`

### Phase 6: Unit Tests - save_blog_post

- [x] Write `test_validate_arxiv_id()` - verify ID validation
- [x] Write `test_load_metadata()` - verify metadata loading
- [x] Write `test_update_metadata()` - verify metadata update
- [x] Write `test_update_index()` - verify index update
- [x] Write `test_save_blog_post()` - verify blog post file creation
- [x] Write `test_paper_not_found()` - handle missing paper
- [x] Write `test_invalid_paper_id()` - handle invalid ID format
- [x] Write `test_cli_arguments()` - verify argument parsing

### Phase 7: Validation and Documentation

- [x] Run all tests with `uv run pytest`
- [x] Run linting with `uv run ruff check .`
- [x] Run type checking with `uv run mypy .`
- [x] Fix any issues found
- [x] Update README.md with new command documentation

---

## Completion Checklist

- [x] All tests pass (208 tests total, 28 new for this feature)
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Command is functional via `/paper-researcher:paper-blog`
- [x] Can generate blog post for paper with summary
- [x] Blog post saved to correct location
- [x] metadata.json updated with has_blog_post: true
- [x] index updated with has_blog_post: true
- [x] Handles missing paper gracefully
- [x] Handles missing summary gracefully

---

## Post-Implementation Retrospective

**Implementation Completion Date:** 2026-01-27

**Differences from Plan:**
- Added `--content-file` option in addition to `--content` for flexibility when passing large blog content via file instead of command line argument
- Added minimum content length validation (100 characters) to prevent empty or trivial blog posts from being saved
- The code review identified duplicated atomic write patterns across functions - acknowledged as future refactoring opportunity

**Lessons Learned:**
1. **Pattern Consistency**: Following established patterns from F1-F5 significantly accelerated implementation - the atomic write pattern, validation functions, and error handling format were all reused
2. **Code Review Value**: The code-reviewer sub-agent identified code duplication (atomic write pattern) and missing test coverage (content file not found) that can be addressed in future iterations
3. **Test-First Benefits**: Writing comprehensive tests upfront caught the unused import issue early during the lint phase
4. **Skill Design**: The skill workflow (read metadata → read summary → generate content → save → update status) mirrors F2 (summarization) closely, making it intuitive for users

**Improvement Suggestions:**
1. **Extract Shared Utilities**: Consider creating `skills/common/utils.py` with shared functions like `validate_arxiv_id()`, `load_index()`, and `atomic_write()` to reduce duplication across 6+ scripts
2. **UTC Timestamps**: Future features should use `datetime.now(timezone.utc).isoformat()` for consistency across time zones
3. **Maximum Content Length**: Add maximum content length validation to prevent memory/disk issues with extremely large blog posts
4. **Integration Tests**: Add end-to-end integration tests that test the full skill workflow from paper collection through blog generation

---

## Notes

- Follow existing patterns from F1-F5 for consistency
- Reuse `validate_arxiv_id()` pattern from other scripts
- Ensure atomic file writing for all updates
