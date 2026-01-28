---
name: paper-share
description: "Share paper collection as a portable ZIP package for collaboration."
allowed-tools: Read, Write, Bash, Skill
---

# Paper Share Command

Share your paper collection with team members by creating a portable ZIP package.

## Usage

```
/paper-researcher:paper-share [--paper-id <id>] [--include-summaries] [--include-annotations] [--description "text"]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--paper-id` | No | All papers | Specific paper ID(s) to share (can be repeated) |
| `--include-summaries` | No | false | Include AI-generated summaries |
| `--include-annotations` | No | false | Include annotations |
| `--description` | No | None | Description for the collection |
| `--output` | No | `./collection.zip` | Output file path |

## Examples

**Share entire collection:**
```
/paper-researcher:paper-share
```

**Share specific papers with summaries:**
```
/paper-researcher:paper-share --paper-id 2401.12345 --paper-id 2401.12346 --include-summaries
```

**Share with description:**
```
/paper-researcher:paper-share --include-summaries --include-annotations --description "LLM research papers Q1 2026"
```

## Workflow

1. Invoke `paper-collaborator` skill with share operation
2. Skill validates arguments and paper IDs
3. Skill calls `share_collection.py` script
4. Script creates ZIP with manifest, papers, and optional content
5. Display package path and summary

## Output

```
Created collection package with 12 papers.
Package: /path/to/collection.zip

Included:
- 12 paper metadata files
- 10 summaries
- 5 annotations

Share this file with team members who can import it with:
/paper-researcher:paper-import --input collection.zip
```

## Error Handling

| Error | Message | Action |
|-------|---------|--------|
| No papers collected | "No papers to share" | Run `/paper-collect` first |
| Invalid paper ID | "Invalid arXiv ID format" | Check paper ID format |
| File write error | "Failed to create package" | Check disk space and permissions |

## Related Commands

- `/paper-researcher:paper-import` - Import a shared collection
- `/paper-researcher:paper-annotate` - Add annotation to a paper
- `/paper-researcher:paper-export` - Export to other formats
