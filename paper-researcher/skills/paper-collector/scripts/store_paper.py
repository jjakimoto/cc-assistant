#!/usr/bin/env python3
"""Store paper metadata to local filesystem.

This script reads paper metadata from a JSON file (output of fetch_arxiv.py)
and stores each paper in the data directory. It maintains an index for quick
lookup and handles duplicate detection.

Usage:
    python store_paper.py --input papers.json --data-dir ./data
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Constants
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("store_paper")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format, False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


def load_index(data_dir: Path) -> dict[str, Any]:
    """Load the paper index from disk.

    Args:
        data_dir: Data directory path

    Returns:
        Index dictionary with paper metadata
    """
    index_path = data_dir / "index" / "papers.json"

    if not index_path.exists():
        logger.info("No existing index found, creating new one")
        return {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "papers": {},
        }

    try:
        with index_path.open("r", encoding="utf-8") as f:
            index: dict[str, Any] = json.load(f)
            logger.info("Loaded index with %d papers", len(index.get("papers", {})))
            return index
    except json.JSONDecodeError as e:
        logger.warning("Corrupted index file, creating new one: %s", e)
        return {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "papers": {},
        }


def save_paper(paper: dict[str, Any], data_dir: Path, topic: str | None = None) -> bool:
    """Save paper metadata to disk.

    Args:
        paper: Paper metadata dictionary
        data_dir: Data directory path
        topic: Optional topic tag to add

    Returns:
        True if paper was saved (new), False if skipped (duplicate)
    """
    paper_id = paper.get("id", "")
    if not paper_id:
        logger.warning("Paper has no ID, skipping")
        return False

    # Validate arXiv ID format to prevent path traversal
    if not validate_arxiv_id(paper_id):
        logger.warning("Invalid arXiv ID format: %s, skipping", paper_id)
        return False

    paper_dir = data_dir / "papers" / paper_id
    metadata_path = paper_dir / "metadata.json"

    # Check for duplicate
    if metadata_path.exists():
        logger.debug("Paper %s already exists, skipping", paper_id)
        return False

    # Create paper directory
    paper_dir.mkdir(parents=True, exist_ok=True)

    # Add collection metadata
    paper_with_metadata: dict[str, Any] = {
        **paper,
        "collected_at": datetime.now().isoformat(),
        "topics": [topic] if topic else [],
        "has_summary": False,
    }

    # Write metadata
    try:
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(paper_with_metadata, f, indent=2, ensure_ascii=False)
        logger.debug("Saved paper %s to %s", paper_id, paper_dir)
        return True
    except OSError as e:
        logger.error("Failed to save paper %s: %s", paper_id, e)
        # Clean up partial write
        if paper_dir.exists():
            shutil.rmtree(paper_dir)
        raise


def update_index(
    index: dict[str, Any],
    papers: list[dict[str, Any]],
    data_dir: Path,
    saved_ids: set[str],
) -> None:
    """Update the paper index with new papers.

    This function performs an atomic write to prevent index corruption.

    Args:
        index: Existing index dictionary
        papers: List of paper metadata
        data_dir: Data directory path
        saved_ids: Set of paper IDs that were newly saved
    """
    # Ensure index directory exists
    index_dir = data_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)

    index_path = index_dir / "papers.json"

    # Add new papers to index
    for paper in papers:
        paper_id = paper.get("id", "")
        if not paper_id:
            continue

        # Only add if not already in index
        if paper_id not in index.get("papers", {}):
            index.setdefault("papers", {})[paper_id] = {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", "")[:500],  # Truncate for index
                "topics": paper.get("topics", []),
                "collected_at": datetime.now().isoformat(),
                "has_summary": False,
            }

    # Update timestamp
    index["updated_at"] = datetime.now().isoformat()

    # Atomic write using temp file
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=index_dir,
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            json.dump(index, tmp, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp.name)

        # Atomic rename
        tmp_path.replace(index_path)
        logger.info("Updated index with %d papers", len(index.get("papers", {})))

    except OSError as e:
        logger.error("Failed to update index: %s", e)
        # Clean up temp file if it exists
        if "tmp_path" in locals() and tmp_path.exists():
            tmp_path.unlink()
        raise


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Store paper metadata to local filesystem")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input JSON file from fetch_arxiv.py",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )

    args = parser.parse_args()

    # Validate input file
    if not args.input.exists():
        logger.error("Input file not found: %s", args.input)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "INPUT_NOT_FOUND",
                        "message": f"Input file not found: {args.input}",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    try:
        # Load input papers
        with args.input.open("r", encoding="utf-8") as f:
            input_data = json.load(f)

        if not input_data.get("success"):
            logger.error("Input file indicates failure, aborting")
            return 1

        papers: list[dict[str, Any]] = input_data.get("papers", [])
        query = input_data.get("query", "")

        logger.info("Processing %d papers from input", len(papers))

        # Ensure data directory exists
        args.data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing index
        index = load_index(args.data_dir)

        # Save papers
        saved_count = 0
        duplicate_count = 0
        saved_ids: set[str] = set()

        for paper in papers:
            try:
                if save_paper(paper, args.data_dir, topic=query):
                    saved_count += 1
                    saved_ids.add(paper.get("id", ""))
                else:
                    duplicate_count += 1
            except OSError as e:
                logger.error("Failed to save paper: %s", e)
                continue

        # Update index
        update_index(index, papers, args.data_dir, saved_ids)

        # Report results
        result_msg = f"Stored {saved_count} new papers"
        if duplicate_count > 0:
            result_msg += f" ({duplicate_count} duplicates skipped)"

        logger.info(result_msg)
        print(result_msg)

        # Output JSON result
        output: dict[str, Any] = {
            "success": True,
            "saved": saved_count,
            "duplicates": duplicate_count,
            "total": len(papers),
        }
        print(json.dumps(output, indent=2))

        return 0

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in input file: %s", e)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_JSON",
                        "message": f"Invalid JSON in input file: {e}",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    except OSError as e:
        logger.error("File I/O error: %s", e)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "IO_ERROR",
                        "message": f"File I/O error: {e}",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
