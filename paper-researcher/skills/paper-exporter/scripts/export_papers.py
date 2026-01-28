#!/usr/bin/env python3
"""Export collected papers to various formats.

This script exports papers from the collection to Markdown, JSON, or CSV formats.
Papers can be filtered by ID, query, or date range.

Usage:
    python export_papers.py --format markdown --all --output ./exports
    python export_papers.py --format json --paper-id 2401.12345 --output ./exports
    python export_papers.py --format csv --query "attention" --output ./exports
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Constants
VALID_FORMATS = ("markdown", "json", "csv")

# arXiv ID validation pattern (defense against path traversal)
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")

# Timespan parsing pattern
TIMESPAN_PATTERN = re.compile(r"^(\d+)([dwmh])$")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("export_papers")


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
    """Validate export format.

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


def parse_timespan(timespan: str) -> timedelta:
    """Parse a timespan string into a timedelta.

    Supports formats:
        - Nd: N days (e.g., "7d" = 7 days)
        - Nw: N weeks (e.g., "1w" = 7 days)
        - Nm: N months (approximated as 30 days)
        - Nh: N hours (e.g., "24h" = 24 hours)

    Args:
        timespan: Timespan string to parse

    Returns:
        timedelta representing the timespan

    Raises:
        ValueError: If timespan format is invalid
    """
    timespan = timespan.strip().lower()

    match = TIMESPAN_PATTERN.match(timespan)
    if not match:
        raise ValueError(f"Invalid timespan format: '{timespan}'. Use: 1d, 7d, 14d, 30d, 1w, 24h")

    value = int(match.group(1))
    unit = match.group(2)

    if value <= 0:
        raise ValueError("Timespan value must be positive")

    if unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    elif unit == "m":
        return timedelta(days=value * 30)  # Approximate month
    elif unit == "h":
        return timedelta(hours=value)
    else:
        raise ValueError(f"Unknown time unit: {unit}")


def load_index(data_dir: Path) -> dict[str, Any]:
    """Load paper index from disk.

    Args:
        data_dir: Path to data directory

    Returns:
        Index dictionary with papers

    Raises:
        FileNotFoundError: If index file does not exist
        json.JSONDecodeError: If index file is not valid JSON
    """
    index_path = data_dir / "index" / "papers.json"

    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    with index_path.open(encoding="utf-8") as f:
        index: dict[str, Any] = json.load(f)

    logger.info("Loaded index with %d papers", len(index.get("papers", {})))
    return index


