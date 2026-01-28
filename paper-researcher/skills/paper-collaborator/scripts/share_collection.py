#!/usr/bin/env python3
"""Share paper collection as a portable ZIP package.

This script creates a shareable ZIP package containing paper metadata,
summaries, and annotations for collaborative sharing.

Usage:
    python share_collection.py --output collection.zip --username "researcher"
    python share_collection.py --output collection.zip --include-summaries
    python share_collection.py --output collection.zip --paper-id 2401.12345
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Constants
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")
MANIFEST_VERSION = "1.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("share_collection")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    This is a security check to prevent path traversal attacks.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format (YYMM.NNNNN), False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


def sanitize_username(username: str) -> str:
    """Sanitize username for safe use in file paths.

    Args:
        username: Raw username string

    Returns:
        Sanitized username safe for file paths
    """
    # Allow only alphanumeric, underscores, hyphens (no dots for consistency)
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
    # Prevent path traversal
    sanitized = sanitized.replace("..", "_")
    # Limit length
    return sanitized[:50] if sanitized else "anonymous"


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


def load_paper_metadata(paper_id: str, data_dir: Path) -> dict[str, Any] | None:
    """Load full metadata for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Metadata dictionary or None if not available
    """
    if not validate_arxiv_id(paper_id):
        logger.warning("Invalid arXiv ID format: %s, skipping", paper_id)
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


def create_manifest(
    paper_ids: list[str],
    username: str,
    include_summaries: bool,
    include_annotations: bool,
    description: str | None,
) -> dict[str, Any]:
    """Create manifest for the collection package.

    Args:
        paper_ids: List of paper IDs in the package
        username: Creator username
        include_summaries: Whether summaries are included
        include_annotations: Whether annotations are included
        description: Optional description

    Returns:
        Manifest dictionary
    """
    return {
        "version": MANIFEST_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": sanitize_username(username),
        "paper_count": len(paper_ids),
        "includes_summaries": include_summaries,
        "includes_annotations": include_annotations,
        "description": description or "",
    }


def build_package(
    data_dir: Path,
    output_path: Path,
    paper_ids: list[str] | None,
    include_summaries: bool,
    include_annotations: bool,
    username: str,
    description: str | None,
) -> tuple[int, list[str]]:
    """Build ZIP package with papers.

    Args:
        data_dir: Path to data directory
        output_path: Path for output ZIP file
        paper_ids: List of specific paper IDs (None for all)
        include_summaries: Whether to include summaries
        include_annotations: Whether to include annotations
        username: Creator username
        description: Optional description

    Returns:
        Tuple of (paper_count, list of paper IDs added)

    Raises:
        OSError: If file operations fail
    """
    # Load index
    index = load_index(data_dir)
    all_papers = index.get("papers", {})

    # Filter papers if specific IDs provided
    if paper_ids:
        papers_to_export = {
            pid: paper
            for pid, paper in all_papers.items()
            if pid in paper_ids and validate_arxiv_id(pid)
        }
    else:
        papers_to_export = {
            pid: paper for pid, paper in all_papers.items() if validate_arxiv_id(pid)
        }

    if not papers_to_export:
        return 0, []

    added_papers: list[str] = []

    # Create ZIP package
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for paper_id in papers_to_export:
            paper_dir = data_dir / "papers" / paper_id

            # Add metadata.json
            metadata_path = paper_dir / "metadata.json"
            if metadata_path.exists():
                zf.write(metadata_path, f"papers/{paper_id}/metadata.json")
                added_papers.append(paper_id)
            else:
                logger.warning("Skipping paper %s: no metadata.json", paper_id)
                continue

            # Add summary.md if requested
            if include_summaries:
                summary_path = paper_dir / "summary.md"
                if summary_path.exists():
                    zf.write(summary_path, f"papers/{paper_id}/summary.md")

            # Add annotations if requested
            if include_annotations:
                annotations_dir = paper_dir / "annotations"
                if annotations_dir.exists() and annotations_dir.is_dir():
                    for annotation_file in annotations_dir.glob("*.json"):
                        zf.write(
                            annotation_file,
                            f"papers/{paper_id}/annotations/{annotation_file.name}",
                        )

        # Build partial index for shared papers only
        partial_index: dict[str, Any] = {
            "version": index.get("version", "1.0"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "papers": {
                pid: papers_to_export[pid] for pid in added_papers
            },
        }
        zf.writestr("index/papers.json", json.dumps(partial_index, indent=2, ensure_ascii=False))

        # Add manifest
        manifest = create_manifest(
            added_papers,
            username,
            include_summaries,
            include_annotations,
            description,
        )
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    logger.info("Created package with %d papers: %s", len(added_papers), output_path)
    return len(added_papers), added_papers


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Share paper collection as ZIP package")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output ZIP file path",
    )
    parser.add_argument(
        "--paper-id",
        action="append",
        dest="paper_ids",
        help="Specific paper IDs to include (can be repeated)",
    )
    parser.add_argument(
        "--include-summaries",
        action="store_true",
        help="Include paper summaries in package",
    )
    parser.add_argument(
        "--include-annotations",
        action="store_true",
        help="Include paper annotations in package",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("USER", "anonymous"),
        help="Creator username for manifest",
    )
    parser.add_argument(
        "--description",
        help="Description for the collection",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )

    args = parser.parse_args()

    try:
        # Validate paper IDs if provided
        if args.paper_ids:
            for paper_id in args.paper_ids:
                if not validate_arxiv_id(paper_id):
                    error_output: dict[str, Any] = {
                        "success": False,
                        "error": {
                            "code": "INVALID_PAPER_ID",
                            "message": f"Invalid arXiv ID format: {paper_id}",
                            "details": "arXiv ID must be in format YYMM.NNNNN (e.g., 2401.12345)",
                        },
                    }
                    print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
                    return 1

        # Build package
        paper_count, paper_ids = build_package(
            data_dir=args.data_dir,
            output_path=args.output,
            paper_ids=args.paper_ids,
            include_summaries=args.include_summaries,
            include_annotations=args.include_annotations,
            username=args.username,
            description=args.description,
        )

        if paper_count == 0:
            output: dict[str, Any] = {
                "success": True,
                "message": "No papers to share. Run /paper-collect first.",
                "paper_count": 0,
                "output_path": None,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0

        output = {
            "success": True,
            "message": f"Created collection package with {paper_count} papers.",
            "paper_count": paper_count,
            "paper_ids": paper_ids,
            "output_path": str(args.output.absolute()),
            "includes_summaries": args.include_summaries,
            "includes_annotations": args.include_annotations,
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
                "message": "Failed to create package",
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
