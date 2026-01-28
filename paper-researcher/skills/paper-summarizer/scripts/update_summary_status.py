#!/usr/bin/env python3
"""Update paper summary status in metadata and index.

This script updates the `has_summary` field in both the paper's metadata.json
and the global papers.json index after a summary has been generated.

Usage:
    python update_summary_status.py --paper-id 2401.12345 --data-dir ./data
"""

from __future__ import annotations

import argparse
import json
import logging
import re
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
logger = logging.getLogger("update_summary_status")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format, False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


def update_metadata(paper_id: str, data_dir: Path) -> bool:
    """Update has_summary status in paper's metadata.json.

    Args:
        paper_id: The arXiv paper ID
        data_dir: Data directory path

    Returns:
        True if update successful, False otherwise
    """
    # Defensive validation
    if not validate_arxiv_id(paper_id):
        logger.error("Invalid paper ID format: %s", paper_id)
        return False

    metadata_path = data_dir / "papers" / paper_id / "metadata.json"

    if not metadata_path.exists():
        logger.error("Metadata file not found: %s", metadata_path)
        return False

    tmp_path: Path | None = None
    try:
        # Load existing metadata
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata: dict[str, Any] = json.load(f)

        # Update summary status
        metadata["has_summary"] = True
        metadata["summary_generated_at"] = datetime.now().isoformat()

        # Atomic write using temp file
        paper_dir = metadata_path.parent
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=paper_dir,
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp_path = Path(tmp.name)
            json.dump(metadata, tmp, indent=2, ensure_ascii=False)

        # Atomic rename
        tmp_path.replace(metadata_path)
        tmp_path = None  # Clear so finally block doesn't try to delete
        logger.info("Updated metadata for paper %s", paper_id)
        return True

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in metadata file: %s", e)
        return False
    except OSError as e:
        logger.error("Failed to update metadata: %s", e)
        return False
    finally:
        # Clean up temp file if it still exists
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def update_index(paper_id: str, data_dir: Path) -> bool:
    """Update has_summary status in papers.json index.

    Args:
        paper_id: The arXiv paper ID
        data_dir: Data directory path

    Returns:
        True if update successful, False otherwise
    """
    # Defensive validation
    if not validate_arxiv_id(paper_id):
        logger.error("Invalid paper ID format: %s", paper_id)
        return False

    index_path = data_dir / "index" / "papers.json"

    if not index_path.exists():
        logger.warning("Index file not found: %s", index_path)
        return False

    tmp_path: Path | None = None
    try:
        # Load existing index
        with index_path.open("r", encoding="utf-8") as f:
            index: dict[str, Any] = json.load(f)

        # Check if paper exists in index
        papers = index.get("papers", {})
        if paper_id not in papers:
            logger.warning("Paper %s not found in index", paper_id)
            return False

        # Update summary status
        papers[paper_id]["has_summary"] = True
        index["updated_at"] = datetime.now().isoformat()

        # Atomic write using temp file
        index_dir = index_path.parent
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=index_dir,
            suffix=".json",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp_path = Path(tmp.name)
            json.dump(index, tmp, indent=2, ensure_ascii=False)

        # Atomic rename
        tmp_path.replace(index_path)
        tmp_path = None  # Clear so finally block doesn't try to delete
        logger.info("Updated index for paper %s", paper_id)
        return True

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in index file: %s", e)
        return False
    except OSError as e:
        logger.error("Failed to update index: %s", e)
        return False
    finally:
        # Clean up temp file if it still exists
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update paper summary status")
    parser.add_argument(
        "--paper-id",
        type=str,
        required=True,
        help="arXiv paper ID (e.g., 2401.12345)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )

    args = parser.parse_args()

    # Validate paper ID format
    if not validate_arxiv_id(args.paper_id):
        logger.error("Invalid arXiv ID format: %s", args.paper_id)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_PAPER_ID",
                        "message": f"Invalid arXiv ID format: {args.paper_id}",
                        "details": "Expected format: YYMM.NNNNN (e.g., 2401.12345)",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    # Check if paper exists
    paper_dir = args.data_dir / "papers" / args.paper_id
    if not paper_dir.exists():
        logger.error("Paper not found in collection: %s", args.paper_id)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "PAPER_NOT_FOUND",
                        "message": f"Paper {args.paper_id} not found in collection",
                        "details": "Run /paper-collect to add papers first",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    # Update metadata
    metadata_updated = update_metadata(args.paper_id, args.data_dir)

    # Update index (continue even if metadata update fails)
    index_updated = update_index(args.paper_id, args.data_dir)

    # Report results
    if metadata_updated and index_updated:
        result: dict[str, Any] = {
            "success": True,
            "paper_id": args.paper_id,
            "message": "Updated summary status",
        }
        print(json.dumps(result, indent=2))
        return 0
    elif metadata_updated:
        result = {
            "success": True,
            "paper_id": args.paper_id,
            "message": "Updated metadata only (index update failed)",
            "warning": "Index may be out of sync",
        }
        print(json.dumps(result, indent=2))
        return 0
    else:
        result = {
            "success": False,
            "error": {
                "code": "UPDATE_FAILED",
                "message": "Failed to update summary status",
                "details": f"Metadata: {metadata_updated}, Index: {index_updated}",
            },
        }
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
