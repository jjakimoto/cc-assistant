# Design: Paper Collection Feature

**Feature:** F1: Paper Collection
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Architecture Overview

### Component Diagram

```
User → /paper-researcher:paper-collect
   ↓
commands/paper-collect.md
   ↓
skills/paper-collector/SKILL.md
   ↓
scripts/fetch_arxiv.py ←→ arXiv API
   ↓
scripts/store_paper.py ←→ data/papers/
```

### Directory Structure

```
paper-researcher/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── paper-collect.md
├── skills/
│   └── paper-collector/
│       ├── SKILL.md
│       └── scripts/
│           ├── fetch_arxiv.py
│           └── store_paper.py
├── data/                    # gitignored
│   ├── papers/
│   │   └── {arxiv_id}/
│   │       └── metadata.json
│   └── index/
│       └── papers.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   └── arxiv_response.xml
│   ├── test_fetch_arxiv.py
│   └── test_store_paper.py
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Component Specifications

### 1. Plugin Metadata (`.claude-plugin/plugin.json`)

```json
{
    "name": "paper-researcher",
    "description": "AI-powered research paper collection, summarization, and search pipeline.",
    "version": "1.0.0",
    "author": {
        "name": "Paper Researcher Team"
    }
}
```

### 2. Command (`commands/paper-collect.md`)

**Purpose:** Entry point for paper collection via slash command.

**YAML Frontmatter:**
```yaml
---
name: paper-collect
description: "Fetch new papers from arXiv based on topics/keywords and store locally."
allowed-tools: Read, Write, Edit, Bash, Task, Skill
---
```

**Behavior:**
- Parse arguments: `--topic`, `--days`, `--max`
- Validate inputs
- Invoke `paper-collector` skill
- Display results to user

### 3. Skill (`skills/paper-collector/SKILL.md`)

**Purpose:** Orchestrate paper collection workflow.

**Workflow:**
1. Run `fetch_arxiv.py` with query parameters
2. Receive JSON output with paper metadata
3. Run `store_paper.py` to persist papers
4. Report count of new papers collected

### 4. Script: `fetch_arxiv.py`

**Purpose:** Query arXiv API and fetch paper metadata.

**CLI Interface:**
```bash
python fetch_arxiv.py --query "LLM agents" --days 7 --max 50 --output papers.json
```

**Implementation Details:**

**Constants:**
```python
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
MAX_RESULTS = 50
REQUEST_DELAY = 3.0  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
```

**Main Functions:**

1. `build_query(topic: str, days: int) -> str`
   - Construct arXiv search query
   - Add date filtering
   - Example: `cat:cs.CL AND ti:agents`

2. `fetch_with_retry(query: str, max_results: int) -> Response`
   - HTTP GET to arXiv API
   - Exponential backoff retry logic
   - Handle 503 specifically

3. `parse_response(xml_text: str) -> list[dict]`
   - Use feedparser to parse Atom feed
   - Extract: id, title, authors, abstract, published, categories, pdf_url

4. `main()`
   - Parse CLI arguments
   - Call fetch_with_retry
   - Parse response
   - Write JSON output

**Output Format:**
```json
{
  "success": true,
  "count": 12,
  "papers": [
    {
      "id": "2401.12345",
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "abstract": "...",
      "published": "2024-01-15",
      "categories": ["cs.CL", "cs.AI"],
      "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf"
    }
  ]
}
```

### 5. Script: `store_paper.py`

**Purpose:** Store paper metadata to filesystem and update index.

**CLI Interface:**
```bash
python store_paper.py --input papers.json --data-dir ./data
```

**Implementation Details:**

**Main Functions:**

1. `load_index(data_dir: Path) -> dict`
   - Load `data/index/papers.json` if exists
   - Return empty dict if not

2. `save_paper(paper: dict, data_dir: Path) -> bool`
   - Create directory: `data/papers/{arxiv_id}/`
   - Write metadata: `metadata.json`
   - Return True if new, False if duplicate

3. `update_index(index: dict, papers: list[dict], data_dir: Path)`
   - Add new papers to index
   - Write atomically to `data/index/papers.json`

4. `main()`
   - Load papers from input JSON
   - Load existing index
   - For each paper: save metadata
   - Update index
   - Report count of new papers

**Output:**
```
Stored 10 new papers (2 duplicates skipped)
```

---

## Data Model

### Paper Metadata Schema

```json
{
  "id": "2401.12345",
  "title": "Paper Title",
  "authors": ["Author 1", "Author 2"],
  "abstract": "Paper abstract...",
  "published": "2024-01-15",
  "updated": "2024-01-20",
  "categories": ["cs.CL", "cs.AI"],
  "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
  "collected_at": "2026-01-27T10:00:00Z",
  "topics": ["LLM agents"],
  "has_summary": false
}
```

### Index Schema

```json
{
  "version": "1.0",
  "updated_at": "2026-01-27T10:00:00Z",
  "papers": {
    "2401.12345": {
      "title": "Paper Title",
      "authors": ["Author 1"],
      "abstract": "...",
      "topics": ["LLM agents"],
      "collected_at": "2026-01-27T10:00:00Z",
      "has_summary": false
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
    "code": "ARXIV_API_UNAVAILABLE",
    "message": "Failed to fetch papers after 3 retries",
    "details": "503 Service Temporarily Unavailable"
  }
}
```

### Error Scenarios

| Scenario | Handling |
|----------|----------|
| Network timeout | Retry with backoff (3 attempts) |
| 503 Service Unavailable | Retry with backoff |
| Invalid query | Return error to user |
| Duplicate paper | Skip silently, don't count as new |
| Disk write failure | Report error, abort |

---

## Testing Strategy

### Unit Tests

1. **test_fetch_arxiv.py:**
   - `test_build_query()` - Query construction
   - `test_parse_response()` - XML parsing
   - `test_retry_logic()` - Exponential backoff
   - `test_error_handling()` - Network failures

2. **test_store_paper.py:**
   - `test_save_paper()` - File creation
   - `test_duplicate_detection()` - Skip duplicates
   - `test_index_update()` - Index atomicity

### Test Fixtures

- `tests/fixtures/arxiv_response.xml` - Sample arXiv API response

### Mocking

- Use `responses` library to mock HTTP calls to arXiv API
- Mock filesystem operations with `pytest` tmpdir

---

## Configuration

### pyproject.toml

```toml
[project]
name = "paper-researcher"
version = "1.0.0"
requires-python = ">=3.10"

dependencies = [
    "requests>=2.28.0",
    "feedparser>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "responses>=0.23.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "responses>=0.23.0",
]
```

### .gitignore

```
data/
*.pyc
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
dist/
build/
.venv/
```

---

## Implementation Sequence

1. **Phase 1: Project Setup**
   - Create plugin directory structure
   - Create `.claude-plugin/plugin.json`
   - Create `pyproject.toml`
   - Create `.gitignore`
   - Initialize uv environment

2. **Phase 2: Core Scripts**
   - Implement `fetch_arxiv.py`
   - Implement `store_paper.py`
   - Add logging

3. **Phase 3: Plugin Integration**
   - Create `commands/paper-collect.md`
   - Create `skills/paper-collector/SKILL.md`

4. **Phase 4: Testing**
   - Write unit tests
   - Create test fixtures
   - Run tests and verify

5. **Phase 5: Documentation**
   - Write README.md
   - Add usage examples
