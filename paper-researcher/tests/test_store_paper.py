"""Unit tests for store_paper.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "paper-collector" / "scripts"))

from store_paper import (
    load_index,
    main,
    save_paper,
    update_index,
    validate_arxiv_id,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_arxiv_id(self) -> None:
        """Test that valid arXiv IDs are accepted."""
        assert validate_arxiv_id("2401.12345") is True
        assert validate_arxiv_id("1234.5678") is True
        assert validate_arxiv_id("2401.99999") is True  # 5-digit variant

    def test_invalid_arxiv_id_format(self) -> None:
        """Test that invalid arXiv ID formats are rejected."""
        assert validate_arxiv_id("not-valid") is False
        assert validate_arxiv_id("12345") is False
        assert validate_arxiv_id("") is False
        assert validate_arxiv_id("../../../etc/passwd") is False


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_existing_index(self, temp_data_dir: Path) -> None:
        """Test loading an existing index file."""
        index_data = {
            "version": "1.0",
            "updated_at": "2024-01-01T00:00:00",
            "papers": {
                "2401.12345": {
                    "title": "Existing Paper",
                    "authors": ["Author"],
                    "topics": [],
                    "collected_at": "2024-01-01T00:00:00",
                    "has_summary": False,
                }
            },
        }

        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        loaded = load_index(temp_data_dir)

        assert loaded["version"] == "1.0"
        assert "2401.12345" in loaded["papers"]

    def test_load_nonexistent_index(self, temp_data_dir: Path) -> None:
        """Test loading when index doesn't exist."""
        loaded = load_index(temp_data_dir)

        assert loaded["version"] == "1.0"
        assert loaded["papers"] == {}

    def test_load_corrupted_index(self, temp_data_dir: Path) -> None:
        """Test handling of corrupted index file."""
        index_path = temp_data_dir / "index" / "papers.json"
        index_path.write_text("not valid json {{{")

        loaded = load_index(temp_data_dir)

        # Should return empty index, not crash
        assert loaded["version"] == "1.0"
        assert loaded["papers"] == {}


