#!/usr/bin/env python3
"""List annotations for a paper.

This script lists all annotations for a specific paper, with options
for different output formats.

Usage:
    python list_annotations.py --paper-id 2401.12345
    python list_annotations.py --paper-id 2401.12345 --format json
    python list_annotations.py --paper-id 2401.12345 --format markdown
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Constants
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")
VALID_FORMATS = ("json", "markdown", "text")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("list_annotations")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    This is a security check to prevent path traversal attacks.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format (YYMM.NNNNN), False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


def validate_format(format_str: str) -> str:
    """Validate output format.

    Args:
        format_str: Format string to validate

    Returns:
        Validated lowercase format string

    Raises:
        argparse.ArgumentTypeError: If format is invalid
    """
    format_lower = format_str.lower()
    if format_lower not in VALID_FORMATS:
        raise argparse.ArgumentTypeError(
            f"Invalid format '{format_str}'. Valid formats: {', '.join(VALID_FORMATS)}"
        )
    return format_lower


def load_annotations(paper_id: str, data_dir: Path) -> list[dict[str, Any]]:
    """Load all annotations for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        List of annotation dictionaries, sorted by creation date
    """
    if not validate_arxiv_id(paper_id):
        return []

    annotations_dir = data_dir / "papers" / paper_id / "annotations"

    if not annotations_dir.exists():
        return []

    annotations: list[dict[str, Any]] = []

    for annotation_file in annotations_dir.glob("*.json"):
        try:
            with annotation_file.open(encoding="utf-8") as f:
                annotation = json.load(f)
                annotations.append(annotation)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to read annotation %s: %s", annotation_file, e)
            continue

    # Sort by creation date (newest first)
    annotations.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )

    return annotations


def format_annotation_text(annotation: dict[str, Any]) -> str:
    """Format a single annotation as plain text.

    Args:
        annotation: Annotation dictionary

    Returns:
        Formatted text string
    """
    lines = [
        f"[{annotation.get('type', 'note').upper()}] by {annotation.get('author', 'unknown')}",
        f"Created: {annotation.get('created_at', 'unknown')}",
        "",
        annotation.get("content", ""),
        "",
        "-" * 40,
    ]
    return "\n".join(lines)


def format_annotation_markdown(annotation: dict[str, Any]) -> str:
    """Format a single annotation as Markdown.

    Args:
        annotation: Annotation dictionary

    Returns:
        Formatted Markdown string
    """
    ann_type = annotation.get("type", "note").capitalize()
    author = annotation.get("author", "unknown")
    created_at = annotation.get("created_at", "unknown")
    content = annotation.get("content", "")

    # Parse and format date if valid
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        date_str = created_at

    lines = [
        f"### {ann_type}",
        "",
        f"**Author:** {author}  ",
        f"**Created:** {date_str}",
        "",
        content,
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def format_annotations(
    annotations: list[dict[str, Any]],
    paper_id: str,
    output_format: str,
) -> str:
    """Format annotations for output.

    Args:
        annotations: List of annotation dictionaries
        paper_id: Paper ID
        output_format: Output format (json, markdown, text)

    Returns:
        Formatted output string
    """
    if output_format == "json":
        output: dict[str, Any] = {
            "paper_id": paper_id,
            "count": len(annotations),
            "annotations": annotations,
        }
        return json.dumps(output, indent=2, ensure_ascii=False)

    elif output_format == "markdown":
        lines = [
            f"# Annotations for Paper {paper_id}",
            "",
            f"**Total annotations:** {len(annotations)}",
            "",
            "---",
            "",
        ]
        for annotation in annotations:
            lines.append(format_annotation_markdown(annotation))
        return "\n".join(lines)

    else:  # text
        lines = [
            f"Annotations for Paper {paper_id}",
            f"Total: {len(annotations)}",
            "=" * 40,
            "",
        ]
        for annotation in annotations:
            lines.append(format_annotation_text(annotation))
        return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="List annotations for a paper")
    parser.add_argument(
        "--paper-id",
        required=True,
        help="arXiv paper ID",
    )
    parser.add_argument(
        "--format",
        type=validate_format,
        default="text",
        dest="output_format",
        help=f"Output format: {', '.join(VALID_FORMATS)} (default: text)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )

    args = parser.parse_args()

    try:
        # Validate paper ID
        if not validate_arxiv_id(args.paper_id):
            error_output: dict[str, Any] = {
                "success": False,
                "error": {
                    "code": "INVALID_PAPER_ID",
                    "message": f"Invalid arXiv ID format: {args.paper_id}",
                    "details": "arXiv ID must be in format YYMM.NNNNN (e.g., 2401.12345)",
                },
            }
            print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        # Check paper exists
        paper_dir = args.data_dir / "papers" / args.paper_id
        if not paper_dir.exists():
            error_output = {
                "success": False,
                "error": {
                    "code": "PAPER_NOT_FOUND",
                    "message": f"Paper {args.paper_id} not found in collection",
                    "details": "Ensure the paper exists in your collection",
                },
            }
            print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        # Load annotations
        annotations = load_annotations(args.paper_id, args.data_dir)

        if not annotations:
            if args.output_format == "json":
                output: dict[str, Any] = {
                    "success": True,
                    "paper_id": args.paper_id,
                    "count": 0,
                    "annotations": [],
                    "message": "No annotations found for this paper.",
                }
                print(json.dumps(output, indent=2, ensure_ascii=False))
            else:
                print(f"No annotations found for paper {args.paper_id}.")
            return 0

        # Format and print output
        formatted = format_annotations(annotations, args.paper_id, args.output_format)

        if args.output_format == "json":
            # Wrap in success response
            result = json.loads(formatted)
            output = {
                "success": True,
                **result,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            print(formatted)

        return 0

    except OSError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "FILE_ERROR",
                "message": "Failed to read annotations",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    except Exception as e:
        error_output = {
            "success": False,
            "error": {
                "code": "UNKNOWN_ERROR",
                "message": "An unexpected error occurred",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
