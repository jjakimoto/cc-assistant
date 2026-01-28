#!/usr/bin/env python3
"""Search collected papers by keyword or natural language query.

This script searches across paper titles, abstracts, and summaries to find
relevant papers in the collection. Results are ranked by relevance score
and returned with excerpts showing matched content.

Usage:
    python search_index.py --query "attention mechanisms" --data-dir ./data --limit 10
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Constants
DEFAULT_LIMIT = 10
MIN_QUERY_LENGTH = 1
MAX_QUERY_LENGTH = 500
EXCERPT_CONTEXT = 50  # Characters before and after match

# arXiv ID validation pattern (defense against path traversal)
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}$")

# Weight factors for different fields
WEIGHT_TITLE = 3.0
WEIGHT_ABSTRACT = 2.0
WEIGHT_SUMMARY = 1.5
WEIGHT_TOPIC = 1.0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("search_index")


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


def validate_arxiv_id(paper_id: str) -> bool:
    """Validate that paper_id matches expected arXiv ID format.

    This is a security check to prevent path traversal attacks.

    Args:
        paper_id: The paper ID to validate

    Returns:
        True if valid arXiv ID format (YYMM.NNNNN), False otherwise
    """
    return bool(ARXIV_ID_PATTERN.match(paper_id))


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


def load_summary(paper_id: str, data_dir: Path) -> str | None:
    """Load summary content for a paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Summary content as string, or None if not available
    """
    # Validate paper ID to prevent path traversal attacks
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


def count_matches(text: str, query_terms: list[str]) -> int:
    """Count how many query terms appear in text.

    Args:
        text: Text to search in
        query_terms: List of query terms to find

    Returns:
        Number of matching terms found
    """
    text_lower = text.lower()
    return sum(1 for term in query_terms if term in text_lower)


def calculate_relevance(
    query_terms: list[str],
    paper: dict[str, Any],
    summary: str | None,
) -> float:
    """Calculate relevance score for a paper.

    Score is based on weighted matches across title, abstract, summary, and topics.

    Args:
        query_terms: List of query terms
        paper: Paper metadata dictionary
        summary: Summary content or None

    Returns:
        Relevance score (0.0 if no matches)
    """
    if not query_terms:
        return 0.0

    score = 0.0

    # Title matches (highest weight)
    title = paper.get("title", "")
    title_matches = count_matches(title, query_terms)
    score += title_matches * WEIGHT_TITLE

    # Abstract matches
    abstract = paper.get("abstract", "")
    abstract_matches = count_matches(abstract, query_terms)
    score += abstract_matches * WEIGHT_ABSTRACT

    # Summary matches
    if summary:
        summary_matches = count_matches(summary, query_terms)
        score += summary_matches * WEIGHT_SUMMARY

    # Topic matches
    topics = paper.get("topics", [])
    for topic in topics:
        topic_matches = count_matches(topic, query_terms)
        score += topic_matches * WEIGHT_TOPIC

    return score


def extract_excerpt(
    query_terms: list[str],
    text: str,
    max_length: int = 150,
) -> str:
    """Extract relevant excerpt containing query terms.

    Finds the first occurrence of any query term and extracts surrounding context.

    Args:
        query_terms: List of query terms to find
        text: Text to extract from
        max_length: Maximum length of excerpt

    Returns:
        Excerpt string with ellipsis if truncated
    """
    if not text or not query_terms:
        return ""

    text_lower = text.lower()

    # Find first matching term
    best_pos = len(text)
    matched_term = ""

    for term in query_terms:
        pos = text_lower.find(term)
        if pos != -1 and pos < best_pos:
            best_pos = pos
            matched_term = term

    if best_pos == len(text):
        # No match found, return start of text
        if len(text) <= max_length:
            return text.strip()
        return text[:max_length].strip() + "..."

    # Calculate excerpt boundaries
    start = max(0, best_pos - EXCERPT_CONTEXT)
    end = min(len(text), best_pos + len(matched_term) + EXCERPT_CONTEXT)

    # Extend to word boundaries
    if start > 0:
        # Find previous space
        while start > 0 and text[start] not in " \n\t":
            start -= 1
        start = max(0, start + 1)

    if end < len(text):
        # Find next space
        while end < len(text) and text[end] not in " \n\t":
            end += 1

    excerpt = text[start:end].strip()

    # Add ellipsis
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""

    return f"{prefix}{excerpt}{suffix}"


def search_papers(
    query: str,
    data_dir: Path,
    limit: int = DEFAULT_LIMIT,
) -> tuple[list[dict[str, Any]], int]:
    """Search papers and return ranked results.

    Args:
        query: Search query string
        data_dir: Path to data directory
        limit: Maximum number of results to return

    Returns:
        Tuple of (list of result dicts, total paper count)

    Raises:
        FileNotFoundError: If index file does not exist
        ValueError: If query is empty or too long
    """
    # Validate query
    query = query.strip()
    if len(query) < MIN_QUERY_LENGTH:
        raise ValueError("Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query too long (max {MAX_QUERY_LENGTH} characters)")

    # Load index
    index = load_index(data_dir)
    papers = index.get("papers", {})
    total_papers = len(papers)

    if total_papers == 0:
        return [], 0

    # Tokenize query
    query_terms = tokenize(query)
    if not query_terms:
        return [], total_papers

    logger.info("Searching for terms: %s", query_terms)

    # Score all papers
    scored_papers: list[tuple[float, str, dict[str, Any], str | None]] = []

    for paper_id, paper in papers.items():
        # Validate paper ID to prevent path traversal attacks
        if not validate_arxiv_id(paper_id):
            logger.warning("Skipping paper with invalid ID: %s", paper_id)
            continue

        # Load summary if available
        summary = None
        if paper.get("has_summary"):
            summary = load_summary(paper_id, data_dir)

        # Calculate relevance
        score = calculate_relevance(query_terms, paper, summary)

        if score > 0:
            # Store summary to avoid duplicate file I/O during result building
            scored_papers.append((score, paper_id, paper, summary))

    # Sort by score (descending)
    scored_papers.sort(key=lambda x: x[0], reverse=True)

    # Build results
    results: list[dict[str, Any]] = []

    for score, paper_id, paper, summary in scored_papers[:limit]:
        # Extract excerpt from abstract or summary (use cached summary)
        excerpt_text = paper.get("abstract", "")
        if summary:
            excerpt_text = summary

        excerpt = extract_excerpt(query_terms, excerpt_text)

        result = {
            "id": paper_id,
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "score": round(score, 2),
            "excerpt": excerpt,
        }
        results.append(result)

    logger.info("Found %d matching papers", len(results))
    return results, total_papers


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Search collected papers by keyword or natural language query"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search query (keywords or natural language)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data"),
        help="Data directory path (default: ./data)",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=DEFAULT_LIMIT,
        help=f"Maximum results to return (default: {DEFAULT_LIMIT})",
    )

    args = parser.parse_args()

    try:
        # Search papers
        results, total_papers = search_papers(args.query, args.data_dir, args.limit)

        # Build output
        output: dict[str, Any] = {
            "success": True,
            "query": args.query,
            "total_papers": total_papers,
            "match_count": len(results),
            "results": results,
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
        print(json.dumps(error_output, indent=2), file=sys.stderr)
        return 1

    except ValueError as e:
        error_output = {
            "success": False,
            "error": {
                "code": "INVALID_QUERY",
                "message": str(e),
                "details": str(e),
            },
        }
        print(json.dumps(error_output, indent=2), file=sys.stderr)
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
