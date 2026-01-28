#!/usr/bin/env python3
"""Import shared paper collection from ZIP package.

This script imports a shared collection ZIP package, merging papers
into the local collection while handling duplicates appropriately.

Usage:
    python import_collection.py --input collection.zip
    python import_collection.py --input collection.zip --overwrite
    python import_collection.py --input collection.zip --data-dir ./data
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Constants
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")
REQUIRED_MANIFEST_FIELDS = ["version", "created_at", "paper_count"]
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB limit per file
MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500 MB total limit
MAX_FILE_COUNT = 10000  # Maximum files in package
MAX_COMPRESSION_RATIO = 100  # 100:1 max ratio for ZIP bomb detection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("import_collection")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    This is a security check to prevent path traversal attacks.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format (YYMM.NNNNN), False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


def validate_zip_path(path: str) -> bool:
    """Validate that a ZIP entry path is safe.

    Prevents path traversal attacks by checking for suspicious patterns.

    Args:
        path: ZIP entry path to validate

    Returns:
        True if path is safe, False otherwise
    """
    # Reject absolute paths
    if path.startswith("/") or path.startswith("\\"):
        return False

    # Reject path traversal attempts
    if ".." in path:
        return False

    # Reject suspicious Windows paths
    if ":" in path:
        return False

    return True


def validate_manifest(manifest: dict[str, Any]) -> tuple[bool, str]:
    """Validate manifest structure and content.

    Args:
        manifest: Manifest dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            return False, f"Missing required field: {field}"

    if not isinstance(manifest.get("paper_count"), int):
        return False, "paper_count must be an integer"

    if manifest.get("paper_count", 0) < 0:
        return False, "paper_count must be non-negative"

    return True, ""


def load_index(data_dir: Path) -> dict[str, Any]:
    """Load paper index from disk.

    Args:
        data_dir: Path to data directory

    Returns:
        Index dictionary with papers (empty if not exists)
    """
    index_path = data_dir / "index" / "papers.json"

    if not index_path.exists():
        return {"version": "1.0", "papers": {}}

    try:
        with index_path.open(encoding="utf-8") as f:
            index: dict[str, Any] = json.load(f)
        logger.info("Loaded existing index with %d papers", len(index.get("papers", {})))
        return index
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to load existing index: %s", e)
        return {"version": "1.0", "papers": {}}


