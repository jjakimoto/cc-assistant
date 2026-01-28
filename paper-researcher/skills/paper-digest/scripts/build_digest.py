#!/usr/bin/env python3
"""Generate digest of recently collected papers.

This script creates a dated markdown digest of papers collected within
a specified time range, grouped by topic with summary snippets.

Usage:
    python build_digest.py --since 7d --data-dir ./data --output data/digests/2026-01-27.md
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Constants
DEFAULT_SINCE = "7d"
DEFAULT_SNIPPET_LENGTH = 200
UNCATEGORIZED_TOPIC = "Uncategorized"

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
logger = logging.getLogger("build_digest")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    This is a security check to prevent path traversal attacks.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format (YYMM.NNNNN), False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


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
        raise ValueError(
            f"Invalid timespan format: '{timespan}'. Use: 1d, 7d, 14d, 30d, 1w, 24h"
        )

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


def load_metadata(paper_id: str, data_dir: Path) -> dict[str, Any] | None:
    """Load full metadata for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Metadata dictionary or None if not available
    """
    if not validate_arxiv_id(paper_id):
        logger.warning("Invalid arXiv ID format: %s, skipping metadata load", paper_id)
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


def extract_snippet(summary: str, max_length: int = DEFAULT_SNIPPET_LENGTH) -> str:
    """Extract a snippet from a summary.

    Extracts the Problem section or first paragraph of content.

    Args:
        summary: Full summary markdown content
        max_length: Maximum length of snippet

    Returns:
        Extracted snippet text
    """
    if not summary:
        return ""

    # Try to extract the Problem section
    problem_match = re.search(r"## Problem\s*\n(.+?)(?:\n##|\Z)", summary, re.DOTALL)
    if problem_match:
        snippet = problem_match.group(1).strip()
        if len(snippet) > max_length:
            snippet = snippet[:max_length].rsplit(" ", 1)[0] + "..."
        return snippet

    # Fallback: extract first non-header paragraph
    lines = summary.split("\n")
    content_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("**"):
            content_lines.append(line)
            if len(" ".join(content_lines)) >= max_length:
                break

    snippet = " ".join(content_lines)
    if len(snippet) > max_length:
        snippet = snippet[:max_length].rsplit(" ", 1)[0] + "..."

    return snippet


def filter_papers(
    papers: dict[str, dict[str, Any]],
    since: datetime,
    until: datetime,
) -> list[tuple[str, dict[str, Any]]]:
    """Filter papers by collection date.

    Args:
        papers: Dictionary of paper_id -> paper data
        since: Start datetime (inclusive)
        until: End datetime (inclusive)

    Returns:
        List of (paper_id, paper_data) tuples for papers in the date range
    """
    filtered: list[tuple[str, dict[str, Any]]] = []

    for paper_id, paper in papers.items():
        if not validate_arxiv_id(paper_id):
            logger.warning("Skipping paper with invalid ID: %s", paper_id)
            continue

        collected_at_str = paper.get("collected_at", "")
        if not collected_at_str:
            continue

        try:
            # Parse ISO format datetime
            collected_at = datetime.fromisoformat(collected_at_str.replace("Z", "+00:00"))
            # Make naive datetime timezone-aware if needed
            if collected_at.tzinfo is None:
                collected_at = collected_at.replace(tzinfo=timezone.utc)

            if since <= collected_at <= until:
                filtered.append((paper_id, paper))
        except ValueError as e:
            logger.warning("Invalid collected_at for paper %s: %s", paper_id, e)
            continue

    # Sort by collection date (newest first)
    filtered.sort(
        key=lambda x: x[1].get("collected_at", ""),
        reverse=True,
    )

    logger.info("Filtered to %d papers in date range", len(filtered))
    return filtered


def group_by_topic(
    papers: list[tuple[str, dict[str, Any]]],
    data_dir: Path,
) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    """Group papers by topic.

    Papers without topics are grouped under "Uncategorized".
    Papers with multiple topics appear in each group.

    Args:
        papers: List of (paper_id, paper_data) tuples
        data_dir: Path to data directory (for loading full metadata)

    Returns:
        Dictionary of topic -> list of (paper_id, paper_data) tuples
    """
    groups: dict[str, list[tuple[str, dict[str, Any]]]] = {}

    for paper_id, paper in papers:
        # Get topics from index first
        topics = paper.get("topics", [])

        # If no topics in index, try loading full metadata
        if not topics:
            metadata = load_metadata(paper_id, data_dir)
            if metadata:
                topics = metadata.get("topics", [])
                # If still no topics, use arXiv categories as fallback
                if not topics:
                    categories = metadata.get("categories", [])
                    if categories:
                        topics = categories

        # If still no topics, use Uncategorized
        if not topics:
            topics = [UNCATEGORIZED_TOPIC]

        # Add paper to each topic group
        for topic in topics:
            if topic not in groups:
                groups[topic] = []
            groups[topic].append((paper_id, paper))

    # Sort groups: put Uncategorized last
    sorted_groups: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for topic in sorted(groups.keys()):
        if topic != UNCATEGORIZED_TOPIC:
            sorted_groups[topic] = groups[topic]
    if UNCATEGORIZED_TOPIC in groups:
        sorted_groups[UNCATEGORIZED_TOPIC] = groups[UNCATEGORIZED_TOPIC]

    logger.info("Grouped papers into %d topics", len(sorted_groups))
    return sorted_groups


def build_digest_content(
    grouped_papers: dict[str, list[tuple[str, dict[str, Any]]]],
    since: datetime,
    until: datetime,
    data_dir: Path,
) -> str:
    """Build the markdown content for a digest.

    Args:
        grouped_papers: Papers grouped by topic
        since: Start datetime
        until: End datetime
        data_dir: Path to data directory

    Returns:
        Markdown content string
    """
    # Count total unique papers
    all_paper_ids = set()
    papers_with_summary = 0
    for paper_list in grouped_papers.values():
        for paper_id, paper in paper_list:
            if paper_id not in all_paper_ids:
                all_paper_ids.add(paper_id)
                if paper.get("has_summary"):
                    papers_with_summary += 1

    total_papers = len(all_paper_ids)

    lines: list[str] = []

    # Header
    lines.append("# Research Paper Digest")
    lines.append("")
    lines.append(f"**Generated:** {until.strftime('%Y-%m-%d')}")
    lines.append(
        f"**Period:** {since.strftime('%Y-%m-%d')} to {until.strftime('%Y-%m-%d')}"
    )
    lines.append(f"**Papers:** {total_papers} ({papers_with_summary} with summaries)")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not grouped_papers:
        lines.append("*No papers collected in this time period.*")
        lines.append("")
    else:
        for topic, paper_list in grouped_papers.items():
            lines.append(f"## {topic}")
            lines.append("")

            for paper_id, paper in paper_list:
                title = paper.get("title", "Untitled")
                authors = paper.get("authors", [])
                authors_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    authors_str += " et al."

                # Load metadata for published date
                metadata = load_metadata(paper_id, data_dir)
                published = ""
                if metadata:
                    published = metadata.get("published", "")

                lines.append(f"### [{paper_id}] {title}")
                lines.append(f"**Authors:** {authors_str}")
                if published:
                    lines.append(f"**Published:** {published}")
                lines.append("")

                # Load and add snippet
                if paper.get("has_summary"):
                    summary = load_summary(paper_id, data_dir)
                    if summary:
                        snippet = extract_snippet(summary)
                        if snippet:
                            lines.append(f"> {snippet}")
                            lines.append("")
                    lines.append(f"[View Full Summary](../papers/{paper_id}/summary.md)")
                else:
                    # Use abstract as fallback
                    abstract = paper.get("abstract", "")
                    if abstract:
                        snippet = abstract[:DEFAULT_SNIPPET_LENGTH]
                        if len(abstract) > DEFAULT_SNIPPET_LENGTH:
                            snippet = snippet.rsplit(" ", 1)[0] + "..."
                        lines.append(f"> {snippet}")
                        lines.append("")
                    lines.append("*Summary not available*")

                lines.append("")

            lines.append("---")
            lines.append("")

    # Footer
    lines.append("*Generated by Paper Researcher Plugin*")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate digest of recently collected papers"
    )
    parser.add_argument(
        "--since",
        default=DEFAULT_SINCE,
        help=f"Time range for papers (e.g., 1d, 7d, 14d, 30d, 1w). Default: {DEFAULT_SINCE}",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: data/digests/{date}.md)",
    )

    args = parser.parse_args()

    try:
        # Parse timespan
        delta = parse_timespan(args.since)

        # Calculate date range
        until = datetime.now(timezone.utc)
        since = until - delta

        logger.info(
            "Generating digest for papers from %s to %s",
            since.strftime("%Y-%m-%d"),
            until.strftime("%Y-%m-%d"),
        )

        # Load index
        index = load_index(args.data_dir)
        papers = index.get("papers", {})

        if not papers:
            output: dict[str, Any] = {
                "success": True,
                "message": "No papers in collection. Run /paper-collect first.",
                "papers_count": 0,
                "output_path": None,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0

        # Filter papers by date
        filtered = filter_papers(papers, since, until)

        if not filtered:
            output = {
                "success": True,
                "message": f"No papers collected in the last {args.since}.",
                "papers_count": 0,
                "output_path": None,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0

        # Group by topic
        grouped = group_by_topic(filtered, args.data_dir)

        # Build digest content
        content = build_digest_content(grouped, since, until, args.data_dir)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            digests_dir = args.data_dir / "digests"
            digests_dir.mkdir(parents=True, exist_ok=True)
            output_path = digests_dir / f"{until.strftime('%Y-%m-%d')}.md"

        # Write digest atomically
        output_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_path.parent,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            tmp_path.replace(output_path)
            logger.info("Wrote digest to %s", output_path)
        finally:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

        # Build output
        output = {
            "success": True,
            "message": f"Digest generated with {len(filtered)} papers.",
            "papers_count": len(filtered),
            "topics_count": len(grouped),
            "output_path": str(output_path),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    except FileNotFoundError as e:
        error_output: dict[str, Any] = {
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
                "message": "Failed to write digest file",
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
