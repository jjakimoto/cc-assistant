#!/usr/bin/env python3
"""Save blog post and update paper status.

This script saves the generated blog post content and updates the `has_blog_post`
field in both the paper's metadata.json and the global papers.json index.

Usage:
    python save_blog_post.py --paper-id 2401.12345 --content "..." --data-dir ./data
    python save_blog_post.py --paper-id 2401.12345 --content-file /path/to/blog.md --data-dir ./data
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
logger = logging.getLogger("save_blog_post")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format, False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


def load_metadata(paper_id: str, data_dir: Path) -> dict[str, Any] | None:
    """Load paper metadata from metadata.json.

    Args:
        paper_id: The arXiv paper ID
        data_dir: Data directory path

    Returns:
        Metadata dict if successful, None otherwise
    """
    if not validate_arxiv_id(paper_id):
        logger.error("Invalid paper ID format: %s", paper_id)
        return None

    metadata_path = data_dir / "papers" / paper_id / "metadata.json"

    if not metadata_path.exists():
        logger.error("Metadata file not found: %s", metadata_path)
        return None

    try:
        with metadata_path.open("r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in metadata file: %s", e)
        return None
    except OSError as e:
        logger.error("Failed to read metadata: %s", e)
        return None


def save_blog_post(paper_id: str, content: str, data_dir: Path) -> Path | None:
    """Save blog post content to file.

    Args:
        paper_id: The arXiv paper ID
        content: Blog post content in markdown
        data_dir: Data directory path

    Returns:
        Path to saved blog post if successful, None otherwise
    """
    if not validate_arxiv_id(paper_id):
        logger.error("Invalid paper ID format: %s", paper_id)
        return None

    blog_dir = data_dir / "blog-posts"
    blog_dir.mkdir(parents=True, exist_ok=True)

    blog_path = blog_dir / f"{paper_id}.md"

    tmp_path: Path | None = None
    try:
        # Atomic write using temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=blog_dir,
            suffix=".md",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content)

        # Atomic rename
        tmp_path.replace(blog_path)
        tmp_path = None  # Clear so finally block doesn't try to delete
        logger.info("Saved blog post for paper %s to %s", paper_id, blog_path)
        return blog_path

    except OSError as e:
        logger.error("Failed to save blog post: %s", e)
        return None
    finally:
        # Clean up temp file if it still exists
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def update_metadata(paper_id: str, data_dir: Path) -> bool:
    """Update has_blog_post status in paper's metadata.json.

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

        # Update blog post status
        metadata["has_blog_post"] = True
        metadata["blog_post_generated_at"] = datetime.now().isoformat()

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


def load_index(data_dir: Path) -> dict[str, Any] | None:
    """Load papers.json index.

    Args:
        data_dir: Data directory path

    Returns:
        Index dict if successful, None otherwise
    """
    index_path = data_dir / "index" / "papers.json"

    if not index_path.exists():
        logger.warning("Index file not found: %s", index_path)
        return None

    try:
        with index_path.open("r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in index file: %s", e)
        return None
    except OSError as e:
        logger.error("Failed to read index: %s", e)
        return None


def update_index(paper_id: str, data_dir: Path) -> bool:
    """Update has_blog_post status in papers.json index.

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

        # Update blog post status
        papers[paper_id]["has_blog_post"] = True
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
    parser = argparse.ArgumentParser(description="Save blog post and update status")
    parser.add_argument(
        "--paper-id",
        type=str,
        required=True,
        help="arXiv paper ID (e.g., 2401.12345)",
    )
    content_group = parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument(
        "--content",
        type=str,
        help="Blog post content as string",
    )
    content_group.add_argument(
        "--content-file",
        type=Path,
        help="Path to file containing blog post content",
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

    # Check if paper has summary
    summary_path = paper_dir / "summary.md"
    metadata = load_metadata(args.paper_id, args.data_dir)
    if metadata is None:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "METADATA_ERROR",
                        "message": f"Failed to load metadata for paper {args.paper_id}",
                        "details": "Check that metadata.json exists and is valid",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    if not metadata.get("has_summary") or not summary_path.exists():
        logger.error("Paper has no summary: %s", args.paper_id)
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "NO_SUMMARY",
                        "message": f"Paper {args.paper_id} has no summary",
                        "details": "Run /paper-summarize first to generate a summary",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    # Get content from argument or file
    content: str
    if args.content_file:
        try:
            content = args.content_file.read_text(encoding="utf-8")
        except OSError as e:
            logger.error("Failed to read content file: %s", e)
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": {
                            "code": "FILE_ERROR",
                            "message": "Failed to read content file",
                            "details": str(e),
                        },
                    }
                ),
                file=sys.stderr,
            )
            return 1
    else:
        content = args.content

    # Validate content
    if not content or len(content.strip()) < 100:
        logger.error("Blog post content is too short")
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_CONTENT",
                        "message": "Blog post content is too short",
                        "details": "Content must be at least 100 characters",
                    },
                }
            ),
            file=sys.stderr,
        )
        return 1

    # Save blog post
    blog_path = save_blog_post(args.paper_id, content, args.data_dir)
    if blog_path is None:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "SAVE_FAILED",
                        "message": "Failed to save blog post",
                        "details": "Check file permissions and disk space",
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
    result: dict[str, Any] = {
        "success": True,
        "paper_id": args.paper_id,
        "blog_path": str(blog_path),
        "message": "Blog post saved successfully",
    }

    if not metadata_updated:
        result["warning"] = "Metadata update failed"
    if not index_updated:
        if "warning" in result:
            result["warning"] += "; Index update failed"
        else:
            result["warning"] = "Index update failed"

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
