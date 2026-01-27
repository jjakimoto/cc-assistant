# Paper Researcher Plugin - Idea Memo

**Project Type:** Internal Tool (Claude Code Plugin)
**Plugin Name:** `paper-researcher`
**Generated:** 2026-01-27
**Tagline:** "From papers to insights, automatically"

## Vision

Researchers/developers can automatically collect, search, and summarize academic papers to stay current on topics of interest without manual reading overhead.

**Interface:** All interactions happen through Claude Code slash commands (e.g., `/paper-collect`, `/paper-search`), which invoke skills that execute Python scripts.

### Success Criteria
- Discover relevant new papers weekly with zero manual searching
- Get actionable summaries in under 2 minutes per paper
- Never miss important papers in areas of interest

---

## Problems to Solve

**Primary:** Researchers struggle with staying current on relevant papers because there are too many publications across multiple sources (arXiv, conferences, journals), leading to either information overload or missing important work.

**Secondary pain points:**
- Manual paper discovery is time-consuming
- Reading full papers takes hours when you only need key insights
- No centralized system to track papers of interest
- Hard to connect papers to your specific research questions

---

## Features

### P0 (MVP)
1. **Paper Collection** - Auto-fetch papers from arXiv based on topics/keywords
2. **Paper Summarization** - Generate concise summaries of paper content using Claude
3. **Search/Query** - Find relevant papers in your collection by topic or question

### P1 (Nice-to-Have)
4. Daily/Weekly Digest - Scheduled summaries of new papers
5. Citation Graph - Track related papers and references
6. Blog Post Generation - Transform summaries into readable blog posts

### P2 (Future)
7. Multi-format Export - PDF annotations, Notion, Obsidian integration
8. Collaboration - Share collections with team members

---

## Integration Requirements

### Phase Rollout

| Phase | Source | Status |
|-------|--------|--------|
| 1 (MVP) | arXiv API | Reference plugin implementation |
| 2 | Local PDF upload | Built-in |
| 3 | Semantic Scholar API | Plugin |
| 4 | Web crawling (conference sites, blogs) | Plugin |
| 5 | Google Scholar | Plugin (if feasible) |

### Plugin Architecture

All paper sources designed as plugins for extensibility:

- `source_plugin` - Fetch papers from external source
- `parser_plugin` - Extract text/metadata from different formats
- `storage_plugin` - Where to save (local files, vector DB, etc.)

---

## Technical Approach

**Core Principle:** This is a Claude Code plugin named `paper-researcher`. Users invoke slash commands, which trigger skills. Skills contain workflow instructions and call Python scripts via Bash for deterministic operations.

### Plugin Structure

The plugin follows the standard Claude Code plugin format:

```
paper-researcher/
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── CLAUDE.md                    # Plugin-level instructions (optional)
├── README.md                    # Documentation
├── agents/                      # Agent definitions
│   ├── arxiv-fetcher.md         # Fetches papers from arXiv
│   ├── paper-summarizer.md      # Generates summaries
│   └── paper-searcher.md        # Searches paper collection
├── commands/                    # Slash commands (entry points)
│   ├── paper-collect.md         # /paper-collect
│   ├── paper-search.md          # /paper-search
│   ├── paper-summarize.md       # /paper-summarize
│   └── paper-digest.md          # /paper-digest
└── skills/                      # Skills with bundled scripts
    ├── paper-collector/
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── fetch_arxiv.py
    │       └── store_paper.py
    ├── paper-summarizer/
    │   ├── SKILL.md
    │   └── scripts/
    │       └── parse_pdf.py
    ├── paper-searcher/
    │   ├── SKILL.md
    │   └── scripts/
    │       └── search_index.py
    └── paper-digest/
        ├── SKILL.md
        └── scripts/
            └── build_digest.py
```

### Plugin Metadata

`.claude-plugin/plugin.json`:
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

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER                                        │
│   /paper-researcher:paper-collect  /paper-researcher:search     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     COMMANDS (commands/)                        │
│  paper-collect.md  paper-search.md  paper-summarize.md          │
│  (invoke skills or spawn agents)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     SKILLS (skills/)                            │
│  paper-collector/  paper-summarizer/  paper-searcher/           │
│  ├── SKILL.md         (workflow instructions)                   │
│  └── scripts/         (Python utilities)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTS (agents/)                            │
│  arxiv-fetcher.md  paper-summarizer.md  paper-searcher.md       │
│  (specialized workers spawned by Task tool)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA (data/)                                │
│  papers/  index/  digests/                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Definitions

#### Commands (`commands/`)
Slash command entry points. Markdown files with YAML frontmatter.

| Command | Description | Invokes |
|---------|-------------|---------|
| `/paper-researcher:paper-collect` | Fetch new papers from sources | `paper-collector` skill |
| `/paper-researcher:paper-search <query>` | Search collected papers | `paper-searcher` skill |
| `/paper-researcher:paper-summarize <paper>` | Summarize a specific paper | `paper-summarizer` skill |
| `/paper-researcher:paper-digest` | Generate digest of recent papers | `paper-digest` skill |

