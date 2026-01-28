# Design: Paper Search Feature

**Feature:** F3: Paper Search
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Complete

---

## Overview

This document describes the implementation design for the paper search feature.

## Architecture

### Component Diagram

```
User
 ↓
/paper-researcher:paper-search <query>
 ↓
commands/paper-search.md
 ↓
skills/paper-searcher/SKILL.md
 ↓
scripts/search_index.py
 ↓
data/index/papers.json (read)
 ↓
Search results (stdout)
```

### Data Flow

1. User invokes `/paper-researcher:paper-search "query"`
2. Command parses query argument
3. Skill invokes `search_index.py` script
4. Script loads index, performs search, ranks results
5. Results formatted and returned to user

## Implementation Approach

### Search Algorithm

**Simple keyword matching:**
- Tokenize query into keywords
- For each paper, search keywords in:
  - Title (weight: 3x)
  - Abstract (weight: 2x)
  - Summary content (weight: 1x)
- Calculate relevance score = sum of weighted matches
- Sort by relevance score descending
- Return top N results

**Excerpt Generation:**
- Find first occurrence of any keyword in abstract/summary
- Extract surrounding context (±50 characters)
- Highlight matched keyword

### Components to Create

#### 1. Script: `search_index.py`

**Location:** `skills/paper-searcher/scripts/search_index.py`

**Functions:**
- `load_index(data_dir: Path) -> dict` - Load papers.json
- `tokenize_query(query: str) -> list[str]` - Split query into keywords
- `search_paper(paper: dict, keywords: list[str]) -> float` - Calculate relevance score
- `extract_excerpt(text: str, keywords: list[str], context: int = 50) -> str` - Generate excerpt
- `search_papers(query: str, data_dir: Path, limit: int) -> list[dict]` - Main search function
- `main()` - CLI entry point

**CLI Arguments:**
- `--query <str>` (required) - Search query
- `--data-dir <path>` (optional, default: ./data) - Data directory
- `--limit <int>` (optional, default: 10) - Max results

**Output Format (JSON):**
```json
{
  "query": "attention mechanisms",
  "count": 5,
  "results": [
    {
      "id": "2401.12345",
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "score": 8.5,
      "excerpt": "...focused on attention mechanisms for..."
    }
  ]
}
```

#### 2. Skill: `paper-searcher`

**Location:** `skills/paper-searcher/SKILL.md`

**Workflow:**
1. Validate query is non-empty
2. Run `search_index.py --query "<query>" --limit 10`
3. Parse JSON output
4. Format results for user display
5. Handle empty results gracefully

#### 3. Command: `paper-search`

**Location:** `commands/paper-search.md`

**Arguments:**
- `<query>` (required) - Search query

**Example Usage:**
```
/paper-researcher:paper-search "attention mechanisms"
/paper-researcher:paper-search "transformer architectures"
```

#### 4. Agent: `paper-searcher` (optional)

**Location:** `agents/paper-searcher.md`

**Purpose:** Could be used for batch searches or more complex search workflows (deferred for now, not required for P0)

### Files to Create/Modify

**New Files:**
- `skills/paper-searcher/scripts/search_index.py`
- `skills/paper-searcher/SKILL.md`
- `commands/paper-search.md`
- `tests/test_search_index.py`

**Modified Files:**
- `README.md` - Add search command documentation

### Error Handling

| Error Scenario | Handling |
|----------------|----------|
| Empty query | Return error message "Query cannot be empty" |
| Index file missing | Return error "No papers collected yet. Run /paper-collect first." |
| No search results | Return "No papers found matching '<query>'" |
| Invalid data directory | Return error with path |

### Edge Cases

- Query with special characters → Sanitize/tokenize
- Very long query → Truncate to reasonable length
- Papers without summaries → Search title + abstract only
- Papers without abstracts → Search title + summary only

## Testing Strategy

### Unit Tests

**test_search_index.py:**
- `test_load_index()` - Verify index loading
- `test_tokenize_query()` - Verify query parsing
- `test_search_paper()` - Verify relevance scoring
- `test_extract_excerpt()` - Verify excerpt generation
- `test_empty_query()` - Handle empty query
- `test_no_results()` - Handle no matches
- `test_cli_arguments()` - Verify argument parsing

### Test Fixtures

- `tests/fixtures/search_index.json` - Sample index with multiple papers
- `tests/fixtures/search_results.json` - Expected search output

## Performance Considerations

- In-memory search (load index once)
- Simple keyword matching (no regex overhead)
- Limit results to 10 by default
- Target: < 2 seconds for search (should be < 1s for small collections)

## Security Considerations

- Validate query length (< 500 chars)
- Sanitize query to prevent injection
- Validate data directory path

## Future Enhancements (Out of Scope)

- Semantic search using embeddings
- Boolean operators (AND, OR, NOT)
- Date range filtering
- Author filtering
- Category filtering
- Fuzzy matching
- Query suggestions

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Simple keyword matching | Fast, no dependencies, good enough for MVP |
| Weighted scoring | Prioritize title matches over content |
| JSON output from script | Structured, parseable, testable |
| In-memory search | Fast for small collections (< 1000 papers) |
| No regex | Simpler, more predictable, faster |

---

## References

- PRD Section 2.1 (F3: Paper Search)
- Functional Design Section 3.3 (Workflow: Search Papers)
- Architecture Doc Section 8.1 (Performance Targets)
