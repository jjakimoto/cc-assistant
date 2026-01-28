#!/usr/bin/env python3
"""Build citation graph from paper metadata.

This script builds a citation graph from the citation data stored in paper
metadata files. It creates an index with graph structure, statistics, and
identifies highly-cited papers.

Usage:
    python build_graph.py --data-dir ./data
    python build_graph.py --data-dir ./data --top 10
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_graph")


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


def load_paper_metadata(paper_id: str, data_dir: Path) -> dict[str, Any] | None:
    """Load metadata for a single paper.

    Args:
        paper_id: arXiv paper ID
        data_dir: Path to data directory

    Returns:
        Paper metadata dictionary or None if not found/invalid
    """
    if not validate_arxiv_id(paper_id):
        logger.warning("Invalid paper ID: %s", paper_id)
        return None

    metadata_path = data_dir / "papers" / paper_id / "metadata.json"
    if not metadata_path.exists():
        logger.debug("Metadata not found: %s", metadata_path)
        return None

    try:
        with open(metadata_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load metadata for %s: %s", paper_id, e)
        return None


def build_graph(data_dir: Path) -> dict[str, dict[str, list[str]]]:
    """Build citation graph from all paper metadata.

    Args:
        data_dir: Path to data directory

    Returns:
        Graph dictionary with paper_id -> {references, cited_by}
    """
    index = load_index(data_dir)
    papers_dict = index.get("papers", {})

    graph: dict[str, dict[str, list[str]]] = {}

    for paper_id in papers_dict:
        if not validate_arxiv_id(paper_id):
            logger.warning("Skipping invalid paper ID in index: %s", paper_id)
            continue

        metadata = load_paper_metadata(paper_id, data_dir)
        if metadata is None:
            continue

        citation_data = metadata.get("citation_data", {})
        refs = citation_data.get("references_in_collection", [])
        cited_by = citation_data.get("cited_by_in_collection", [])

        # Validate all IDs in refs and cited_by
        valid_refs = [r for r in refs if validate_arxiv_id(r)]
        valid_cited_by = [c for c in cited_by if validate_arxiv_id(c)]

        graph[paper_id] = {
            "references": valid_refs,
            "cited_by": valid_cited_by,
        }

    return graph


def calculate_stats(graph: dict[str, dict[str, list[str]]]) -> dict[str, Any]:
    """Calculate graph statistics.

    Args:
        graph: Citation graph dictionary

    Returns:
        Statistics dictionary
    """
    total_papers = len(graph)
    papers_with_citations = 0
    total_edges = 0

    for _paper_id, edges in graph.items():
        refs = edges.get("references", [])
        cited_by = edges.get("cited_by", [])

        if refs or cited_by:
            papers_with_citations += 1

        # Count edges (each reference is an edge)
        total_edges += len(refs)

    return {
        "total_papers": total_papers,
        "papers_with_citations": papers_with_citations,
        "total_edges": total_edges,
    }


def get_highly_cited(
    graph: dict[str, dict[str, list[str]]], top_n: int = 10
) -> list[tuple[str, int]]:
    """Get top N highly-cited papers.

    Args:
        graph: Citation graph dictionary
        top_n: Number of top papers to return

    Returns:
        List of (paper_id, citation_count) tuples sorted by count descending
    """
    citation_counts: list[tuple[str, int]] = []

    for paper_id, edges in graph.items():
        cited_by = edges.get("cited_by", [])
        citation_counts.append((paper_id, len(cited_by)))

    # Sort by citation count descending
    citation_counts.sort(key=lambda x: x[1], reverse=True)

    # Filter to only papers with at least 1 citation and limit to top_n
    cited_papers = [(pid, count) for pid, count in citation_counts if count > 0]
    return cited_papers[:top_n]


def save_index(index: dict[str, Any], data_dir: Path) -> None:
    """Save citations index atomically.

    Args:
        index: Citations index dictionary
        data_dir: Path to data directory
    """
    index_dir = data_dir / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "citations.json"

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=index_dir, suffix=".json", prefix=".citations_"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, index_path)
        tmp_path = None
        logger.info("Saved citations index to: %s", index_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build citation graph from paper metadata"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Path to data directory",
    )
    parser.add_argument(
        "--top",
        type=positive_int,
        default=10,
        help="Number of highly-cited papers to show (default: 10)",
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

    try:
        logger.info("Building citation graph from: %s", args.data_dir)

        # Build graph
        graph = build_graph(args.data_dir)

        if not graph:
            logger.warning("No papers with citation data found")
            output: dict[str, Any] = {
                "success": True,
                "total_papers": 0,
                "papers_with_citations": 0,
                "total_edges": 0,
                "highly_cited": [],
            }
            print(json.dumps(output, indent=2))
            return 0

        # Calculate stats
        stats = calculate_stats(graph)

        # Get highly cited papers
        highly_cited = get_highly_cited(graph, args.top)

        # Build citations index
        citations_index: dict[str, Any] = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "graph": graph,
            "stats": {
                **stats,
                "highly_cited": [pid for pid, _ in highly_cited],
            },
        }

        # Save index
        save_index(citations_index, args.data_dir)

        # Output results
        output = {
            "success": True,
            "total_papers": stats["total_papers"],
            "papers_with_citations": stats["papers_with_citations"],
            "total_edges": stats["total_edges"],
            "highly_cited": [
                {"id": pid, "cited_by_count": count} for pid, count in highly_cited
            ],
        }

        logger.info(
            "Graph built: %d papers, %d with citations, %d edges",
            stats["total_papers"],
            stats["papers_with_citations"],
            stats["total_edges"],
        )

        print(json.dumps(output, indent=2))
        return 0

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