class TestSavePaper:
    """Tests for save_paper function."""

    def test_save_new_paper(self, temp_data_dir: Path, sample_paper: dict[str, Any]) -> None:
        """Test saving a new paper."""
        result = save_paper(sample_paper, temp_data_dir, topic="LLM agents")

        assert result is True

        # Check file was created
        paper_dir = temp_data_dir / "papers" / sample_paper["id"]
        assert paper_dir.exists()

        metadata_path = paper_dir / "metadata.json"
        assert metadata_path.exists()

        # Check content
        with metadata_path.open() as f:
            saved = json.load(f)

        assert saved["id"] == sample_paper["id"]
        assert saved["title"] == sample_paper["title"]
        assert saved["topics"] == ["LLM agents"]
        assert saved["has_summary"] is False
        assert "collected_at" in saved

    def test_save_duplicate_paper(self, temp_data_dir: Path, sample_paper: dict[str, Any]) -> None:
        """Test that duplicate papers are skipped."""
        # Save first time
        result1 = save_paper(sample_paper, temp_data_dir)
        assert result1 is True

        # Save second time
        result2 = save_paper(sample_paper, temp_data_dir)
        assert result2 is False

    def test_save_paper_without_id(self, temp_data_dir: Path) -> None:
        """Test handling paper without ID."""
        paper_no_id: dict[str, Any] = {
            "title": "No ID Paper",
            "authors": ["Author"],
        }

        result = save_paper(paper_no_id, temp_data_dir)
        assert result is False

    def test_save_paper_with_path_traversal_id(self, temp_data_dir: Path) -> None:
        """Test that path traversal attempts are rejected."""
        malicious_paper: dict[str, Any] = {
            "id": "../../../etc/passwd",
            "title": "Malicious Paper",
            "authors": ["Attacker"],
        }
        result = save_paper(malicious_paper, temp_data_dir)
        assert result is False

    def test_save_paper_with_invalid_id_format(self, temp_data_dir: Path) -> None:
        """Test that invalid ID formats are rejected."""
        invalid_paper: dict[str, Any] = {
            "id": "not-valid-arxiv-format",
            "title": "Invalid Paper",
            "authors": ["Author"],
        }
        result = save_paper(invalid_paper, temp_data_dir)
        assert result is False

    def test_save_paper_creates_directory(
        self, tmp_path: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test that paper directory is created if it doesn't exist."""
        data_dir = tmp_path / "new_data"
        # Don't create the directory

        result = save_paper(sample_paper, data_dir)
        assert result is True

        # Directory should be created
        assert (data_dir / "papers" / sample_paper["id"]).exists()


class TestDuplicateDetection:
    """Tests for duplicate detection logic."""

    def test_duplicate_by_id(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> None:
        """Test that papers with same ID are detected as duplicates."""
        paper1 = sample_papers[0]

        # Save original
        save_paper(paper1, temp_data_dir)

        # Modify title but keep same ID
        paper1_modified = {**paper1, "title": "Modified Title"}
        result = save_paper(paper1_modified, temp_data_dir)

        assert result is False  # Should be detected as duplicate

    def test_different_ids_not_duplicates(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> None:
        """Test that papers with different IDs are not duplicates."""
        results = []
        for paper in sample_papers:
            results.append(save_paper(paper, temp_data_dir))

        # All should be saved successfully
        assert all(results)
        assert len(results) == len(sample_papers)


class TestUpdateIndex:
    """Tests for update_index function."""

    def test_update_empty_index(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> None:
        """Test updating an empty index."""
        index: dict[str, Any] = {
            "version": "1.0",
            "updated_at": "",
            "papers": {},
        }

        saved_ids = {p["id"] for p in sample_papers}
        update_index(index, sample_papers, temp_data_dir, saved_ids)

        # Check index was updated
        assert len(index["papers"]) == len(sample_papers)
        assert "updated_at" in index

        # Check index file was written
        index_path = temp_data_dir / "index" / "papers.json"
        assert index_path.exists()

    def test_update_existing_index(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> None:
        """Test updating an existing index with new papers."""
        # Create existing index
        existing_paper = {
            "title": "Existing Paper",
            "authors": ["Author"],
            "abstract": "...",
            "topics": [],
            "collected_at": "2024-01-01T00:00:00",
            "has_summary": False,
        }
        index: dict[str, Any] = {
            "version": "1.0",
            "updated_at": "2024-01-01T00:00:00",
            "papers": {"2401.00000": existing_paper},
        }

        saved_ids = {p["id"] for p in sample_papers}
        update_index(index, sample_papers, temp_data_dir, saved_ids)

        # Should have existing + new papers
        assert len(index["papers"]) == 1 + len(sample_papers)
        assert "2401.00000" in index["papers"]  # Existing
        assert sample_papers[0]["id"] in index["papers"]  # New

    def test_no_duplicate_in_index(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> None:
        """Test that duplicate papers are not added twice to index."""
        index: dict[str, Any] = {
            "version": "1.0",
            "updated_at": "",
            "papers": {},
        }

        saved_ids = {p["id"] for p in sample_papers}
        update_index(index, sample_papers, temp_data_dir, saved_ids)

        # Update again with same papers
        update_index(index, sample_papers, temp_data_dir, saved_ids)

        # Should still have same count (no duplicates)
        assert len(index["papers"]) == len(sample_papers)


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_required_input_argument(self) -> None:
        """Test that --input is required."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["store_paper.py"]):
                main()

    def test_input_file_not_found(self, tmp_path: Path) -> None:
        """Test handling of non-existent input file."""
        nonexistent = tmp_path / "does_not_exist.json"

        with patch(
            "sys.argv",
            ["store_paper.py", "--input", str(nonexistent)],
        ):
            exit_code = main()

        assert exit_code == 1

    def test_full_workflow(self, temp_fetch_output: Path, temp_data_dir: Path) -> None:
        """Test full CLI workflow."""
        with patch(
            "sys.argv",
            [
                "store_paper.py",
                "--input",
                str(temp_fetch_output),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            exit_code = main()

        assert exit_code == 0

        # Check papers were stored
        papers_dir = temp_data_dir / "papers"
        assert any(papers_dir.iterdir())

        # Check index was updated
        index_path = temp_data_dir / "index" / "papers.json"
        assert index_path.exists()

    def test_default_data_dir(
        self, temp_fetch_output: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test default data directory is used when not specified."""
        # Change to tmp_path so default ./data is created there
        monkeypatch.chdir(tmp_path)

        with patch(
            "sys.argv",
            ["store_paper.py", "--input", str(temp_fetch_output)],
        ):
            exit_code = main()

        assert exit_code == 0
        assert (tmp_path / "data" / "index" / "papers.json").exists()
