# Task List: Collaboration Feature

**Feature:** F8: Collaboration
**Priority:** P2 (Future)
**Date:** 2026-01-27
**Status:** Completed

---

## Implementation Tasks

### Phase 1: Directory Setup

- [x] ~~Create separate skill directories~~ (Consolidated into single `skills/paper-collaborator/` directory)
- [x] Create `skills/paper-collaborator/` directory
- [x] Create `skills/paper-collaborator/scripts/` directory

### Phase 2: Core Script - share_collection.py

- [x] Create `skills/paper-collaborator/scripts/share_collection.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `sanitize_username(username: str) -> str` function
- [x] Implement `load_index(data_dir: Path) -> dict` function
- [x] Implement `load_paper_metadata(paper_id: str, data_dir: Path) -> dict | None` function
- [x] Implement `create_manifest(paper_ids, username, options) -> dict` function
- [x] Implement `build_package(data_dir, output_path, options) -> tuple[int, list]` function
- [x] Implement CLI argument parsing (--output, --include-summaries, --include-annotations, --username, --data-dir, --paper-id)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing papers
- [x] Add error handling for file I/O failures

### Phase 3: Core Script - import_collection.py

- [x] Create `skills/paper-collaborator/scripts/import_collection.py`
- [x] Implement `validate_manifest(manifest: dict) -> bool` function
- [x] Implement `validate_paths(zip_file: ZipFile) -> bool` function (security)
- [x] Implement ZIP bomb protection (MAX_TOTAL_SIZE, MAX_FILE_COUNT, MAX_COMPRESSION_RATIO)
- [x] Implement `merge_papers(package_dir, data_dir, overwrite) -> tuple[int, int]` function
- [x] Implement `merge_index(package_dir, data_dir) -> None` function
- [x] Implement `merge_annotations(package_dir, data_dir) -> int` function
- [x] Implement CLI argument parsing (--input, --data-dir, --overwrite)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for invalid package
- [x] Add error handling for path traversal attempts

### Phase 4: Core Script - save_annotation.py

- [x] Create `skills/paper-collaborator/scripts/save_annotation.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `sanitize_username(username: str) -> str` function
- [x] Implement `load_metadata(paper_id: str, data_dir: Path) -> dict | None` function
- [x] Implement `update_metadata(paper_id, data_dir, annotation_count) -> bool` function
- [x] Implement `count_annotations(paper_id, data_dir) -> int` function
- [x] Implement `save_annotation(paper_id, content, annotation_type, username, data_dir) -> dict` function
- [x] Implement CLI argument parsing (--paper-id, --content, --type, --username, --data-dir)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing paper
- [x] Add error handling for file I/O failures

### Phase 5: Core Script - list_annotations.py

- [x] Create `skills/paper-collaborator/scripts/list_annotations.py`
- [x] Implement `validate_arxiv_id(paper_id: str) -> bool` function
- [x] Implement `load_annotations(paper_id: str, data_dir: Path) -> list[dict]` function
- [x] Implement `format_annotations(annotations, output_format) -> str` function
- [x] Support multiple output formats (json, markdown, text)
- [x] Implement CLI argument parsing (--paper-id, --data-dir, --format)
- [x] Implement `main()` function to orchestrate workflow
- [x] Add logging configuration
- [x] Add error handling for missing paper

### Phase 6: Plugin Integration - Commands

- [x] Create `commands/paper-share.md` with YAML frontmatter
- [x] Create `commands/paper-import.md` with YAML frontmatter
- [x] Create `commands/paper-annotate.md` with YAML frontmatter
- [x] Document command arguments for each
- [x] Add usage examples for each
- [x] Add error handling guidance for each

### Phase 7: Plugin Integration - Skills

- [x] ~~Create separate SKILL.md files~~ (Consolidated into single `skills/paper-collaborator/SKILL.md`)
- [x] Create `skills/paper-collaborator/SKILL.md` with 4 operations (share, import, annotate, list)
- [x] Add skill metadata and workflows
- [x] Add instructions for calling scripts
- [x] Add output format specifications

### Phase 8: Testing Infrastructure

- [x] Create `tests/test_share_collection.py`
- [x] Create `tests/test_import_collection.py`
- [x] Create `tests/test_save_annotation.py`
- [x] Create `tests/test_list_annotations.py`

### Phase 9: Unit Tests - share_collection

- [x] Write `TestValidateArxivId` class - verify arXiv ID validation
- [x] Write `TestSanitizeUsername` class - verify username sanitization
- [x] Write `TestLoadIndex` class - verify index loading
- [x] Write `TestLoadPaperMetadata` class - verify metadata loading
- [x] Write `TestCreateManifest` class - verify manifest creation
- [x] Write `TestBuildPackage` class - verify ZIP creation with papers, summaries, annotations
- [x] Write `TestMainFunction` class - verify CLI argument parsing

