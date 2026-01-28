#!/usr/bin/env python3
"""Fetch citation data from Semantic Scholar API.

This script fetches citation data for papers in the collection using the
Semantic Scholar API. It supports fetching for a single paper or all papers
in the collection, with retry logic and rate limiting.

Usage:
    python fetch_citations.py --paper-id 2401.12345 --data-dir ./data
    python fetch_citations.py --all --data-dir ./data
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Constants
S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
REQUEST_DELAY = 3.0  # seconds between requests (100 req/5min = ~3s per request)
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
RATE_LIMIT_WAIT = 60  # seconds to wait on 429

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fetch_citations")


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate arXiv ID format.

    Args:
        paper_id: Paper ID to validate

    Returns:
        True if valid arXiv ID format (YYMM.NNNNN or YYMM.NNNN)
    """
    if not paper_id:
        return False
    return bool(re.match(r"^\d{4}\.\d{4,5}$", paper_id))


def load_index(data_dir: Path) -> dict[str, Any]:
    """Load papers index from data directory.

    Args:
        data_dir: Path to data directory

    Returns:
        Papers index dictionary or empty dict if not found
    """
    index_path = data_dir / "index" / "papers.json"
    if not index_path.exists():
        logger.warning("Papers index not found: %s", index_path)
        return {"papers": {}}

    try:
        with open(index_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load index: %s", e)
        return {"papers": {}}


def fetch_with_retry(arxiv_id: str, max_retries: int = MAX_RETRIES) -> dict[str, Any] | None:
    """Fetch citation data from Semantic Scholar with retry logic.

    Args:
        arxiv_id: arXiv paper ID
        max_retries: Maximum number of retry attempts

    Returns:
        Citation data dictionary or None if not found
    """
    url = f"{S2_BASE_URL}/paper/arXiv:{arxiv_id}"
    params = {"fields": "references,citations,citationCount,referenceCount,externalIds"}

    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            logger.debug(
                "Fetching citations for %s (attempt %d/%d)",
                arxiv_id,
                attempt + 1,
                max_retries,
            )

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 404:
                logger.info("Paper not found in Semantic Scholar: %s", arxiv_id)
                return None

            if response.status_code == 429:
                logger.warning("Rate limited, waiting %ds...", RATE_LIMIT_WAIT)
                time.sleep(RATE_LIMIT_WAIT)
                continue

            response.raise_for_status()

            # Respect rate limiting
            time.sleep(REQUEST_DELAY)

            result: dict[str, Any] = response.json()
            return result

        except requests.RequestException as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = REQUEST_DELAY * (BACKOFF_FACTOR**attempt)
                logger.warning(
                    "Request failed (attempt %d/%d): %s. Retrying in %.1fs",
                    attempt + 1,
                    max_retries,
                    str(e),
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error("All %d attempts failed for %s", max_retries, arxiv_id)

    if last_exception:
        raise last_exception
    return None


def extract_arxiv_ids(papers: list[dict[str, Any]] | None) -> list[str]:
    """Extract arXiv IDs from Semantic Scholar paper references/citations.

    Args:
        papers: List of paper objects from S2 API

    Returns:
        List of arXiv IDs
    """
    if not papers:
        return []

    arxiv_ids: list[str] = []
    for paper in papers:
        external_ids = paper.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv")
        if arxiv_id and validate_arxiv_id(arxiv_id):
            arxiv_ids.append(arxiv_id)

    return arxiv_ids


def filter_in_collection(arxiv_ids: list[str], index: dict[str, Any]) -> list[str]:
    """Filter arXiv IDs to only those in our collection.

    Args:
        arxiv_ids: List of arXiv IDs to filter
        index: Papers index dictionary

    Returns:
        List of arXiv IDs that are in our collection
    """
    papers_dict = index.get("papers", {})
    return [aid for aid in arxiv_ids if aid in papers_dict]


def update_metadata(
    paper_id: str,
    citation_data: dict[str, Any] | None,
    data_dir: Path,
    index: dict[str, Any],
) -> bool:
    """Update paper metadata with citation data.

    Args:
        paper_id: arXiv paper ID
        citation_data: Citation data from S2 API or None if unavailable
        data_dir: Path to data directory
        index: Papers index dictionary

    Returns:
        True if update successful
    """
    if not validate_arxiv_id(paper_id):
        logger.error("Invalid paper ID: %s", paper_id)
        return False

    paper_dir = data_dir / "papers" / paper_id
    metadata_path = paper_dir / "metadata.json"

    if not metadata_path.exists():
        logger.error("Metadata not found: %s", metadata_path)
        return False

    try:
        # Load existing metadata
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)

        # Build citation data
        if citation_data is None:
            # Paper not found in S2
            metadata["citation_data"] = {
                "source": "unavailable",
                "fetched_at": datetime.now().isoformat(),
                "citation_count": 0,
                "reference_count": 0,
                "references_in_collection": [],
                "cited_by_in_collection": [],
            }
        else:
            # Extract references and citations
            ref_arxiv_ids = extract_arxiv_ids(citation_data.get("references"))
            cite_arxiv_ids = extract_arxiv_ids(citation_data.get("citations"))

            # Filter to in-collection papers
            refs_in_collection = filter_in_collection(ref_arxiv_ids, index)
            cited_by_in_collection = filter_in_collection(cite_arxiv_ids, index)

            metadata["citation_data"] = {
                "source": "semantic_scholar",
                "fetched_at": datetime.now().isoformat(),
                "citation_count": citation_data.get("citationCount", 0),
                "reference_count": citation_data.get("referenceCount", 0),
                "references_in_collection": refs_in_collection,
                "cited_by_in_collection": cited_by_in_collection,
            }

        # Atomic write
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(
                dir=paper_dir, suffix=".json", prefix=".metadata_"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, metadata_path)
            tmp_path = None
            logger.debug("Updated metadata for %s", paper_id)
            return True
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to update metadata for %s: %s", paper_id, e)
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch citation data from Semantic Scholar API"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--paper-id",
        help="arXiv paper ID to fetch citations for",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Fetch citations for all papers in collection",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Path to data directory",
    )

    args = parser.parse_args()

    # Validate data directory
    if not args.data_dir.exists():
        error_output: dict[str, Any] = {
            "success": False,
            "error": {
                "code": "DATA_DIR_NOT_FOUND",
                "message": f"Data directory not found: {args.data_dir}",
                "details": None,
            },
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        return 1

    # Load papers index
    index = load_index(args.data_dir)
    papers_dict = index.get("papers", {})

    if not papers_dict:
        logger.warning("No papers in collection")
        output: dict[str, Any] = {
            "success": True,
            "papers_processed": 0,
            "papers_with_citations": 0,
            "papers_not_found": 0,
            "errors": [],
        }
        print(json.dumps(output, indent=2))
        return 0

    # Determine which papers to process
    if args.paper_id:
        if not validate_arxiv_id(args.paper_id):
            error_output = {
                "success": False,
                "error": {
                    "code": "INVALID_PAPER_ID",
                    "message": f"Invalid arXiv ID format: {args.paper_id}",
                    "details": "Expected format: YYMM.NNNNN (e.g., 2401.12345)",
                },
            }
            print(json.dumps(error_output, indent=2), file=sys.stderr)
            return 1

        if args.paper_id not in papers_dict:
            error_output = {
                "success": False,
                "error": {
                    "code": "PAPER_NOT_IN_COLLECTION",
                    "message": f"Paper not in collection: {args.paper_id}",
                    "details": None,
                },
            }
            print(json.dumps(error_output, indent=2), file=sys.stderr)
            return 1

        paper_ids = [args.paper_id]
    else:
        paper_ids = list(papers_dict.keys())

    # Process papers
    papers_processed = 0
    papers_with_citations = 0
    papers_not_found = 0
    errors: list[str] = []

    logger.info("Processing %d papers...", len(paper_ids))

    for paper_id in paper_ids:
        if not validate_arxiv_id(paper_id):
            logger.warning("Skipping invalid paper ID: %s", paper_id)
            errors.append(f"Invalid ID: {paper_id}")
            continue

        try:
            citation_data = fetch_with_retry(paper_id)

            if citation_data is None:
                papers_not_found += 1
            else:
                papers_with_citations += 1

            if update_metadata(paper_id, citation_data, args.data_dir, index):
                papers_processed += 1
            else:
                errors.append(f"Failed to update: {paper_id}")

        except requests.RequestException as e:
            logger.error("Failed to fetch citations for %s: %s", paper_id, e)
            errors.append(f"Fetch failed: {paper_id}")

    # Output results
    output = {
        "success": len(errors) == 0,
        "papers_processed": papers_processed,
        "papers_with_citations": papers_with_citations,
        "papers_not_found": papers_not_found,
        "errors": errors,
    }

    logger.info(
        "Done: %d processed, %d with citations, %d not found, %d errors",
        papers_processed,
        papers_with_citations,
        papers_not_found,
        len(errors),
    )

    print(json.dumps(output, indent=2))
    return 0 if len(errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
