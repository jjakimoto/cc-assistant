---
name: paper-collaborator
description: "Enable collaboration features: share collections, import shared papers, and annotate papers."
---

# Paper Collaborator Skill

This skill enables collaboration features for the paper-researcher plugin:
- Share paper collections as portable ZIP packages
- Import shared collections from team members
- Add and view annotations on papers

## When to Use

- When a user wants to share their paper collection with others
- When a user wants to import a shared collection
- When a user wants to annotate papers
- When a user wants to view annotations on papers

## Operations

### 1. Share Collection

Create a portable ZIP package containing papers, summaries, and annotations.

**Arguments:**
- `--output <path>` (optional): Output ZIP file path (default: `./collection.zip`)
- `--paper-id <id>` (optional, repeatable): Specific paper IDs to include
- `--include-summaries` (optional): Include AI-generated summaries
- `--include-annotations` (optional): Include annotations
- `--username <name>` (optional): Creator username for manifest
- `--description <text>` (optional): Description for the collection

**Workflow:**

1. Validate arguments
2. Execute share script:

```bash
uv run python skills/paper-collaborator/scripts/share_collection.py \
  --output <output-path> \
  [--paper-id <id>]... \
  [--include-summaries] \
  [--include-annotations] \
  [--username <name>] \
  [--description <text>] \
  --data-dir ./data
```

**Expected Success Output:**
```json
{
  "success": true,
  "message": "Created collection package with 12 papers.",
  "paper_count": 12,
  "paper_ids": ["2401.12345", ...],
  "output_path": "/absolute/path/to/collection.zip",
  "includes_summaries": true,
  "includes_annotations": false
}
```

**Expected Error Output:**
```json
{
  "success": false,
  "error": {
    "code": "INDEX_NOT_FOUND",
    "message": "No papers collected yet. Run /paper-collect first.",
    "details": "..."
  }
}
```

3. Display results to user:
   - Package path
   - Number of papers included
   - What content was included
   - Instructions for sharing

---

### 2. Import Collection

Import a shared ZIP package, merging papers into the local collection.

**Arguments:**
- `--input <path>` (required): Path to ZIP package
- `--overwrite` (optional): Overwrite existing papers

**Workflow:**

1. Validate ZIP file exists
2. Execute import script:

```bash
uv run python skills/paper-collaborator/scripts/import_collection.py \
  --input <input-path> \
  [--overwrite] \
  --data-dir ./data
```

**Expected Success Output:**
```json
{
  "success": true,
  "message": "Imported 10 papers (2 skipped, 5 annotations).",
  "imported_count": 10,
  "skipped_count": 2,
  "annotation_count": 5,
  "imported_ids": ["2401.12345", ...]
}
```

**Expected Error Output:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PACKAGE",
    "message": "Invalid or corrupted package",
    "details": "..."
  }
}
```

3. Display results to user:
   - Import summary
   - List of imported papers
   - Any warnings or skipped items

---

### 3. Add Annotation

Save an annotation for a paper.

**Arguments:**
- `--paper-id <id>` (required): arXiv paper ID
- `--type <type>` (optional): Annotation type (note, highlight, question, comment)
- `--content <text>` or `--content-file <path>`: Annotation content

**Workflow:**

1. Validate paper ID format
2. Check paper exists in collection
3. If `--content` not provided, prompt user for annotation content
4. Execute save script:

```bash
uv run python skills/paper-collaborator/scripts/save_annotation.py \
  --paper-id <paper-id> \
  --content "<content>" \
  [--type <type>] \
  --data-dir ./data
```

**Expected Success Output:**
```json
{
  "success": true,
  "message": "Saved annotation for paper 2401.12345.",
  "annotation_id": "abc12345",
  "paper_id": "2401.12345",
  "author": "researcher",
  "type": "note"
}
```

5. Display confirmation to user

---

### 4. List Annotations

View annotations for a paper.

**Arguments:**
- `--paper-id <id>` (required): arXiv paper ID
- `--format <format>` (optional): Output format (text, markdown, json)

**Workflow:**

1. Validate paper ID format
2. Execute list script:

```bash
uv run python skills/paper-collaborator/scripts/list_annotations.py \
  --paper-id <paper-id> \
  [--format <format>] \
  --data-dir ./data
```

**Expected Success Output (json format):**
```json
{
  "success": true,
  "paper_id": "2401.12345",
  "count": 3,
  "annotations": [
    {
      "id": "abc12345",
      "author": "researcher",
      "created_at": "2026-01-27T10:30:00Z",
      "type": "note",
      "content": "..."
    }
  ]
}
```

3. Display formatted annotations to user

---

## Scripts

### share_collection.py

**Location:** `skills/paper-collaborator/scripts/share_collection.py`

**Purpose:** Create shareable ZIP package with papers

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--output` | Yes | - | Output ZIP file path |
| `--paper-id` | No | All | Specific paper IDs |
| `--include-summaries` | No | false | Include summaries |
| `--include-annotations` | No | false | Include annotations |
| `--username` | No | $USER | Creator username |
| `--description` | No | None | Collection description |
| `--data-dir` | No | ./data | Data directory |

### import_collection.py

**Location:** `skills/paper-collaborator/scripts/import_collection.py`

**Purpose:** Import papers from ZIP package

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--input` | Yes | - | Input ZIP file path |
| `--overwrite` | No | false | Overwrite existing |
| `--data-dir` | No | ./data | Data directory |

### save_annotation.py

**Location:** `skills/paper-collaborator/scripts/save_annotation.py`

**Purpose:** Save annotation for a paper

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--paper-id` | Yes | - | arXiv paper ID |
| `--content` | Yes* | - | Annotation content |
| `--content-file` | Yes* | - | File with content |
| `--type` | No | note | Annotation type |
| `--username` | No | $USER | Author username |
| `--data-dir` | No | ./data | Data directory |

*Either `--content` or `--content-file` is required

### list_annotations.py

**Location:** `skills/paper-collaborator/scripts/list_annotations.py`

**Purpose:** List annotations for a paper

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--paper-id` | Yes | - | arXiv paper ID |
| `--format` | No | text | Output format |
| `--data-dir` | No | ./data | Data directory |

---

## Data Storage

### Collection Package Structure

```
collection.zip
├── manifest.json           # Package metadata
├── papers/
│   └── {paper_id}/
│       ├── metadata.json   # Paper metadata
│       ├── summary.md      # Optional summary
│       └── annotations/    # Optional annotations
│           └── *.json
└── index/
    └── papers.json         # Partial index
```

### Annotation Storage

```
data/papers/{paper_id}/annotations/
└── {username}_{timestamp}_{id}.json
```

**Annotation Schema:**
```json
{
  "id": "abc12345",
  "paper_id": "2401.12345",
  "author": "researcher",
  "created_at": "2026-01-27T10:30:00Z",
  "updated_at": "2026-01-27T10:30:00Z",
  "type": "note",
  "content": "Annotation text..."
}
```

---

## Error Handling

| Error Code | Message | Handling |
|------------|---------|----------|
| `INDEX_NOT_FOUND` | No papers collected | Prompt to run `/paper-collect` |
| `INVALID_PAPER_ID` | Invalid arXiv ID | Show format requirements |
| `PAPER_NOT_FOUND` | Paper not in collection | Prompt to collect paper |
| `FILE_NOT_FOUND` | Package not found | Check file path |
| `INVALID_PACKAGE` | Invalid ZIP package | Verify package integrity |
| `INVALID_ZIP` | Not a ZIP file | Check file format |
| `FILE_ERROR` | I/O error | Check permissions |