### Phase 10: Unit Tests - import_collection

- [x] Write `TestValidateManifest` class - verify manifest validation
- [x] Write `TestValidatePaths` class - verify path traversal prevention
- [x] Write `TestMergePapers` class - verify paper merging with overwrite options
- [x] Write `TestMergeIndex` class - verify index merging
- [x] Write `TestMergeAnnotations` class - verify annotation merging
- [x] Write `TestImportPackage` class - verify full package import
- [x] Write `TestMainFunction` class - verify CLI argument parsing
- [x] Write ZIP bomb protection tests

### Phase 11: Unit Tests - annotation scripts

- [x] Write `TestValidateArxivId` class - verify arXiv ID validation
- [x] Write `TestSanitizeUsername` class - verify username sanitization
- [x] Write `TestLoadMetadata` class - verify metadata loading
- [x] Write `TestSaveAnnotation` class - verify annotation save with types
- [x] Write `TestCountAnnotations` class - verify annotation counting
- [x] Write `TestLoadAnnotations` class - verify annotation loading
- [x] Write `TestFormatAnnotations` class - verify formatting (json, markdown, text)
- [x] Write `TestMainFunction` classes - verify CLI argument parsing for both scripts

### Phase 12: Validation and Documentation

- [x] Run all tests with `uv run pytest` - 344 tests pass
- [x] Run linting with `uv run ruff check .` - All checks passed
- [x] Run type checking with `uv run mypy .` - Success for new scripts
- [x] Fix linting issues (B904, E501, import sorting)
- [x] Update README.md with new command documentation

---

## Completion Checklist

- [x] All tests pass (344 tests)
- [x] Linting passes (ruff)
- [x] Type checking passes (mypy)
- [x] README.md is updated
- [x] Commands functional via slash commands
- [x] Can share collection as ZIP
- [x] Can import shared collection
- [x] Can add annotations to papers
- [x] Can view annotations
- [x] Path traversal attacks prevented
- [x] ZIP bomb protection implemented
- [x] Duplicate papers handled correctly

---

## Retrospective

**Completion Date:** 2026-01-27

### What Went Well

1. **Consolidated Architecture**: Instead of creating 3 separate skills (paper-sharer, paper-importer, paper-annotator), consolidated into a single `paper-collaborator` skill with 4 operations. This reduces maintenance overhead and follows a more cohesive design.

2. **Comprehensive Security**: Implemented robust security measures:
   - Path traversal prevention in both share and import operations
   - ZIP bomb protection with size limits, file count limits, and compression ratio checks
   - Username sanitization to prevent injection attacks
   - arXiv ID validation using strict regex patterns

3. **Test Coverage**: Created 90+ new tests covering all functionality, edge cases, and security scenarios.

4. **Code Review Integration**: The code-reviewer sub-agent identified important security improvements (ZIP bomb protection, consistent sanitize_username) that were incorporated before final validation.

### Differences from Original Plan

1. **Skill Organization**: Original plan called for 3 separate skill directories. Implementation uses 1 consolidated skill (`paper-collaborator`) with 4 scripts, which is more maintainable.

2. **Additional Security**: Added ZIP bomb protection (MAX_TOTAL_SIZE, MAX_FILE_COUNT, MAX_COMPRESSION_RATIO) not in original plan.

3. **Annotation Types**: Added `annotation_type` field (note, highlight, question, comment) to provide more flexibility.

4. **Output Formats**: Added multiple output formats for list_annotations (json, markdown, text).

### Lessons Learned

1. **Consolidation Over Fragmentation**: Grouping related functionality into a single skill with multiple operations is cleaner than many small skills.

2. **Security First**: Security validations (path traversal, ZIP bombs) should be considered early in design, not added as afterthoughts.

3. **Test Fixture Patterns**: The `temp_data_dir` fixture pattern from existing tests made writing new tests straightforward and consistent.

4. **Code Review Value**: Automated code review caught issues that manual review might have missed.

### Technical Debt / Future Improvements

1. Consider adding rate limiting for annotation operations
2. Could add annotation search/filter capabilities
3. May want to add annotation export as separate files in shared packages

---

## Notes

- Followed existing patterns from F1-F7 for consistency
- Reused `validate_arxiv_id()` pattern from other scripts
- Used atomic file writing with tempfile + os.replace()
- Used zipfile module for package creation/extraction
- Sanitized all user inputs (especially usernames and paths)
