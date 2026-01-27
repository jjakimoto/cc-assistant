# Development Guidelines: Paper Researcher Plugin

**Version:** 1.0
**Date:** 2026-01-27

---

## 1. Overview

This document defines coding standards, conventions, and best practices for developing the Paper Researcher Claude Code plugin.

---

## 2. Code Style

### 2.1 Python Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

| Rule | Value |
|------|-------|
| Line length | 88 characters (Black default) |
| Indentation | 4 spaces |
| Quotes | Double quotes for strings |
| Imports | Sorted with isort (ruff handles this) |

### 2.2 Formatting

Use `ruff` for linting and formatting:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### 2.3 Type Hints

Use type hints for all function signatures:

```python
# Good
def fetch_papers(query: str, max_results: int = 50) -> list[dict]:
    ...

# Bad
def fetch_papers(query, max_results=50):
    ...
```

Run mypy for type checking:

```bash
mypy skills/
```

---

## 3. Naming Conventions

### 3.1 Python

| Entity | Convention | Example |
|--------|------------|---------|
| Functions | lowercase_with_underscores | `fetch_papers()` |
| Variables | lowercase_with_underscores | `paper_count` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `MAX_RESULTS` |
| Classes | PascalCase | `ArxivClient` |
| Private | Leading underscore | `_parse_entry()` |

### 3.2 Files and Directories

| Entity | Convention | Example |
|--------|------------|---------|
| Python modules | lowercase_underscores | `fetch_arxiv.py` |
| Directories | lowercase-hyphenated | `paper-collector/` |
| Config files | lowercase | `pyproject.toml` |
| Markdown | lowercase-hyphenated | `paper-collect.md` |

### 3.3 Claude Code Components

| Entity | Convention | Example |
|--------|------------|---------|
| Commands | lowercase-hyphenated | `paper-collect` |
| Skills | lowercase-hyphenated | `paper-collector` |
| Agents | lowercase-hyphenated | `arxiv-fetcher` |

---

## 4. Documentation Standards

### 4.1 Docstrings

Use Google-style docstrings:

```python
def fetch_papers(query: str, max_results: int = 50) -> list[dict]:
    """Fetch papers from arXiv matching the query.

    Args:
        query: Search query string (e.g., "LLM agents")
        max_results: Maximum number of papers to return (default: 50)

    Returns:
        List of paper metadata dictionaries

    Raises:
        ArxivAPIError: If API request fails after retries
    """
    ...
```

### 4.2 Comments

```python
# Good: Explain WHY, not WHAT
# Rate limit: arXiv allows max 1 request per 3 seconds
time.sleep(3.0)

# Bad: Restating the code
# Sleep for 3 seconds
time.sleep(3.0)
```

### 4.3 SKILL.md Structure

```markdown
---
name: skill-name
description: "Brief description of what the skill does."
---

# Skill Name

## Overview
What this skill does and when to use it.

## Workflow
1. Step 1
2. Step 2
3. Step 3

## Scripts
- `scripts/script_name.py` - Description
```

### 4.4 Command Markdown Structure

```markdown
---
name: command-name
description: "Brief description"
allowed-tools: Read, Write, Bash, Task, Skill
---

# Command Name

Description of what the command does.

## Arguments
- `--arg1 <value>` (required): Description
- `--arg2 <value>` (optional): Description

## Examples
\`\`\`
/plugin:command-name --arg1 value
\`\`\`
```

---

## 5. Error Handling

### 5.1 Exception Hierarchy

```python
class PaperResearcherError(Exception):
    """Base exception for paper-researcher plugin."""
    pass

class ArxivAPIError(PaperResearcherError):
    """Error communicating with arXiv API."""
    pass

class StorageError(PaperResearcherError):
    """Error reading/writing to storage."""
    pass

class ValidationError(PaperResearcherError):
    """Error validating input data."""
    pass
```

### 5.2 Error Handling Pattern

```python
def fetch_papers(query: str) -> list[dict]:
    try:
        response = requests.get(ARXIV_URL, params={"search_query": query})
        response.raise_for_status()
        return parse_response(response.text)
    except requests.Timeout:
        raise ArxivAPIError("Request timed out. Try again later.")
    except requests.HTTPError as e:
        if e.response.status_code == 503:
            raise ArxivAPIError("arXiv service unavailable. Try again later.")
        raise ArxivAPIError(f"HTTP error: {e}")
    except Exception as e:
        raise ArxivAPIError(f"Unexpected error: {e}")
```

### 5.3 User-Facing Error Messages

```python
# Good: Actionable, user-friendly
"Failed to fetch papers after 3 retries. Check your internet connection."

# Bad: Technical jargon
"HTTPError 503: Service Temporarily Unavailable"
```

---

## 6. Testing Standards

### 6.1 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Test data
├── test_fetch_arxiv.py      # Unit tests for fetch_arxiv.py
├── test_store_paper.py
└── test_integration.py      # Integration tests
```

### 6.2 Test Naming

```python
def test_fetch_papers_returns_list_on_success():
    """Tests should describe expected behavior."""
    ...

def test_fetch_papers_raises_error_on_timeout():
    """Include edge cases in test names."""
    ...
