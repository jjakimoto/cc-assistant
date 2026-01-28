# Paper Researcher

AI-powered research paper collection, summarization, and search pipeline.

## Overview

Paper Researcher is a Claude Code plugin that enables researchers and developers to automatically collect, summarize, and search academic papers. The plugin eliminates manual paper discovery overhead by fetching papers from sources like arXiv, generating AI-powered summaries, and providing semantic search across collected papers.

**Tagline:** "From papers to insights, automatically"

## Features

### P0 (MVP)
- **Paper Collection** - Auto-fetch papers from arXiv based on topics/keywords
- **Paper Summarization** - Generate concise summaries of paper content using Claude
- **Paper Search** - Find relevant papers in your collection by topic or question

### P1 (Nice-to-Have)
- Daily/Weekly Digest - Scheduled summaries of new papers
- Citation Graph - Track related papers and references
- Blog Post Generation - Transform summaries into readable blog posts

## Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Claude Code CLI

### Setup

1. Clone or copy this plugin to your plugins directory:

```bash
cd your-project
git clone <this-repo> paper-researcher
```

2. Install dependencies:

```bash
cd paper-researcher
uv venv
uv sync
```

3. Register with Claude Code:

```bash
claude plugin install ./paper-researcher
```

## Usage

### Collect Papers

Fetch papers from arXiv based on a topic:

```bash
/paper-researcher:paper-collect --topic "LLM agents" --days 7
```

**Arguments:**
- `--topic <string>` (required): Search query/topic
- `--days <int>` (optional, default=7): Days to look back
- `--max <int>` (optional, default=50): Maximum papers to collect

**Example Output:**
```
Collected 12 new papers on "LLM agents" (past 7 days)

New papers:
1. [2401.12345] "Agent Framework for LLM Applications" - Smith et al.
2. [2401.12346] "Multi-Agent Collaboration in Language Models" - Jones et al.
...
```

### Search Papers

Search your collected papers by keyword or question:

```bash
/paper-researcher:paper-search "attention mechanisms"
```

**Arguments:**
- `<query>` (required): Search keywords or natural language question

**Example Output:**
```
Found 5 papers matching "attention mechanisms":

1. [2401.12345] "Attention is All You Need Revisited" - Smith et al.
   Score: 8.5
   > "...novel attention mechanism that improves on the original..."

2. [2401.12346] "Multi-Head Attention Patterns" - Jones et al.
   Score: 6.0
   > "...analyzing attention patterns across layers..."
```

**Search Features:**
- Searches across paper titles, abstracts, and summaries
- Returns ranked results by relevance score
- Extracts relevant excerpts showing matched content
- Case-insensitive matching

### Summarize a Paper

Generate a summary for a specific paper:

```bash
/paper-researcher:paper-summarize 2401.12345
```

**Arguments:**
- `<paper-id>` (required): arXiv paper ID

**Example Output:**
```markdown
# Agent Framework for LLM Applications

**Authors:** John Smith, Jane Doe
**arXiv:** 2401.12345 | **Published:** 2024-01-15

## Problem
Current LLM applications struggle with complex multi-step tasks...

## Method
The authors propose a hierarchical agent framework...

## Results
45% improvement over baseline on ALFWorld benchmark...

## Takeaways
- Hierarchical decomposition improves task handling
- Reflection phases are critical for error recovery
- Framework is model-agnostic
```

### Generate Digest

Create a digest of recently collected papers:

```bash
/paper-researcher:paper-digest --since 7d
```

## Data Storage

Papers are stored locally in the `data/` directory (excluded from git):

```
data/
├── papers/           # Individual paper directories
│   ├── 2401.12345/
│   │   ├── metadata.json
│   │   ├── summary.md
│   │   └── paper.pdf (optional)
│   └── ...
├── index/            # Search index
│   └── papers.json
└── digests/          # Generated digests
    └── 2026-01-27.md
```

## Development

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

### Type Checking

```bash
uv run mypy .
```

## Architecture

```
paper-researcher/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── commands/
│   ├── paper-collect.md     # Collect papers from arXiv
│   ├── paper-search.md      # Search collected papers
│   └── paper-summarize.md   # Summarize a specific paper
├── skills/
│   ├── paper-collector/
│   │   ├── SKILL.md         # Collection workflow
│   │   └── scripts/
│   │       ├── fetch_arxiv.py
│   │       └── store_paper.py
│   ├── paper-searcher/
│   │   ├── SKILL.md         # Search workflow
│   │   └── scripts/
│   │       └── search_index.py
│   └── paper-summarizer/
│       ├── SKILL.md         # Summarization workflow
│       └── scripts/
│           └── update_summary_status.py
├── agents/
│   └── paper-summarizer.md  # Batch summarization agent
├── tests/
├── data/                    # Runtime data (gitignored)
├── pyproject.toml
└── README.md
```

## Troubleshooting

### Common Issues

**arXiv API Rate Limiting**

If you see errors about rate limiting, the script has built-in retry logic with exponential backoff. If issues persist, wait a few minutes and try again.

**No papers found**

- Try broadening your search query
- Increase the `--days` parameter to search further back
- Check that your topic keywords match arXiv paper titles/abstracts

**No search results**

- Try different or broader keywords
- Ensure papers have been collected first with `/paper-researcher:paper-collect`
- Search uses keyword matching - try simpler terms

**Import errors when running scripts**

Ensure dependencies are installed:
```bash
cd paper-researcher
uv sync
```

**Tests failing**

Make sure you're running tests from the `paper-researcher` directory:
```bash
cd paper-researcher
uv run pytest
```

**Type checking errors with feedparser**

feedparser doesn't have type stubs. The `# type: ignore[import-untyped]` comment is expected.

## License

MIT
