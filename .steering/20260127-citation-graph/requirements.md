# Requirements: Citation Graph Feature

**Feature:** F5: Citation Graph
**Priority:** P1
**Date:** 2026-01-27
**Status:** Active

---

## 1. Overview

The Citation Graph feature enables tracking of relationships between papers in the collection through citations. It extracts citation data from external APIs (Semantic Scholar), builds a relationship graph between papers, and identifies highly-cited papers within the collection.

---

## 2. User Stories

### US1: Fetch Citation Data
**As a** researcher,
**I want to** fetch citation data for papers in my collection,
**So that** I can understand how papers relate to each other.

### US2: View Highly-Cited Papers
**As a** researcher,
**I want to** identify the most-cited papers in my collection,
**So that** I can prioritize reading the most influential work.

### US3: Explore Paper Relationships
**As a** developer,
**I want to** see which papers cite or are cited by a specific paper,
**So that** I can discover related work.

---

## 3. Functional Requirements

### FR1: Citation Data Fetching
- **FR1.1:** Fetch citation data from Semantic Scholar API using arXiv paper IDs
- **FR1.2:** Store references (papers this paper cites) in metadata
- **FR1.3:** Store citations (papers citing this paper) in metadata
- **FR1.4:** Record citation counts (total, within collection)
- **FR1.5:** Handle papers not found in Semantic Scholar gracefully
- **FR1.6:** Implement retry with exponential backoff (3 attempts)
- **FR1.7:** Respect Semantic Scholar API rate limits (100 requests/5min for unauthenticated)

### FR2: Citation Index
- **FR2.1:** Create `data/index/citations.json` to store graph data
- **FR2.2:** Track edges between papers (references and cited_by)
- **FR2.3:** Maintain list of highly-cited papers (top papers by in-collection citations)
- **FR2.4:** Support atomic updates to prevent corruption

### FR3: Graph Analysis
- **FR3.1:** Calculate in-collection citation counts for each paper
- **FR3.2:** Identify highly-cited papers (top 10 by citation count)
- **FR3.3:** Support querying references and citations for a specific paper

### FR4: Command Integration
- **FR4.1:** Create `/paper-researcher:paper-citations` command
- **FR4.2:** Support fetching citations for all papers: `--all`
- **FR4.3:** Support fetching citations for a single paper: `<paper-id>`
- **FR4.4:** Display citation statistics and highly-cited papers

---

## 4. Non-Functional Requirements

### NFR1: Performance
- Fetch citations for 50 papers in under 5 minutes (rate limited)
- Build citation index in under 10 seconds

### NFR2: Reliability
- Retry failed API requests with exponential backoff
- Continue processing if individual paper lookup fails
- Atomic writes for index updates

### NFR3: Extensibility
- Abstract citation source for future providers (Google Scholar, etc.)

---

## 5. Acceptance Criteria

### AC1: Citation Fetching
- [ ] Can fetch citation data for a single paper by arXiv ID
- [ ] Can fetch citation data for all papers in collection
- [ ] Papers not in Semantic Scholar are marked with source: "unavailable"
- [ ] API failures retry 3 times with exponential backoff
- [ ] Rate limiting is respected (100 req/5min)

### AC2: Citation Index
- [ ] `citations.json` is created and maintained
- [ ] Index contains references and cited_by for each paper
- [ ] Highly-cited papers list is updated after each fetch
- [ ] Atomic writes prevent corruption

### AC3: Integration
- [ ] Command `/paper-researcher:paper-citations` works correctly
- [ ] Paper metadata includes `citation_data` field
- [ ] All tests pass (pytest)
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)

---

## 6. Data Model Extension

### Paper Metadata (Extended)
```json
{
  "id": "2401.12345",
  // ... existing fields ...
  "citation_data": {
    "source": "semantic_scholar",
    "fetched_at": "2026-01-27T12:00:00",
    "citation_count": 42,
    "reference_count": 25,
    "references_in_collection": ["2301.54321"],
    "cited_by_in_collection": ["2402.11111"]
  }
}
```

### Citations Index (New)
```json
{
  "version": "1.0",
  "updated_at": "2026-01-27T12:00:00",
  "graph": {
    "2401.12345": {
      "references": ["2301.54321"],
      "cited_by": ["2402.11111"]
    }
  },
  "stats": {
    "total_papers": 50,
    "papers_with_citations": 45,
    "total_edges": 150,
    "highly_cited": ["2301.54321", "2312.98765"]
  }
}
```

---

## 7. Technical Constraints

- Use Semantic Scholar API (no API key required for basic access)
- Rate limit: 100 requests per 5 minutes (unauthenticated)
- arXiv ID format: `YYMM.NNNNN` or `YYMM.NNNN`
- Follow existing script patterns (argparse, logging, JSON output)

---

## 8. Out of Scope

- Visualization of citation graph (P2 feature)
- Citation data from PDF extraction
- Multi-hop citation traversal (citations of citations)
- Citation count trends over time
