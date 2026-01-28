# Requirements: Paper Collection Feature

**Feature:** F1: Paper Collection
**Priority:** P0 (MVP)
**Date:** 2026-01-27
**Status:** Active

---

## Overview

Auto-fetch papers from arXiv based on user-specified topics/keywords. This is the foundational feature of the Paper Researcher plugin that enables automatic paper discovery.

## User Stories

1. **As a researcher**, I want to collect papers on "LLM agents" from the past 7 days so I can stay current on the topic.
2. **As a developer**, I want to specify multiple topics so I can track different research areas.
3. **As a user**, I want reliable paper collection that handles API failures gracefully.

## Acceptance Criteria

- [ ] Fetch papers from arXiv API based on query terms
- [ ] Support date range filtering (default: 7 days)
- [ ] Limit results to 50 papers per request (configurable)
- [ ] Retry with exponential backoff on API failures (3 attempts)
- [ ] Store paper metadata locally in `./data/papers/`
- [ ] Data directory excluded from git via `.gitignore`
- [ ] Report count of new papers collected

## Functional Requirements

### FR-1: arXiv API Integration
- Query arXiv API at `http://export.arxiv.org/api/query`
- Support topic/keyword-based search
- Support date range filtering using `submittedDate` field
- Parse Atom feed response using feedparser
- Handle pagination if needed

### FR-2: Retry Logic
- Implement exponential backoff on failures
- Max 3 retry attempts
- Backoff factor of 2 (delays: 3s, 6s, 12s)
- Handle 503 Service Unavailable specifically

### FR-3: Data Storage
- Store paper metadata as JSON in `data/papers/{arxiv_id}/metadata.json`
- Maintain index at `data/index/papers.json`
- Skip duplicate papers already in collection
- Create directories automatically if they don't exist

### FR-4: Command Interface
- Slash command: `/paper-researcher:paper-collect`
- Arguments: `--topic <string>`, `--days <int>`, `--max <int>`
- Output: Count of new papers collected with list

## Non-Functional Requirements

- **Performance**: Collect 50 papers in under 60 seconds
- **Reliability**: Graceful degradation on API/network failures
- **Rate Limiting**: Respect arXiv API limits (3 second delay between requests)

## Constraints

- Python 3.10+ required
- Uses `uv` for package management
- Claude Code plugin architecture
- Local filesystem storage only

## Dependencies

- None (first feature to implement)

## Out of Scope

- PDF downloading (optional, not required for MVP)
- Summary generation (handled by F2)
- Search functionality (handled by F3)