def load_paper(paper_id: str, data_dir: Path) -> dict[str, Any] | None:
    """Load full metadata for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Metadata dictionary or None if not available
    """
    if not validate_arxiv_id(paper_id):
        logger.warning("Invalid arXiv ID format: %s, skipping paper load", paper_id)
        return None

    metadata_path = data_dir / "papers" / paper_id / "metadata.json"

    if not metadata_path.exists():
        return None

    try:
        with metadata_path.open(encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to read metadata for %s: %s", paper_id, e)
        return None


def load_summary(paper_id: str, data_dir: Path) -> str | None:
    """Load summary content for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Summary content as string, or None if not available
    """
    if not validate_arxiv_id(paper_id):
        logger.warning("Invalid arXiv ID format: %s, skipping summary load", paper_id)
        return None

    summary_path = data_dir / "papers" / paper_id / "summary.md"

    if not summary_path.exists():
        return None

    try:
        return summary_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("Failed to read summary for %s: %s", paper_id, e)
        return None


def tokenize(text: str) -> list[str]:
    """Tokenize text into searchable terms.

    Converts to lowercase, removes punctuation, and splits into words.

    Args:
        text: Input text to tokenize

    Returns:
        List of lowercase word tokens
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation and split into words
    words = re.findall(r"\b[a-z0-9]+\b", text)

    # Filter out very short words (single chars except common ones)
    words = [w for w in words if len(w) > 1 or w in ("a", "i")]

    return words


def filter_papers(
    papers: dict[str, dict[str, Any]],
    query: str | None = None,
    since: datetime | None = None,
    paper_id: str | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Filter papers by query, date, or ID.

    Args:
        papers: Dictionary of paper_id -> paper data
        query: Optional search query
        since: Optional start datetime (papers collected after this)
        paper_id: Optional specific paper ID to filter

    Returns:
        List of (paper_id, paper_data) tuples matching filters
    """
    filtered: list[tuple[str, dict[str, Any]]] = []

    # Tokenize query if provided
    query_terms: list[str] = []
    if query:
        query_terms = tokenize(query)

    for pid, paper in papers.items():
        # Validate paper ID
        if not validate_arxiv_id(pid):
            logger.warning("Skipping paper with invalid ID: %s", pid)
            continue

        # Filter by specific paper ID
        if paper_id and pid != paper_id:
            continue

        # Filter by date
        if since:
            collected_at_str = paper.get("collected_at", "")
            if collected_at_str:
                try:
                    collected_at = datetime.fromisoformat(collected_at_str.replace("Z", "+00:00"))
                    if collected_at.tzinfo is None:
                        collected_at = collected_at.replace(tzinfo=timezone.utc)
                    if collected_at < since:
                        continue
                except ValueError:
                    logger.warning("Invalid collected_at for paper %s", pid)
                    continue

        # Filter by query
        if query_terms:
            # Search in title, abstract, and topics
            searchable = " ".join(
                [
                    paper.get("title", ""),
                    paper.get("abstract", ""),
                    " ".join(paper.get("topics", [])),
                ]
            ).lower()

            # Check if any query term matches
            if not any(term in searchable for term in query_terms):
                continue

        filtered.append((pid, paper))

    # Sort by collection date (newest first)
    filtered.sort(
        key=lambda x: x[1].get("collected_at", ""),
        reverse=True,
    )

    logger.info("Filtered to %d papers", len(filtered))
    return filtered


def export_markdown(
    papers: list[tuple[str, dict[str, Any]]],
    output_dir: Path,
    include_summary: bool,
    data_dir: Path,
) -> int:
    """Export papers to Markdown format.

    Args:
        papers: List of (paper_id, paper_data) tuples
        output_dir: Output directory path
        include_summary: Whether to include full summary
        data_dir: Data directory path

    Returns:
        Number of papers exported
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    exported = 0
    now = datetime.now(timezone.utc)

    for paper_id, paper in papers:
        # Load full metadata
        metadata = load_paper(paper_id, data_dir)
        if not metadata:
            metadata = paper

        lines: list[str] = []
        lines.append(f"# {metadata.get('title', 'Untitled')}")
        lines.append("")
        lines.append(f"**arXiv:** [{paper_id}](https://arxiv.org/abs/{paper_id})")

        authors = metadata.get("authors", [])
        if authors:
            lines.append(f"**Authors:** {', '.join(authors)}")

        published = metadata.get("published", "")
        if published:
            lines.append(f"**Published:** {published}")

        categories = metadata.get("categories", [])
        if categories:
            lines.append(f"**Categories:** {', '.join(categories)}")

        lines.append("")
        lines.append("## Abstract")
        lines.append("")
        lines.append(metadata.get("abstract", "*No abstract available*"))
        lines.append("")

        # Include summary if requested
        if include_summary:
            summary = load_summary(paper_id, data_dir)
            if summary:
                lines.append("## Summary")
                lines.append("")
                lines.append(summary)
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*Exported on {now.strftime('%Y-%m-%d')}*")
        lines.append("")

        content = "\n".join(lines)

        # Write file atomically
        output_path = output_dir / f"paper_{paper_id}.md"
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_dir,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            tmp_path.replace(output_path)
            exported += 1
        finally:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    logger.info("Exported %d papers as Markdown", exported)
    return exported


def export_json(
    papers: list[tuple[str, dict[str, Any]]],
    output_dir: Path,
    include_summary: bool,
    data_dir: Path,
) -> int:
    """Export papers to JSON format.

    Args:
        papers: List of (paper_id, paper_data) tuples
        output_dir: Output directory path
        include_summary: Whether to include full summary
        data_dir: Data directory path

    Returns:
        Number of papers exported
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    export_data: list[dict[str, Any]] = []

    for paper_id, paper in papers:
        # Load full metadata
        metadata = load_paper(paper_id, data_dir)
        if not metadata:
            metadata = dict(paper)
            metadata["id"] = paper_id
        else:
            metadata = dict(metadata)  # Copy to avoid mutation

        # Include summary if requested
        if include_summary:
            summary = load_summary(paper_id, data_dir)
            if summary:
                metadata["summary_content"] = summary

        export_data.append(metadata)

    # Build output structure
    output_content: dict[str, Any] = {
        "exported_at": now.isoformat(),
        "count": len(export_data),
        "papers": export_data,
    }

    # Write collection file
    output_path = output_dir / "papers.json"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_dir,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(output_content, tmp, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp.name)
        tmp_path.replace(output_path)
        logger.info("Exported %d papers as JSON", len(export_data))
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    return len(export_data)


def export_csv(
    papers: list[tuple[str, dict[str, Any]]],
    output_dir: Path,
    data_dir: Path,
) -> int:
    """Export papers to CSV format.

    Args:
        papers: List of (paper_id, paper_data) tuples
        output_dir: Output directory path
        data_dir: Data directory path

    Returns:
        Number of papers exported
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV headers
    fieldnames = [
        "id",
        "title",
        "authors",
        "published",
        "categories",
        "has_summary",
        "pdf_url",
        "collected_at",
    ]

    rows: list[dict[str, str]] = []

    for paper_id, paper in papers:
        # Load full metadata
        metadata = load_paper(paper_id, data_dir)
        if not metadata:
            metadata = paper

        row = {
            "id": paper_id,
            "title": metadata.get("title", ""),
            "authors": "; ".join(metadata.get("authors", [])),
            "published": metadata.get("published", ""),
            "categories": "; ".join(metadata.get("categories", [])),
            "has_summary": str(metadata.get("has_summary", False)).lower(),
            "pdf_url": metadata.get("pdf_url", ""),
            "collected_at": metadata.get("collected_at", ""),
        }
        rows.append(row)

    # Write CSV file
    output_path = output_dir / "papers.csv"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_dir,
            suffix=".tmp",
            delete=False,
            newline="",
        ) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)
            tmp_path = Path(tmp.name)
        tmp_path.replace(output_path)
        logger.info("Exported %d papers as CSV", len(rows))
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    return len(rows)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Export collected papers to various formats")
    parser.add_argument(
        "--format",
        type=validate_format,
        required=True,
        help=f"Export format: {', '.join(VALID_FORMATS)}",
    )

    # Selection arguments (mutually exclusive group)
    selection_group = parser.add_mutually_exclusive_group(required=True)
    selection_group.add_argument(
        "--paper-id",
        help="Export single paper by arXiv ID",
    )
    selection_group.add_argument(
        "--all",
        action="store_true",
        help="Export all papers in collection",
    )
    selection_group.add_argument(
        "--query",
        help="Export papers matching search query",
    )

    parser.add_argument(
        "--since",
        help="Filter papers collected since (e.g., 7d, 30d, 1w)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (default: data/exports/{format}/)",
    )
    parser.add_argument(
        "--include-summary",
        action="store_true",
        help="Include full summary content (Markdown and JSON only)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )

    args = parser.parse_args()

    try:
        # Validate paper ID if provided
        if args.paper_id and not validate_arxiv_id(args.paper_id):
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

        # Parse date filter if provided
        since_dt: datetime | None = None
        if args.since:
            delta = parse_timespan(args.since)
            since_dt = datetime.now(timezone.utc) - delta

        # Load index
        index = load_index(args.data_dir)
        papers = index.get("papers", {})

        if not papers:
            output: dict[str, Any] = {
                "success": True,
                "message": "No papers in collection. Run /paper-collect first.",
                "export_count": 0,
                "output_path": None,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0

        # Filter papers
        filtered = filter_papers(
            papers,
            query=args.query,
            since=since_dt,
            paper_id=args.paper_id,
        )

        if not filtered:
            msg = "No papers match the specified criteria."
            if args.paper_id:
                msg = f"Paper {args.paper_id} not found in collection."
            elif args.query:
                msg = f"No papers match query '{args.query}'."
            elif args.since:
                msg = f"No papers collected in the last {args.since}."

            output = {
                "success": True,
                "message": msg,
                "export_count": 0,
                "output_path": None,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0

        # Determine output directory
        if args.output:
            output_dir = args.output
        else:
            output_dir = args.data_dir / "exports" / args.format
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export based on format
        export_count = 0
        if args.format == "markdown":
            export_count = export_markdown(
                filtered, output_dir, args.include_summary, args.data_dir
            )
        elif args.format == "json":
            export_count = export_json(filtered, output_dir, args.include_summary, args.data_dir)
        elif args.format == "csv":
            export_count = export_csv(filtered, output_dir, args.data_dir)

        # Build output
        output = {
            "success": True,
            "message": f"Exported {export_count} papers as {args.format.upper()}.",
            "export_count": export_count,
            "format": args.format,
            "output_path": str(output_dir),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    except FileNotFoundError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "INDEX_NOT_FOUND",
                "message": "No papers collected yet. Run /paper-collect first.",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    except ValueError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "INVALID_ARGUMENT",
                "message": str(e),
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    except json.JSONDecodeError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "INVALID_INDEX",
                "message": "Paper index is corrupted",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    except OSError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "FILE_ERROR",
                "message": "Failed to write export files",
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
