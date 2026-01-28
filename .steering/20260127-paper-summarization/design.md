# Design: Paper Summarization Feature

**Feature:** F2: Paper Summarization
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Architecture Overview

### Component Diagram

```
User → /paper-researcher:paper-summarize <paper-id>
   ↓
commands/paper-summarize.md
   ↓
skills/paper-summarizer/SKILL.md
   ↓
1. Read metadata.json → Get paper details
2. Generate summary using Claude → Structured prompt
3. Write summary.md → Store in paper directory
4. Run update_summary_status.py → Update metadata and index
```

### Directory Structure

```
paper-researcher/
├── commands/
│   └── paper-summarize.md         # NEW: Summarization command
├── skills/
│   └── paper-summarizer/          # NEW: Summarization skill
│       ├── SKILL.md
│       └── scripts/
│           └── update_summary_status.py  # NEW: Update has_summary
├── agents/
│   └── paper-summarizer.md        # NEW: Batch summarization agent
├── data/
│   └── papers/
│       └── {arxiv_id}/
│           ├── metadata.json      # MODIFIED: has_summary → true
│           └── summary.md         # NEW: Generated summary
└── tests/
    └── test_update_summary_status.py  # NEW: Unit tests
```

---

## Component Specifications

### 1. Command (`commands/paper-summarize.md`)

**Purpose:** Entry point for paper summarization via slash command.

**YAML Frontmatter:**
```yaml
---
name: paper-summarize
description: "Generate or regenerate summary for a specific paper."
allowed-tools: Read, Write, Bash, Task, Skill
---
```

**Arguments:**
- `<paper-id>` (required): arXiv ID to summarize

**Behavior:**
- Validate paper ID format
- Check if paper exists in collection
- Invoke `paper-summarizer` skill
- Display generated summary to user

### 2. Skill (`skills/paper-summarizer/SKILL.md`)

**Purpose:** Orchestrate paper summarization workflow.

**Workflow:**
1. Read paper metadata from `data/papers/{id}/metadata.json`
2. Extract abstract from metadata
3. Generate summary using Claude with structured prompt
4. Write summary to `data/papers/{id}/summary.md`
5. Run `update_summary_status.py` to update metadata and index
6. Return summary to user

### 3. Script: `update_summary_status.py`

**Purpose:** Update `has_summary` field in metadata and index after summarization.

**CLI Interface:**
```bash
python update_summary_status.py --paper-id 2401.12345 --data-dir ./data
```

**Implementation Details:**

**Main Functions:**

1. `update_metadata(paper_id: str, data_dir: Path) -> bool`
   - Load `data/papers/{id}/metadata.json`
   - Set `has_summary: true`
   - Write back atomically
   - Return success status

2. `update_index(paper_id: str, data_dir: Path) -> bool`
   - Load `data/index/papers.json`
   - Set paper's `has_summary: true`
   - Write back atomically
   - Return success status

3. `main()`
   - Parse CLI arguments
   - Validate paper ID
   - Call update functions
   - Report success/failure

**Output Format:**
```json
{
  "success": true,
  "paper_id": "2401.12345",
  "message": "Updated summary status"
}
```

### 4. Agent (`agents/paper-summarizer.md`)

**Purpose:** Batch summarization of multiple papers.

**Responsibilities:**
- Accept list of paper IDs or "all unsummarized"
- For each paper, invoke summarization workflow
- Report progress and results
- Handle errors gracefully, continue on failure

---

## Summary Generation

### Claude Prompt Template

```
Summarize this academic paper in the following structured format:

# [Paper Title]

**Authors:** [Author list from metadata]
**arXiv:** [ID] | **Published:** [Date]

## Problem
[1-2 sentences describing what problem this paper addresses]

## Method
[2-3 sentences describing the approach taken]

## Results
[Key findings and metrics]

## Takeaways
[3-5 actionable bullet points for practitioners]

---

Paper Title: {title}
Authors: {authors}
Abstract:
{abstract}
```

