# Repository Structure: Paper Researcher Plugin

**Version:** 1.0
**Date:** 2026-01-27

---

## 1. Overview

This document defines the file and directory structure for the Paper Researcher Claude Code plugin.

---

## 2. Directory Structure

```
paper-researcher/
├── .claude-plugin/                 # Plugin metadata (required)
│   └── plugin.json                 # Plugin configuration
│
├── agents/                         # Agent definitions
│   ├── arxiv-fetcher.md            # arXiv API integration agent
│   ├── paper-summarizer.md         # Summary generation agent
│   └── paper-searcher.md           # Search functionality agent
│
├── commands/                       # Slash command definitions
│   ├── paper-collect.md            # /paper-researcher:paper-collect
│   ├── paper-search.md             # /paper-researcher:paper-search
│   ├── paper-summarize.md          # /paper-researcher:paper-summarize
│   └── paper-digest.md             # /paper-researcher:paper-digest
│
├── skills/                         # Skills with bundled scripts
│   ├── paper-collector/            # Paper collection skill
│   │   ├── SKILL.md                # Skill instructions
│   │   └── scripts/                # Python scripts
│   │       ├── fetch_arxiv.py      # Query arXiv API
│   │       └── store_paper.py      # Store paper metadata
│   │
│   ├── paper-summarizer/           # Summary generation skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── parse_pdf.py        # Extract text from PDF
│   │
│   ├── paper-searcher/             # Paper search skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── search_index.py     # Build/query search index
│   │
│   └── paper-digest/               # Digest generation skill
│       ├── SKILL.md
│       └── scripts/
│           └── build_digest.py     # Generate paper digests
│
├── data/                           # Runtime data (gitignored)
│   ├── papers/                     # Individual paper directories
│   │   └── {arxiv_id}/             # e.g., 2401.12345/
│   │       ├── metadata.json       # Paper metadata
│   │       ├── summary.md          # Generated summary
│   │       └── paper.pdf           # Original PDF (optional)
│   │
│   ├── index/                      # Search indexes
│   │   ├── papers.json             # Global paper index
│   │   └── topics.json             # Topic → paper mappings
│   │
│   └── digests/                    # Generated digests
│       └── {YYYY-MM-DD}.md         # e.g., 2026-01-27.md
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # pytest fixtures
│   ├── fixtures/                   # Test data
│   │   ├── arxiv_response.xml      # Mock API response
│   │   └── sample_paper/           # Sample paper directory
│   ├── test_fetch_arxiv.py
│   ├── test_store_paper.py
│   ├── test_parse_pdf.py
│   └── test_search_index.py
│
├── docs/                           # Documentation (if separate from project docs)
│   └── ...
│
├── .gitignore                      # Git ignore rules
├── pyproject.toml                  # Python project configuration
├── README.md                       # Plugin documentation
└── CLAUDE.md                       # Plugin-level instructions (optional)
```

---

## 3. Directory Roles

### 3.1 Plugin Structure (Required)

| Directory | Role | Required |
|-----------|------|----------|
| `.claude-plugin/` | Plugin metadata and configuration | Yes |
| `agents/` | Agent definitions for autonomous tasks | No |
| `commands/` | Slash command entry points | Yes |
| `skills/` | Skill packages with scripts | Yes |

### 3.2 Runtime Directories

| Directory | Role | Git Status |
|-----------|------|------------|
| `data/` | Runtime storage for papers, indexes, digests | Ignored |
| `data/papers/` | Individual paper directories | Ignored |
| `data/index/` | Search indexes | Ignored |
| `data/digests/` | Generated digest files | Ignored |

### 3.3 Development Directories

| Directory | Role | Git Status |
|-----------|------|------------|
| `tests/` | Test suite | Tracked |
| `tests/fixtures/` | Test data and mocks | Tracked |
| `docs/` | Documentation | Tracked |

---

## 4. File Placement Rules

### 4.1 Plugin Files

| File Type | Location | Naming Convention |
|-----------|----------|-------------------|
| Plugin metadata | `.claude-plugin/plugin.json` | Fixed name |
| Command definitions | `commands/{command-name}.md` | Lowercase, hyphenated |
| Agent definitions | `agents/{agent-name}.md` | Lowercase, hyphenated |
| Skill instructions | `skills/{skill-name}/SKILL.md` | SKILL.md (uppercase) |
| Skill scripts | `skills/{skill-name}/scripts/*.py` | Lowercase, underscored |

