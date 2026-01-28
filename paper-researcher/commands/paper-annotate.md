---
name: paper-annotate
description: "Add annotation to a paper in your collection."
allowed-tools: Read, Write, Bash, Skill
---

# Paper Annotate Command

Add annotations, notes, or comments to papers in your collection.

## Usage

```
/paper-researcher:paper-annotate <paper-id> [--type <type>]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<paper-id>` | Yes | - | arXiv paper ID to annotate |
| `--type` | No | note | Annotation type: note, highlight, question, comment |
| `--list` | No | false | List existing annotations instead of adding |

## Examples

**Add a note:**
```
/paper-researcher:paper-annotate 2401.12345
```
Then provide your annotation content when prompted.

**Add a question:**
```
/paper-researcher:paper-annotate 2401.12345 --type question
```

**List annotations:**
```
/paper-researcher:paper-annotate 2401.12345 --list
```

## Annotation Types

| Type | Description |
|------|-------------|
| `note` | General notes about the paper |
| `highlight` | Key findings or important sections |
| `question` | Questions for discussion |
| `comment` | Comments for team members |

## Workflow

### Adding Annotation

1. Invoke `paper-collaborator` skill with annotate operation
2. Skill validates paper ID
3. Prompt user for annotation content
4. Skill calls `save_annotation.py` script
5. Script saves annotation with timestamp and author
6. Display confirmation

### Listing Annotations

1. Invoke `paper-collaborator` skill with list operation
2. Skill calls `list_annotations.py` script
3. Display formatted annotations

## Output

**Adding annotation:**
```
Saved annotation for paper 2401.12345.

Annotation ID: abc12345
Type: note
Author: researcher
Created: 2026-01-27 10:30:00
```

**Listing annotations:**
```
Annotations for Paper 2401.12345
Total: 3

---

### Note
**Author:** researcher
**Created:** 2026-01-27 10:30

This paper introduces a novel approach to...

---

### Question
**Author:** teammate
**Created:** 2026-01-26 15:00

How does this compare to previous work on...
```

## Error Handling

| Error | Message | Action |
|-------|---------|--------|
| Paper not found | "Paper not found in collection" | Verify paper ID |
| Invalid paper ID | "Invalid arXiv ID format" | Check paper ID format |
| Empty content | "Annotation content is empty" | Provide annotation text |

## Related Commands

- `/paper-researcher:paper-share` - Share collection with annotations
- `/paper-researcher:paper-summarize` - Generate AI summary
- `/paper-researcher:paper-search` - Find papers to annotate
