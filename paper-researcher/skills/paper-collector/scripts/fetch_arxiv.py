#!/usr/bin/env python3
"""Fetch research papers from arXiv API.

This script queries the arXiv API to fetch paper metadata based on search
topics/keywords. It supports date range filtering, configurable result limits,
and includes retry logic with exponential backoff for API failures.

Usage:
    python fetch_arxiv.py --query "LLM agents" --days 7 --max 50 --output papers.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import feedparser  # type: ignore[import-untyped]
import requests

# Constants
ARXIV_BASE_URL = "https://export.arxiv.org/api/query"
MAX_RESULTS = 50
REQUEST_DELAY = 3.0  # seconds between requests
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fetch_arxiv")


def positive_int(value: str) -> int:
    """Argparse type for positive integers.

    Args:
        value: String value to convert

    Returns:
        Positive integer value

    Raises:
        argparse.ArgumentTypeError: If value is not a positive integer
    """
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue


def build_query(topic: str, days: int) -> str:
    """Build arXiv search query string.

    Args:
        topic: Search topic/keywords
        days: Number of days to look back

    Returns:
        arXiv query string
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Format dates for arXiv (YYYYMMDD format)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # Clean up topic - remove special characters that could break the query
    clean_topic = re.sub(r"[^\w\s]", "", topic)

    # Build query: search in title and abstract
    query = f"all:{clean_topic}"

    # Add date filter using submittedDate
    query = f"{query} AND submittedDate:[{start_str} TO {end_str}]"

    return query


def fetch_with_retry(query: str, max_results: int = MAX_RESULTS) -> str:
    """Fetch papers from arXiv API with retry logic.

    Args:
        query: arXiv query string
        max_results: Maximum number of results to fetch

    Returns:
        Raw XML response text

    Raises:
        requests.RequestException: If all retries fail
    """
    params: dict[str, str | int] = {
        "search_query": query,
        "start": 0,
        "max_results": min(max_results, MAX_RESULTS),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "Querying arXiv (attempt %d/%d): %s",
                attempt + 1,
                MAX_RETRIES,
                query[:100],
            )

            response = requests.get(ARXIV_BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            # Respect rate limiting
            time.sleep(REQUEST_DELAY)

            return response.text

        except requests.RequestException as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = REQUEST_DELAY * (BACKOFF_FACTOR**attempt)
                logger.warning(
                    "Request failed (attempt %d/%d): %s. Retrying in %.1fs",
                    attempt + 1,
                    MAX_RETRIES,
                    str(e),
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error("All %d attempts failed", MAX_RETRIES)

    raise last_exception or requests.RequestException("All retries failed")


def parse_response(xml_text: str) -> list[dict[str, Any]]:
    """Parse arXiv Atom feed response.

    Args:
        xml_text: Raw XML response from arXiv API

    Returns:
        List of paper metadata dictionaries
    """
    feed = feedparser.parse(xml_text)
    papers: list[dict[str, Any]] = []

    for entry in feed.entries:
        # Extract arXiv ID from the entry ID URL
        # Format: http://arxiv.org/abs/2401.12345v1
        entry_id = entry.get("id", "")
        arxiv_id_match = re.search(r"(\d{4}\.\d{4,5})", entry_id)
        if not arxiv_id_match:
            logger.warning("Could not extract arXiv ID from: %s", entry_id)
            continue

        arxiv_id = arxiv_id_match.group(1)

        # Extract authors
        authors = [author.get("name", "") for author in entry.get("authors", [])]

        # Extract categories
        categories = [tag.get("term", "") for tag in entry.get("tags", [])]

        # Build paper metadata
        paper: dict[str, Any] = {
            "id": arxiv_id,
            "title": entry.get("title", "").replace("\n", " ").strip(),
            "authors": authors,
            "abstract": entry.get("summary", "").replace("\n", " ").strip(),
            "published": entry.get("published", "")[:10],  # YYYY-MM-DD
            "updated": entry.get("updated", "")[:10],
            "categories": categories,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        }

        papers.append(paper)

    return papers


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fetch research papers from arXiv API")
    parser.add_argument(
        "--query",
        required=True,
        help="Search topic/keywords",
    )
    parser.add_argument(
        "--days",
        type=positive_int,
        default=7,
        help="Number of days to look back (default: 7)",
    )
    parser.add_argument(
        "--max",
        type=positive_int,
        default=MAX_RESULTS,
        help=f"Maximum papers to fetch (1-{MAX_RESULTS}, default: {MAX_RESULTS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file path (default: stdout)",
    )

    args = parser.parse_args()

    try:
        # Build query
        query = build_query(args.query, args.days)
        logger.info("Searching arXiv for: %s (last %d days)", args.query, args.days)

        # Fetch papers
        xml_response = fetch_with_retry(query, args.max)

        # Parse response
        papers = parse_response(xml_response)
        logger.info("Found %d papers", len(papers))

        # Build output
        output: dict[str, Any] = {
            "success": True,
            "count": len(papers),
            "query": args.query,
            "days": args.days,
            "papers": papers,
        }

        # Write output
        json_output = json.dumps(output, indent=2, ensure_ascii=False)

        if args.output:
            args.output.write_text(json_output)
            logger.info("Wrote output to: %s", args.output)
        else:
            print(json_output)

        return 0

    except requests.RequestException as e:
        error_output: dict[str, Any] = {
            "success": False,
            "error": {
                "code": "ARXIV_API_UNAVAILABLE",
                "message": f"Failed to fetch papers after {MAX_RETRIES} retries",
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
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
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