```

### 6.3 Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def sample_paper_metadata() -> dict:
    """Sample paper metadata for testing."""
    return {
        "id": "2401.12345",
        "title": "Test Paper",
        "authors": ["Test Author"],
        "abstract": "Test abstract",
        "published": "2024-01-15",
    }

@pytest.fixture
def temp_data_dir(tmp_path) -> Path:
    """Temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "papers").mkdir()
    (data_dir / "index").mkdir()
    return data_dir
```

### 6.4 Mocking External APIs

```python
import responses

@responses.activate
def test_fetch_papers_handles_api_response():
    # Mock arXiv API response
    responses.add(
        responses.GET,
        "http://export.arxiv.org/api/query",
        body=open("tests/fixtures/arxiv_response.xml").read(),
        status=200,
    )

    result = fetch_papers("LLM agents")
    assert len(result) == 5
```

### 6.5 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=skills --cov-report=html

# Run specific test file
pytest tests/test_fetch_arxiv.py

# Run tests matching pattern
pytest -k "test_fetch"
```

---

## 7. Git Conventions

### 7.1 Branch Naming

```
feature/{description}    # New features
fix/{description}        # Bug fixes
docs/{description}       # Documentation
refactor/{description}   # Code refactoring
```

Examples:
- `feature/semantic-scholar-integration`
- `fix/retry-logic-timeout`
- `docs/update-readme`

### 7.2 Commit Messages

Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Examples:
```
feat(collector): add exponential backoff retry logic

fix(summarizer): handle empty abstract gracefully

docs(readme): add installation instructions
```

### 7.3 Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest`)
- [ ] Type checking passes (`mypy`)
- [ ] Linting passes (`ruff check`)
- [ ] Documentation updated if needed
- [ ] No sensitive data committed

---

## 8. Security Guidelines

### 8.1 Input Validation

```python
import re

def validate_arxiv_id(paper_id: str) -> bool:
    """Validate arXiv ID format."""
    if not paper_id:
        return False
    return bool(re.match(r"^\d{4}\.\d{4,5}$", paper_id))

def validate_query(query: str) -> bool:
    """Validate search query - prevent injection."""
    if not query or len(query) > 500:
        return False
    # Reject shell metacharacters
    if re.search(r"[;<>&|`$]", query):
        return False
    return True
```

### 8.2 File Operations

```python
from pathlib import Path

def safe_write(file_path: Path, content: str) -> None:
    """Safely write content to file."""
    # Ensure path is within data directory
    data_dir = Path("data").resolve()
    target = file_path.resolve()

    if not str(target).startswith(str(data_dir)):
        raise SecurityError(f"Path escape attempt: {file_path}")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
```

### 8.3 Secrets Management

- Never commit API keys or secrets
- Use environment variables for configuration
- Add secrets patterns to `.gitignore`

---

## 9. Performance Guidelines

### 9.1 API Rate Limiting

```python
import time

REQUEST_DELAY = 3.0  # arXiv rate limit

def rate_limited_request(url: str) -> requests.Response:
    """Make rate-limited request."""
    response = requests.get(url)
    time.sleep(REQUEST_DELAY)
    return response
```

### 9.2 Efficient File Operations

```python
# Good: Read file once
def search_papers(query: str) -> list[dict]:
    index = json.loads(Path("data/index/papers.json").read_text())
    return [p for p in index["papers"].values() if query in p["title"]]

# Bad: Read file for each paper
def search_papers(query: str) -> list[dict]:
    results = []
    for paper_dir in Path("data/papers").iterdir():
        meta = json.loads((paper_dir / "metadata.json").read_text())
        if query in meta["title"]:
            results.append(meta)
    return results
```

### 9.3 Memory Management

```python
# Good: Generator for large datasets
def iter_papers() -> Iterator[dict]:
    for paper_dir in Path("data/papers").iterdir():
        yield json.loads((paper_dir / "metadata.json").read_text())

# Bad: Load all into memory
def get_all_papers() -> list[dict]:
    return [
        json.loads((d / "metadata.json").read_text())
        for d in Path("data/papers").iterdir()
    ]
```

---

## 10. Logging Standards

### 10.1 Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed diagnostic info |
| INFO | Normal operation messages |
| WARNING | Unexpected but handled situations |
| ERROR | Errors that prevent operation |

### 10.2 Logging Pattern

```python
import logging

logger = logging.getLogger(__name__)

def fetch_papers(query: str) -> list[dict]:
    logger.info(f"Fetching papers for query: {query}")

    try:
        response = requests.get(ARXIV_URL, params={"search_query": query})
        logger.debug(f"API response status: {response.status_code}")
        papers = parse_response(response.text)
        logger.info(f"Found {len(papers)} papers")
        return papers
    except Exception as e:
        logger.error(f"Failed to fetch papers: {e}")
        raise
```

---

## 11. Development Workflow

### 11.1 Setup

```bash
# Clone repository
git clone <repo-url>
cd paper-researcher

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync --all-extras
```

### 11.2 Development Cycle

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `pytest`
4. Run linting: `ruff check .`
5. Run type check: `mypy skills/`
6. Commit: `git commit -m "feat: add feature"`
7. Push: `git push origin feature/my-feature`
8. Create pull request

### 11.3 Pre-commit Checks

```bash
# Manual pre-commit check
ruff format .
ruff check --fix .
mypy skills/
pytest
```

---

## 12. Troubleshooting

### 12.1 Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Check virtual environment is activated |
| API timeout | Increase timeout, check network |
| Permission denied | Check file permissions on data/ |
| Type errors | Run `mypy` and fix annotations |

### 12.2 Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```