def save_index(index: dict[str, Any], data_dir: Path) -> None:
    """Save paper index to disk atomically.

    Args:
        index: Index dictionary to save
        data_dir: Path to data directory
    """
    index_dir = data_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "papers.json"

    # Update timestamp
    index["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Atomic write
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=index_dir,
            suffix=".tmp",
            delete=False,
        ) as tmp:
            json.dump(index, tmp, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp.name)
        tmp_path.replace(index_path)
        logger.info("Saved index with %d papers", len(index.get("papers", {})))
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def import_package(
    input_path: Path,
    data_dir: Path,
    overwrite: bool,
) -> tuple[int, int, int, list[str]]:
    """Import papers from ZIP package.

    Args:
        input_path: Path to input ZIP file
        data_dir: Path to data directory
        overwrite: Whether to overwrite existing papers

    Returns:
        Tuple of (imported_count, skipped_count, annotation_count, imported_ids)

    Raises:
        ValueError: If package is invalid
        OSError: If file operations fail
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Package not found: {input_path}")

    imported_count = 0
    skipped_count = 0
    annotation_count = 0
    imported_ids: list[str] = []

    with zipfile.ZipFile(input_path, "r") as zf:
        # Validate package size and file count (ZIP bomb protection)
        file_list = zf.infolist()
        file_count = len(file_list)
        if file_count > MAX_FILE_COUNT:
            raise ValueError(f"Too many files in package: {file_count}")

        total_size = sum(info.file_size for info in file_list)
        if total_size > MAX_TOTAL_SIZE:
            raise ValueError(f"Package too large: {total_size} bytes")

        # Validate all paths and individual files (security check)
        for info in file_list:
            if not validate_zip_path(info.filename):
                raise ValueError(f"Invalid path in package: {info.filename}")
            if info.file_size > MAX_FILE_SIZE:
                raise ValueError(f"File too large: {info.filename}")
            # Check compression ratio for ZIP bomb detection
            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_COMPRESSION_RATIO:
                    raise ValueError(f"Suspicious compression ratio in {info.filename}")

        # Read and validate manifest
        try:
            manifest_data = zf.read("manifest.json")
            manifest = json.loads(manifest_data.decode("utf-8"))
        except KeyError as err:
            raise ValueError("Package missing manifest.json") from err
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid manifest.json: {e}") from e

        is_valid, error_msg = validate_manifest(manifest)
        if not is_valid:
            raise ValueError(f"Invalid manifest: {error_msg}")

        logger.info(
            "Importing package from %s (%d papers)",
            manifest.get("created_by", "unknown"),
            manifest.get("paper_count", 0),
        )

        # Load existing index
        index = load_index(data_dir)
        existing_papers = index.get("papers", {})

        # Process each paper in the package
        paper_entries = [
            info for info in zf.infolist()
            if info.filename.startswith("papers/")
            and info.filename.endswith("/metadata.json")
        ]

        for entry in paper_entries:
            # Extract paper ID from path: papers/{paper_id}/metadata.json
            parts = entry.filename.split("/")
            if len(parts) != 3:
                continue

            paper_id = parts[1]

            # Validate paper ID
            if not validate_arxiv_id(paper_id):
                logger.warning("Skipping paper with invalid ID: %s", paper_id)
                continue

            # Check if paper already exists
            if paper_id in existing_papers and not overwrite:
                logger.info("Skipping existing paper: %s", paper_id)
                skipped_count += 1
                continue

            # Create paper directory
            paper_dir = data_dir / "papers" / paper_id
            paper_dir.mkdir(parents=True, exist_ok=True)

            # Extract metadata.json
            try:
                metadata_data = zf.read(entry.filename)
                metadata = json.loads(metadata_data.decode("utf-8"))

                # Update metadata with import info
                metadata["imported_at"] = datetime.now(timezone.utc).isoformat()
                metadata["imported_from"] = manifest.get("created_by", "unknown")

                metadata_path = paper_dir / "metadata.json"
                tmp_path: Path | None = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        dir=paper_dir,
                        suffix=".tmp",
                        delete=False,
                    ) as tmp:
                        json.dump(metadata, tmp, indent=2, ensure_ascii=False)
                        tmp_path = Path(tmp.name)
                    tmp_path.replace(metadata_path)
                finally:
                    if tmp_path and tmp_path.exists():
                        try:
                            tmp_path.unlink()
                        except OSError:
                            pass

            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to import metadata for %s: %s", paper_id, e)
                continue

            # Extract summary.md if present
            summary_entry = f"papers/{paper_id}/summary.md"
            if summary_entry in zf.namelist():
                try:
                    summary_data = zf.read(summary_entry)
                    summary_path = paper_dir / "summary.md"
                    summary_path.write_bytes(summary_data)
                except OSError as e:
                    logger.warning("Failed to import summary for %s: %s", paper_id, e)

            # Extract annotations if present
            annotations_prefix = f"papers/{paper_id}/annotations/"
            annotation_entries = [
                info for info in zf.infolist()
                if info.filename.startswith(annotations_prefix)
                and info.filename.endswith(".json")
            ]

            if annotation_entries:
                annotations_dir = paper_dir / "annotations"
                annotations_dir.mkdir(exist_ok=True)

                for ann_entry in annotation_entries:
                    ann_name = Path(ann_entry.filename).name
                    try:
                        ann_data = zf.read(ann_entry.filename)
                        ann_path = annotations_dir / ann_name
                        ann_path.write_bytes(ann_data)
                        annotation_count += 1
                    except OSError as e:
                        logger.warning("Failed to import annotation %s: %s", ann_name, e)

            # Update index
            existing_papers[paper_id] = {
                "title": metadata.get("title", ""),
                "authors": metadata.get("authors", []),
                "abstract": metadata.get("abstract", "")[:500],
                "topics": metadata.get("topics", []),
                "collected_at": metadata.get("collected_at", ""),
                "has_summary": "has_summary" in metadata and metadata["has_summary"],
                "imported_at": metadata.get("imported_at", ""),
            }

            imported_count += 1
            imported_ids.append(paper_id)
            logger.info("Imported paper: %s", paper_id)

        # Save updated index
        index["papers"] = existing_papers
        save_index(index, data_dir)

    return imported_count, skipped_count, annotation_count, imported_ids


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import shared paper collection")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input ZIP file path",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing papers (default: skip duplicates)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )

    args = parser.parse_args()

    try:
        imported, skipped, annotations, paper_ids = import_package(
            input_path=args.input,
            data_dir=args.data_dir,
            overwrite=args.overwrite,
        )

        output: dict[str, Any] = {
            "success": True,
            "message": f"Imported {imported} papers ({skipped} skipped, "
            f"{annotations} annotations).",
            "imported_count": imported,
            "skipped_count": skipped,
            "annotation_count": annotations,
            "imported_ids": paper_ids,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    except FileNotFoundError as e:
        error_output: dict[str, Any] = {
            "success": False,
            "error": {
                "code": "FILE_NOT_FOUND",
                "message": "Package file not found",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    except ValueError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "INVALID_PACKAGE",
                "message": "Invalid or corrupted package",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    except zipfile.BadZipFile as e:
        error_output = {
            "success": False,
            "error": {
                "code": "INVALID_ZIP",
                "message": "File is not a valid ZIP archive",
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
                "message": "Failed to import package",
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
