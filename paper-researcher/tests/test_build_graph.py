"""Unit tests for build_graph.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-citation" / "scripts")
)

from build_graph import (
    build_graph,
    calculate_stats,
    get_highly_cited,
    load_paper_metadata,
    main,
    save_index,
    validate_arxiv_id,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_ids(self) -> None:
        """Test valid arXiv IDs."""
        assert validate_arxiv_id("2401.1234") is True
        assert validate_arxiv_id("2401.12345") is True

    def test_invalid_ids(self) -> None:
        """Test invalid arXiv IDs."""
        assert validate_arxiv_id("") is False
        assert validate_arxiv_id("invalid") is False
        assert validate_arxiv_id("2401.123") is False


class TestLoadPaperMetadata:
    """Tests for load_paper_metadata function."""

    def test_load_existing_metadata(self, temp_data_dir: Path) -> None:
        """Test loading existing metadata."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))

        result = load_paper_metadata("2401.12345", temp_data_dir)
        assert result is not None
        assert result["id"] == "2401.12345"

    def test_missing_metadata(self, temp_data_dir: Path) -> None:
        """Test handling missing metadata."""
        result = load_paper_metadata("2401.99999", temp_data_dir)
        assert result is None

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test handling invalid paper ID."""
        result = load_paper_metadata("invalid", temp_data_dir)
        assert result is None


class TestBuildGraph:
    """Tests for build_graph function."""

    def test_build_graph_with_citations(self, temp_data_dir: Path) -> None:
        """Test building graph from papers with citation data."""
        # Create papers index
        index: dict[str, Any] = {"papers": {"2401.12345": {}, "2301.5432": {}}}
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        # Create paper 1 with citations
        paper1_dir = temp_data_dir / "papers" / "2401.12345"
        paper1_dir.mkdir(parents=True)
        paper1 = {
            "id": "2401.12345",
            "citation_data": {
                "references_in_collection": ["2301.5432"],
                "cited_by_in_collection": [],
            },
        }
        (paper1_dir / "metadata.json").write_text(json.dumps(paper1))

        # Create paper 2
        paper2_dir = temp_data_dir / "papers" / "2301.5432"
        paper2_dir.mkdir(parents=True)
        paper2 = {
            "id": "2301.5432",
            "citation_data": {
                "references_in_collection": [],
                "cited_by_in_collection": ["2401.12345"],
            },
        }
        (paper2_dir / "metadata.json").write_text(json.dumps(paper2))

        graph = build_graph(temp_data_dir)

        assert len(graph) == 2
        assert graph["2401.12345"]["references"] == ["2301.5432"]
        assert graph["2301.5432"]["cited_by"] == ["2401.12345"]

    def test_empty_collection(self, temp_data_dir: Path) -> None:
        """Test building graph from empty collection."""
        index: dict[str, Any] = {"papers": {}}
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        graph = build_graph(temp_data_dir)
        assert graph == {}


class TestCalculateStats:
    """Tests for calculate_stats function."""

    def test_calculate_stats(self) -> None:
        """Test calculating graph statistics."""
        graph: dict[str, dict[str, list[str]]] = {
            "2401.12345": {
                "references": ["2301.5432"],
                "cited_by": [],
            },
            "2301.5432": {
                "references": [],
                "cited_by": ["2401.12345"],
            },
        }

        stats = calculate_stats(graph)

        assert stats["total_papers"] == 2
        assert stats["papers_with_citations"] == 2
        assert stats["total_edges"] == 1  # One reference edge

    def test_empty_graph(self) -> None:
        """Test stats for empty graph."""
        stats = calculate_stats({})
        assert stats["total_papers"] == 0
        assert stats["papers_with_citations"] == 0
        assert stats["total_edges"] == 0


class TestGetHighlyCited:
    """Tests for get_highly_cited function."""

    def test_get_top_cited(self) -> None:
        """Test getting top cited papers."""
        graph: dict[str, dict[str, list[str]]] = {
            "paper1": {"references": [], "cited_by": ["a", "b", "c"]},
            "paper2": {"references": [], "cited_by": ["x"]},
            "paper3": {"references": [], "cited_by": ["a", "b"]},
        }

        result = get_highly_cited(graph, top_n=2)

        assert len(result) == 2
        assert result[0] == ("paper1", 3)
        assert result[1] == ("paper3", 2)

    def test_exclude_zero_citations(self) -> None:
        """Test that papers with 0 citations are excluded."""
        graph: dict[str, dict[str, list[str]]] = {
            "paper1": {"references": [], "cited_by": ["a"]},
            "paper2": {"references": [], "cited_by": []},
        }

        result = get_highly_cited(graph, top_n=10)

        assert len(result) == 1
        assert result[0][0] == "paper1"

    def test_empty_graph(self) -> None:
        """Test empty graph returns empty list."""
        result = get_highly_cited({}, top_n=10)
        assert result == []


class TestSaveIndex:
    """Tests for save_index function."""

    def test_save_index_atomic(self, temp_data_dir: Path) -> None:
        """Test atomic saving of citations index."""
        index: dict[str, Any] = {
            "version": "1.0",
            "graph": {"2401.12345": {"references": [], "cited_by": []}},
            "stats": {"total_papers": 1},
        }

        save_index(index, temp_data_dir)

        # Verify file was created
        index_path = temp_data_dir / "index" / "citations.json"
        assert index_path.exists()

        # Verify content
        saved = json.loads(index_path.read_text())
        assert saved["version"] == "1.0"
        assert saved["graph"]["2401.12345"] is not None

    def test_creates_index_dir(self, tmp_path: Path) -> None:
        """Test that index directory is created if missing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        index: dict[str, Any] = {"version": "1.0", "graph": {}}
        save_index(index, data_dir)

        assert (data_dir / "index" / "citations.json").exists()


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_requires_data_dir(self) -> None:
        """Test --data-dir is required."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["build_graph.py"]):
                main()

    def test_invalid_data_dir(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error with non-existent data directory."""
        with patch(
            "sys.argv", ["build_graph.py", "--data-dir", "/nonexistent/path"]
        ):
            exit_code = main()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "DATA_DIR_NOT_FOUND" in captured.err

    def test_default_top(self, temp_data_dir: Path) -> None:
        """Test default --top value."""
        # Create empty index
        (temp_data_dir / "index" / "papers.json").write_text('{"papers": {}}')

        with patch("sys.argv", ["build_graph.py", "--data-dir", str(temp_data_dir)]):
            exit_code = main()

        assert exit_code == 0

    def test_custom_top(self, temp_data_dir: Path) -> None:
        """Test custom --top value."""
        # Create empty index
        (temp_data_dir / "index" / "papers.json").write_text('{"papers": {}}')

        with patch(
            "sys.argv",
            ["build_graph.py", "--data-dir", str(temp_data_dir), "--top", "5"],
        ):
            exit_code = main()

        assert exit_code == 0


class TestEmptyCollection:
    """Tests for empty collection handling."""

    def test_empty_collection_success(
        self, temp_data_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that empty collection returns success."""
        # Create empty index
        (temp_data_dir / "index" / "papers.json").write_text('{"papers": {}}')

        with patch("sys.argv", ["build_graph.py", "--data-dir", str(temp_data_dir)]):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["success"] is True
        assert output["total_papers"] == 0
