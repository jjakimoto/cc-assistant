#!/usr/bin/env python3
"""Save annotation for a paper.

This script saves a user annotation for a specific paper, storing it
in the paper's annotations directory.

Usage:
    python save_annotation.py --paper-id 2401.12345 --content "Great paper!" --username "researcher"
    python save_annotation.py --paper-id 2401.12345 --content-file notes.txt
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Constants
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")
MIN_CONTENT_LENGTH = 1
MAX_CONTENT_LENGTH = 50000

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("save_annotation")


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
    # Allow only alphanumeric, underscores, hyphens
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
    # Prevent path traversal
    sanitized = sanitized.replace("..", "_")
    # Limit length
    return sanitized[:50] if sanitized else "anonymous"


def load_metadata(paper_id: str, data_dir: Path) -> dict[str, Any] | None:
    """Load metadata for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Metadata dictionary or None if not found
    """
    if not validate_arxiv_id(paper_id):
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


def update_metadata(paper_id: str, data_dir: Path, annotation_count: int) -> bool:
    """Update paper metadata with annotation count.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory
        annotation_count: New annotation count

    Returns:
        True if successful, False otherwise
    """
    if not validate_arxiv_id(paper_id):
        return False

    metadata_path = data_dir / "papers" / paper_id / "metadata.json"

    if not metadata_path.exists():
        return False

    tmp_path: Path | None = None
    try:
        with metadata_path.open(encoding="utf-8") as f:
            metadata = json.load(f)

        metadata["annotation_count"] = annotation_count
        metadata["last_annotated_at"] = datetime.now(timezone.utc).isoformat()

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=metadata_path.parent,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(metadata, tmp, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp.name)
        tmp_path.replace(metadata_path)
        return True
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Failed to update metadata: %s", e)
        return False
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def count_annotations(paper_id: str, data_dir: Path) -> int:
    """Count annotations for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Number of annotations
    """
    if not validate_arxiv_id(paper_id):
        return 0

    annotations_dir = data_dir / "papers" / paper_id / "annotations"

    if not annotations_dir.exists():
        return 0

    return len(list(annotations_dir.glob("*.json")))


def save_annotation(
    paper_id: str,
    content: str,
    username: str,
    data_dir: Path,
    annotation_type: str = "note",
) -> tuple[bool, str]:
    """Save annotation for a paper.

    Args:
        paper_id: arXiv paper ID
        content: Annotation content
        username: Author username
        data_dir: Path to data directory
        annotation_type: Type of annotation (note, highlight, question, comment)

    Returns:
        Tuple of (success, annotation_id or error_message)
    """
    if not validate_arxiv_id(paper_id):
        return False, "Invalid paper ID format"

    # Check paper exists
    paper_dir = data_dir / "papers" / paper_id
    if not paper_dir.exists():
        return False, f"Paper {paper_id} not found in collection"

    # Create annotations directory
    annotations_dir = paper_dir / "annotations"
    annotations_dir.mkdir(exist_ok=True)

    # Generate annotation ID
    annotation_id = str(uuid.uuid4())[:8]
    safe_username = sanitize_username(username)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"{safe_username}_{timestamp}_{annotation_id}.json"

    # Build annotation object
    annotation: dict[str, Any] = {
        "id": annotation_id,
        "paper_id": paper_id,
        "author": safe_username,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "type": annotation_type,
        "content": content,
    }

    # Save annotation
    annotation_path = annotations_dir / filename
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=annotations_dir,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(annotation, tmp, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp.name)
        tmp_path.replace(annotation_path)

        # Update metadata with annotation count
        new_count = count_annotations(paper_id, data_dir)
        update_metadata(paper_id, data_dir, new_count)

        logger.info("Saved annotation %s for paper %s", annotation_id, paper_id)
        return True, annotation_id

    except OSError as e:
        logger.error("Failed to save annotation: %s", e)
        return False, str(e)
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Save annotation for a paper")
    parser.add_argument(
        "--paper-id",
        required=True,
        help="arXiv paper ID",
    )

    # Content source (mutually exclusive)
    content_group = parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument(
        "--content",
        help="Annotation content",
    )
    content_group.add_argument(
        "--content-file",
        type=Path,
        help="File containing annotation content",
    )

    parser.add_argument(
        "--username",
        default=os.environ.get("USER", "anonymous"),
        help="Author username",
    )
    parser.add_argument(
        "--type",
        choices=["note", "highlight", "question", "comment"],
        default="note",
        dest="annotation_type",
        help="Annotation type (default: note)",
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

        # Get content
        if args.content:
            content = args.content
        else:
            if not args.content_file.exists():
                error_output = {
                    "success": False,
                    "error": {
                        "code": "FILE_NOT_FOUND",
                        "message": f"Content file not found: {args.content_file}",
                        "details": "Provide a valid file path with --content-file",
                    },
                }
                print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
                return 1
            content = args.content_file.read_text(encoding="utf-8")

        # Validate content length
        if len(content) < MIN_CONTENT_LENGTH:
            error_output = {
                "success": False,
                "error": {
                    "code": "INVALID_CONTENT",
                    "message": "Annotation content is empty",
                    "details": f"Content must be at least {MIN_CONTENT_LENGTH} character(s)",
                },
            }
            print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        if len(content) > MAX_CONTENT_LENGTH:
            error_output = {
                "success": False,
                "error": {
                    "code": "CONTENT_TOO_LONG",
                    "message": "Annotation content is too long",
                    "details": f"Content must be at most {MAX_CONTENT_LENGTH} characters",
                },
            }
            print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        # Save annotation
        success, result = save_annotation(
            paper_id=args.paper_id,
            content=content,
            username=args.username,
            data_dir=args.data_dir,
            annotation_type=args.annotation_type,
        )

        if success:
            output: dict[str, Any] = {
                "success": True,
                "message": f"Saved annotation for paper {args.paper_id}.",
                "annotation_id": result,
                "paper_id": args.paper_id,
                "author": sanitize_username(args.username),
                "type": args.annotation_type,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0
        else:
            error_output = {
                "success": False,
                "error": {
                    "code": "PAPER_NOT_FOUND",
                    "message": result,
                    "details": "Ensure the paper exists in your collection",
                },
            }
            print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

    except OSError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "FILE_ERROR",
                "message": "Failed to save annotation",
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
