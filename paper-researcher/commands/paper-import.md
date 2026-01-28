---
name: paper-import
description: "Import shared paper collection from ZIP package."
allowed-tools: Read, Write, Bash, Skill
---

# Paper Import Command

Import a paper collection shared by a team member.

## Usage

```
/paper-researcher:paper-import <input-file> [--overwrite]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<input-file>` | Yes | - | Path to ZIP package to import |
| `--overwrite` | No | false | Overwrite existing papers (default: skip) |

## Examples

**Import shared collection:**
```
/paper-researcher:paper-import collection.zip
```

**Import with overwrite:**
```
/paper-researcher:paper-import team_papers.zip --overwrite
```

## Workflow

1. Invoke `paper-collaborator` skill with import operation
2. Skill validates ZIP file path
3. Skill calls `import_collection.py` script
4. Script validates package (manifest, paths)
5. Script merges papers into local collection
6. Display import summary

## Output

```
Imported 10 papers from collection.

Summary:
- Imported: 10 papers
- Skipped: 2 papers (already exist)
- Annotations: 5 imported

Package info:
- Created by: researcher@team
- Created at: 2026-01-27
- Description: LLM research papers Q1 2026
```

## Security

The import process validates:
- ZIP file integrity
- Path traversal prevention (no `..` in paths)
- Paper ID format validation
- Maximum file size limits

## Error Handling

| Error | Message | Action |
|-------|---------|--------|
| File not found | "Package file not found" | Check file path |
| Invalid ZIP | "Not a valid ZIP archive" | Verify file is not corrupted |
| Invalid manifest | "Invalid or corrupted package" | Package may be corrupted |
| Path traversal | "Invalid path in package" | Package contains malicious paths |

## Related Commands

- `/paper-researcher:paper-share` - Create a shareable package
- `/paper-researcher:paper-collect` - Collect new papers
- `/paper-researcher:paper-search` - Search imported papers