### 4.2 Data Files

| File Type | Location | Naming Convention |
|-----------|----------|-------------------|
| Paper metadata | `data/papers/{arxiv_id}/metadata.json` | Fixed name |
| Paper summary | `data/papers/{arxiv_id}/summary.md` | Fixed name |
| Paper PDF | `data/papers/{arxiv_id}/paper.pdf` | Fixed name |
| Paper index | `data/index/papers.json` | Fixed name |
| Topic index | `data/index/topics.json` | Fixed name |
| Digest | `data/digests/{YYYY-MM-DD}.md` | ISO date format |

### 4.3 Test Files

| File Type | Location | Naming Convention |
|-----------|----------|-------------------|
| Test modules | `tests/test_*.py` | `test_` prefix |
| Fixtures | `tests/fixtures/` | Descriptive names |
| Conftest | `tests/conftest.py` | Fixed name |

---

## 5. Key Files

### 5.1 plugin.json

```json
{
    "name": "paper-researcher",
    "description": "AI-powered research paper collection, summarization, and search pipeline.",
    "version": "1.0.0",
    "author": {
        "name": "your-name"
    }
}
```

### 5.2 pyproject.toml

```toml
[project]
name = "paper-researcher"
version = "1.0.0"
description = "AI-powered research paper pipeline"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.28.0",
    "feedparser>=6.0.0",
    "pypdf>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "responses>=0.23.0",
]

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 5.3 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/

# Virtual environments
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp

# Plugin runtime data (DO NOT COMMIT)
data/

# Test artifacts
.pytest_cache/
.coverage
htmlcov/

# OS files
.DS_Store
Thumbs.db
```

---

## 6. Conventions

### 6.1 Naming Conventions

| Entity | Convention | Example |
|--------|------------|---------|
| Directories | lowercase, hyphenated | `paper-collector/` |
| Python files | lowercase, underscored | `fetch_arxiv.py` |
| JSON files | lowercase, underscored | `papers.json` |
| Markdown files | lowercase, hyphenated | `paper-collect.md` |
| Python functions | lowercase, underscored | `fetch_papers()` |
| Python classes | PascalCase | `ArxivClient` |
| Constants | UPPERCASE, underscored | `MAX_RESULTS` |

### 6.2 Import Structure

```python
# Standard library
import json
import time
from pathlib import Path

# Third-party
import feedparser
import requests

# Local
from .utils import validate_arxiv_id
```

---

## 7. Example File Structures

### 7.1 Example Paper Directory

```
data/papers/2401.12345/
├── metadata.json
│   {
│     "id": "2401.12345",
│     "title": "Agent Framework for LLM Applications",
│     "authors": ["John Smith", "Jane Doe"],
│     "abstract": "We present...",
│     "published": "2024-01-15",
│     "categories": ["cs.CL", "cs.AI"],
│     "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
│     "collected_at": "2026-01-27T10:00:00Z",
│     "topics": ["LLM agents"],
│     "has_summary": true
│   }
│
├── summary.md
│   # Agent Framework for LLM Applications
│
│   **Authors:** John Smith, Jane Doe
│   **arXiv:** 2401.12345 | **Published:** 2024-01-15
│
│   ## Problem
│   ...
│
│   ## Method
│   ...
│
│   ## Results
│   ...
│
│   ## Takeaways
│   - ...
│
└── paper.pdf (optional)
```

### 7.2 Example Digest

```
data/digests/2026-01-27.md

# Paper Digest: 2026-01-27

**Papers collected:** 12
**Topics:** LLM agents, transformers

---

## LLM Agents (8 papers)

### Agent Framework for LLM Applications
**[2401.12345]** | Smith, Doe | 2024-01-15

> We present a framework for building LLM-based agents...

---

## Transformers (4 papers)

...
```

---

## 8. Migration Guidelines

### 8.1 Adding New Paper Sources

1. Create new skill directory: `skills/{source-name}/`
2. Add `SKILL.md` with workflow instructions
3. Add scripts in `skills/{source-name}/scripts/`
4. Optionally create agent in `agents/{source-name}.md`
5. Update command to support new source

### 8.2 Adding New Export Formats

1. Create export skill: `skills/export-{format}/`
2. Add export script
3. Create command if needed