Example command (`commands/paper-collect.md`):
```markdown
---
name: paper-collect
description: "Fetch new papers from arXiv based on topics/keywords and store locally."
allowed-tools: Read, Write, Edit, Bash, Task, Skill
---

# Paper Collection Command

Invoke the paper-collector skill to fetch papers.

Arguments: `--topic <topic> [--days <N>]`

Example: `/paper-researcher:paper-collect --topic "LLM agents" --days 7`
```

#### Skills (`skills/`)
Self-contained packages with SKILL.md + bundled scripts.

| Skill | Purpose | Bundled Scripts |
|-------|---------|-----------------|
| `paper-collector/` | Fetch papers from arXiv, store locally | `fetch_arxiv.py`, `store_paper.py` |
| `paper-summarizer/` | Generate summaries using Claude | `parse_pdf.py` |
| `paper-searcher/` | Search across paper collection | `search_index.py` |
| `paper-digest/` | Weekly digest of new papers | `build_digest.py` |

Example skill (`skills/paper-collector/SKILL.md`):
```markdown
---
name: paper-collector
description: "Fetch research papers from arXiv API and store locally. This skill should be used when users want to collect new papers on specific topics."
---

# Paper Collector Skill

## Workflow

1. Run `scripts/fetch_arxiv.py` with topic and date range
2. For each paper found, run `scripts/store_paper.py` to save metadata
3. Report count of new papers collected

## Scripts

- `scripts/fetch_arxiv.py --query <topic> --days <N>` - Query arXiv API
- `scripts/store_paper.py --input <json>` - Store paper metadata to data/papers/
```

#### Agents (`agents/`)
Specialized autonomous workers for complex tasks.

| Agent | Responsibility |
|-------|----------------|
| `arxiv-fetcher` | Fetch papers from arXiv API (used by paper-collector skill) |
| `paper-summarizer` | Generate Claude-powered summaries |
| `paper-searcher` | Semantic search across collection |

### Data Storage

```
data/
├── papers/                    # Raw paper storage
│   ├── 2401.12345/
│   │   ├── metadata.json      # Title, authors, abstract, etc.
│   │   ├── paper.pdf          # Original PDF (optional)
│   │   └── summary.md         # Generated summary
│   └── ...
├── index/                     # Search index
│   └── papers.json            # Paper metadata index
└── digests/                   # Generated digests
    └── 2026-01-27.md
```

### Language

Python for scripts - best ecosystem for arXiv API, PDF parsing, and data processing.

---

## Clarifications Applied

| Question | Decision |
|----------|----------|
| Project Type | Internal Tool (workflow automation) |
| Core Idea | Auto-collect, search, summarize papers |
| Success Definition | Zero manual searching, 2-min summaries, never miss papers |
| Tagline | "From papers to insights, automatically" |
| Pain Points | Information overload, time-consuming reading |
| P0 Features | Collection + Summarization + Search |
| Initial Integration | arXiv only (simplicity first) |
| Plugin Design | All sources as plugins, arXiv as reference |
| Tech Stack | Claude Code plugin (`paper-researcher`) → commands → skills → agents → Python scripts |

---

## Open Questions

- [ ] What specific topics/keywords to track initially?
- [ ] Preferred summary length (brief vs detailed)?
- [ ] Frequency of paper checks (daily, weekly, on-demand)?
- [ ] Filtering criteria (citations, authors, conferences)?

---

## Next Steps

1. Review this document
2. Run `/specd:setup-project` for full documentation (PRD, architecture, etc.)
3. Create the `paper-researcher` plugin:

   **Phase 1: Plugin Foundation**
   - Create plugin directory structure
   - Create `.claude-plugin/plugin.json`
   - Create `README.md` and optional `CLAUDE.md`

   **Phase 2: paper-collector (Core Feature)**
   - Create `commands/paper-collect.md`
   - Create `skills/paper-collector/SKILL.md`
   - Implement `skills/paper-collector/scripts/fetch_arxiv.py`
   - Implement `skills/paper-collector/scripts/store_paper.py`
   - Create `agents/arxiv-fetcher.md` (optional, for complex fetching)

   **Phase 3: paper-summarizer**
   - Create `commands/paper-summarize.md`
   - Create `skills/paper-summarizer/SKILL.md`
   - Implement `skills/paper-summarizer/scripts/parse_pdf.py`
   - Create `agents/paper-summarizer.md`

   **Phase 4: paper-searcher**
   - Create `commands/paper-search.md`
   - Create `skills/paper-searcher/SKILL.md`
   - Implement `skills/paper-searcher/scripts/search_index.py`
   - Create `agents/paper-searcher.md`

   **Phase 5: paper-digest & Polish**
   - Create `commands/paper-digest.md`
   - Create `skills/paper-digest/SKILL.md`
   - Implement `skills/paper-digest/scripts/build_digest.py`
   - Test end-to-end workflow
   - Documentation
