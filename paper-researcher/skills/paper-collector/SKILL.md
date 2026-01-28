---
name: paper-collector
description: "Fetch research papers from arXiv API and store locally. This skill should be used when users want to collect new papers on specific topics."
---

# Paper Collector Skill

Collect research papers from arXiv based on user-specified topics/keywords.

## When to Use

Use this skill when the user wants to:
- Collect new papers on a specific topic
- Fetch recent publications from arXiv
- Build a local paper collection for research

## Arguments

The skill receives these arguments from the command:
- `topic` (required): Search topic/keywords
- `days` (optional, default=7): Days to look back
- `max` (optional, default=50): Maximum papers to collect

## Workflow

### Step 1: Validate Arguments

Ensure required arguments are provided:
- `topic` must be a non-empty string
- `days` must be a positive integer
- `max` must be between 1 and 50

### Step 2: Fetch Papers from arXiv

Run the fetch script to query arXiv API:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-collector/scripts/fetch_arxiv.py \
    --query "<topic>" \
    --days <days> \
    --max <max> \
    --output /tmp/papers.json
```

**Expected Output:** JSON file with paper metadata

**Error Handling:**
- If script returns non-zero exit code, check stderr for error details
- Common errors: network timeout, arXiv API unavailable
- Retry logic is built into the script (3 attempts with backoff)

### Step 3: Store Papers Locally

Run the store script to save papers to disk:

```bash
cd /path/to/paper-researcher
uv run python skills/paper-collector/scripts/store_paper.py \
    --input /tmp/papers.json \
    --data-dir ./data
```

**Expected Output:**
- Paper metadata saved to `data/papers/{arxiv_id}/metadata.json`
- Index updated at `data/index/papers.json`
- Console output with count of saved papers

**Error Handling:**
- Duplicate papers are automatically skipped
- File I/O errors are logged and reported

### Step 4: Generate Summaries

After storing papers, spawn the `paper-summarizer` agent to generate summaries for all newly collected papers.

**Spawn Agent:**
Use the Task tool to spawn the paper-summarizer agent:
```
Task('paper-summarizer', 'Generate summaries for all unsummarized papers')
```

The agent will:
1. Find all papers with `has_summary: false` in the index
2. Generate structured summaries for each paper
3. Save summaries to `data/papers/{id}/summary.md`
4. Update `has_summary: true` in metadata and index
5. Report summary generation progress

**Error Handling:**
- If summarization fails for a paper, log warning and continue
- Summary failures don't affect paper collection success

### Step 5: Report Results

Format the results for the user:

```
Collected <N> new papers on "<topic>" (past <days> days)

New papers:
1. [<arxiv_id>] "<title>" - <authors>
2. [<arxiv_id>] "<title>" - <authors>
...

Summaries generated for <N> papers.
```

If no papers found:
```
No papers found for "<topic>" in the past <days> days.
Try different keywords or a longer time range.
```

## Scripts

### fetch_arxiv.py

**Location:** `skills/paper-collector/scripts/fetch_arxiv.py`

**Purpose:** Query arXiv API and fetch paper metadata

**Usage:**
```bash
python fetch_arxiv.py --query "<topic>" --days <N> --max <N> --output papers.json
```

**Output Format:**
```json
{
  "success": true,
  "count": 12,
  "query": "LLM agents",
  "days": 7,
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

**Error Format:**
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

### store_paper.py

**Location:** `skills/paper-collector/scripts/store_paper.py`

**Purpose:** Store paper metadata to local filesystem

**Usage:**
```bash
python store_paper.py --input papers.json --data-dir ./data
```

**Output Format:**
```
Stored 10 new papers (2 duplicates skipped)
{
  "success": true,
  "saved": 10,
  "duplicates": 2,
  "total": 12
}
```

## Data Storage

Papers are stored in the following structure:

```
data/
├── papers/
│   ├── 2401.12345/
│   │   └── metadata.json
│   └── 2401.12346/
│       └── metadata.json
└── index/
    └── papers.json
```

### metadata.json

Individual paper metadata:
```json
{
  "id": "2401.12345",
  "title": "Paper Title",
  "authors": ["Author 1"],
  "abstract": "...",
  "published": "2024-01-15",
  "collected_at": "2026-01-27T10:00:00",
  "topics": ["LLM agents"],
  "has_summary": false
}
```

### papers.json (Index)

Global index for quick lookups:
```json
{
  "version": "1.0",
  "updated_at": "2026-01-27T10:00:00",
  "papers": {
    "2401.12345": {
      "title": "Paper Title",
      "authors": ["Author 1"],
      "topics": ["LLM agents"],
      "collected_at": "2026-01-27T10:00:00",
      "has_summary": false
    }
  }
}
```

## Troubleshooting

### arXiv API Errors

**503 Service Temporarily Unavailable:**
- arXiv has rate limiting, script includes 3-second delays
- Script retries 3 times with exponential backoff
- If persistent, try again later

**Empty Results:**
- Try broader keywords
- Increase `--days` parameter
- Check arXiv directly to verify papers exist

### Storage Errors

**Permission Denied:**
- Ensure `data/` directory is writable
- Check disk space

**Corrupted Index:**
- Delete `data/index/papers.json` and re-run collection
- Index will be rebuilt automatically
