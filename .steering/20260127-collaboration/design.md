# Design: Collaboration Feature

**Feature:** F8: Collaboration
**Priority:** P2 (Future)
**Date:** 2026-01-27
**Status:** Draft

---

## Overview

This design describes the implementation approach for sharing collections and collaborative annotation in the paper-researcher plugin.

---

## Architecture

### Component Overview

```
User A (share)                    User B (import)
     |                                  |
     v                                  v
/paper-share                    /paper-import
     |                                  |
     v                                  v
share_collection.py             import_collection.py
     |                                  |
     v                                  v
collection.zip -----------------> merge into data/
```

### New Components

1. **skills/paper-sharer/** - Share collection skill
   - `scripts/share_collection.py` - Export collection to ZIP

2. **skills/paper-annotator/** - Annotation skill
   - `scripts/save_annotation.py` - Save annotation for paper
   - `scripts/list_annotations.py` - List annotations for paper

3. **skills/paper-importer/** - Import shared collection skill
   - `scripts/import_collection.py` - Import ZIP and merge

4. **commands/**
   - `paper-share.md` - Share collection command
   - `paper-import.md` - Import collection command
   - `paper-annotate.md` - Add annotation command

---

## Data Model

### Collection Package Format (ZIP)

```
collection.zip
├── manifest.json          # Package metadata
├── papers/
│   └── {paper_id}/
│       ├── metadata.json
│       ├── summary.md     # Optional
│       └── annotations/   # Optional
│           └── {author}_{timestamp}.md
└── index/
    └── papers.json
```

### Manifest Schema

```json
{
  "version": "1.0",
  "created_at": "2026-01-27T10:00:00Z",
  "created_by": "username",
  "paper_count": 12,
  "includes_summaries": true,
  "includes_annotations": true
}
```

### Annotation Schema

```
data/papers/{paper_id}/annotations/{author}_{timestamp}.md
```

```markdown
# Annotation

**Author:** username
**Created:** 2026-01-27T10:00:00Z
**Paper:** {paper_id}

---

[Annotation content]
```

---

## Workflows

### Share Collection

1. User runs `/paper-share --output collection.zip`
2. Skill invokes `share_collection.py`
3. Script creates ZIP with manifest, papers, and index
4. User shares ZIP file with team

### Import Collection

1. User runs `/paper-import collection.zip`
2. Skill invokes `import_collection.py`
3. Script extracts ZIP, validates manifest
4. Script merges papers into local collection
5. Duplicates are skipped, new papers added
6. Annotations merged with author attribution

### Add Annotation

1. User runs `/paper-annotate <paper-id>`
2. Skill prompts for annotation content
3. Script saves annotation with username and timestamp
4. Paper metadata updated with annotation count

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| Invalid ZIP format | Report error, abort import |
| Missing manifest | Report error, abort import |
| Duplicate paper | Skip, keep local version |
| Annotation conflict | Keep both, append suffix |
| Paper not found | Report error for annotation |

---

## Security Considerations

- Validate all paths in ZIP to prevent traversal attacks
- Sanitize author names to prevent path injection
- Validate paper IDs before annotation operations

---