### Summary Output Format

File: `data/papers/{arxiv_id}/summary.md`

```markdown
# Agent Framework for LLM Applications

**Authors:** John Smith, Jane Doe
**arXiv:** 2401.12345 | **Published:** 2024-01-15

## Problem
Current LLM applications struggle with complex multi-step tasks that require planning and tool use. This paper addresses the challenge of building reliable agent systems.

## Method
The authors propose a hierarchical agent framework that separates planning, execution, and reflection phases. The system uses a tree-structured approach to explore multiple solution paths.

## Results
The framework achieves 45% improvement over baseline on the ALFWorld benchmark. Human evaluation shows 3.2x higher task completion rate compared to single-step prompting.

## Takeaways
- Hierarchical decomposition improves complex task handling
- Reflection phases are critical for error recovery
- The framework is model-agnostic and works with various LLMs
```

---

## Data Model Updates

### metadata.json (Modified)

After summarization:
```json
{
  "id": "2401.12345",
  "title": "Paper Title",
  "authors": ["Author 1"],
  "abstract": "...",
  "published": "2024-01-15",
  "collected_at": "2026-01-27T10:00:00",
  "topics": ["LLM agents"],
  "has_summary": true,           // CHANGED: false → true
  "summary_generated_at": "2026-01-27T11:00:00"  // NEW: timestamp
}
```

### papers.json Index (Modified)

```json
{
  "version": "1.0",
  "updated_at": "2026-01-27T11:00:00",
  "papers": {
    "2401.12345": {
      "title": "Paper Title",
      "authors": ["Author 1"],
      "topics": ["LLM agents"],
      "collected_at": "2026-01-27T10:00:00",
      "has_summary": true          // CHANGED: false → true
    }
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "PAPER_NOT_FOUND",
    "message": "Paper 2401.12345 not found in collection",
    "details": "Run /paper-collect to add papers first"
  }
}
```

### Error Scenarios

| Scenario | Handling |
|----------|----------|
| Paper not in collection | Return error with suggestion to collect first |
| Missing abstract | Skip summarization, report warning |
| Summary already exists | Offer to regenerate or skip |
| File write failure | Report error, metadata unchanged |
| Index update failure | Log error, continue (summary still valid) |

---

## Integration with Paper Collector

### Modified paper-collector Workflow

After storing papers:

```
Step 4: Generate Summaries (NEW)
   For each newly collected paper:
   1. Invoke paper-summarizer skill
   2. Generate and save summary
   3. Update has_summary status
   4. Continue to next paper

Step 5: Report Results (Updated)
   Include summary count in report:
   "Collected 12 new papers, 12 summaries generated"
```

---

## Testing Strategy

### Unit Tests

1. **test_update_summary_status.py:**
   - `test_update_metadata()` - Verify metadata update
   - `test_update_index()` - Verify index update
   - `test_paper_not_found()` - Handle missing paper
   - `test_atomic_write()` - Verify no corruption on failure

### Test Fixtures

- `tests/fixtures/sample_metadata.json` - Paper metadata for testing
- `tests/fixtures/sample_summary.md` - Expected summary format

### Mocking

- Use `tmp_path` fixture for file operations
- No Claude API mocking needed (skill handles Claude interaction)

---

## Implementation Sequence

1. **Phase 1: Script Development**
   - Create `update_summary_status.py`
   - Implement update_metadata function
   - Implement update_index function
   - Add CLI argument parsing
   - Add error handling

2. **Phase 2: Plugin Integration**
   - Create `commands/paper-summarize.md`
   - Create `skills/paper-summarizer/SKILL.md`
   - Create `agents/paper-summarizer.md`

3. **Phase 3: Testing**
   - Write unit tests for update_summary_status.py
   - Create test fixtures
   - Verify end-to-end workflow

4. **Phase 4: Integration**
   - Modify paper-collector skill to call summarizer
   - Test batch summarization
   - Update documentation
