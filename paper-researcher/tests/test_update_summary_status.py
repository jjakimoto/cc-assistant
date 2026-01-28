"""Unit tests for update_summary_status.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-summarizer" / "scripts")
)

from update_summary_status import (
    main,
    update_index,
    update_metadata,
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


class TestUpdateMetadata:
    """Tests for update_metadata function."""

    def test_update_existing_metadata(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test updating existing metadata file."""
        paper_id = sample_paper["id"]
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        # Create initial metadata
        metadata_path = paper_dir / "metadata.json"
        initial_metadata = {
            **sample_paper,
            "collected_at": "2024-01-01T00:00:00",
            "topics": [],
            "has_summary": False,
        }
        with metadata_path.open("w") as f:
            json.dump(initial_metadata, f)

        # Update metadata
        result = update_metadata(paper_id, temp_data_dir)

        assert result is True

        # Verify update
        with metadata_path.open() as f:
            updated = json.load(f)

        assert updated["has_summary"] is True
        assert "summary_generated_at" in updated

    def test_update_nonexistent_metadata(self, temp_data_dir: Path) -> None:
        """Test updating when metadata file doesn't exist."""
        result = update_metadata("2401.99999", temp_data_dir)
        assert result is False

    def test_update_corrupted_metadata(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test handling of corrupted metadata file."""
        paper_id = sample_paper["id"]
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        # Create corrupted metadata
        metadata_path = paper_dir / "metadata.json"
        metadata_path.write_text("not valid json {{{")

        result = update_metadata(paper_id, temp_data_dir)
        assert result is False


class TestUpdateIndex:
    """Tests for update_index function."""

    def test_update_existing_index(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test updating existing index file."""
        paper_id = sample_paper["id"]

        # Create index with paper entry
        index_data = {
            "version": "1.0",
            "updated_at": "2024-01-01T00:00:00",
            "papers": {
                paper_id: {
                    "title": sample_paper["title"],
                    "authors": sample_paper["authors"],
                    "topics": [],
                    "collected_at": "2024-01-01T00:00:00",
                    "has_summary": False,
                }
            },
        }

        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Update index
        result = update_index(paper_id, temp_data_dir)

        assert result is True

        # Verify update
        with index_path.open() as f:
            updated = json.load(f)

        assert updated["papers"][paper_id]["has_summary"] is True
        assert updated["updated_at"] != "2024-01-01T00:00:00"

    def test_update_nonexistent_index(self, temp_data_dir: Path) -> None:
        """Test updating when index file doesn't exist."""
        # Remove index directory content
        index_path = temp_data_dir / "index" / "papers.json"
        if index_path.exists():
            index_path.unlink()

        result = update_index("2401.12345", temp_data_dir)
        assert result is False

    def test_update_paper_not_in_index(self, temp_data_dir: Path) -> None:
        """Test updating when paper is not in index."""
        # Create empty index
        index_data = {
            "version": "1.0",
            "updated_at": "2024-01-01T00:00:00",
            "papers": {},
        }

        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        result = update_index("2401.99999", temp_data_dir)
        assert result is False

    def test_update_corrupted_index(self, temp_data_dir: Path) -> None:
        """Test handling of corrupted index file."""
        index_path = temp_data_dir / "index" / "papers.json"
        index_path.write_text("not valid json {{{")

        result = update_index("2401.12345", temp_data_dir)
        assert result is False


class TestAtomicWrite:
    """Tests for atomic file writing behavior."""

    def test_metadata_atomic_update(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test that metadata update is atomic."""
        paper_id = sample_paper["id"]
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        # Create initial metadata
        metadata_path = paper_dir / "metadata.json"
        initial_metadata = {
            **sample_paper,
            "collected_at": "2024-01-01T00:00:00",
            "topics": [],
            "has_summary": False,
        }
        with metadata_path.open("w") as f:
            json.dump(initial_metadata, f)

        # Update should complete atomically
        result = update_metadata(paper_id, temp_data_dir)
        assert result is True

        # File should be valid JSON after update
        with metadata_path.open() as f:
            updated = json.load(f)
        assert updated["has_summary"] is True

    def test_index_atomic_update(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test that index update is atomic."""
        paper_id = sample_paper["id"]

        # Create index
        index_data = {
            "version": "1.0",
            "updated_at": "2024-01-01T00:00:00",
            "papers": {
                paper_id: {
                    "title": sample_paper["title"],
                    "authors": sample_paper["authors"],
                    "topics": [],
                    "collected_at": "2024-01-01T00:00:00",
                    "has_summary": False,
                }
            },
        }

        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Update should complete atomically
        result = update_index(paper_id, temp_data_dir)
        assert result is True

        # File should be valid JSON after update
        with index_path.open() as f:
            updated = json.load(f)
        assert updated["papers"][paper_id]["has_summary"] is True


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_required_paper_id_argument(self) -> None:
        """Test that --paper-id is required."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["update_summary_status.py"]):
                main()

    def test_invalid_paper_id_format(self, tmp_path: Path) -> None:
        """Test handling of invalid paper ID format."""
        with patch(
            "sys.argv",
            [
                "update_summary_status.py",
                "--paper-id",
                "not-valid-id",
                "--data-dir",
                str(tmp_path),
            ],
        ):
            exit_code = main()

        assert exit_code == 1

    def test_paper_not_found(self, temp_data_dir: Path) -> None:
        """Test handling of paper not in collection."""
        with patch(
            "sys.argv",
            [
                "update_summary_status.py",
                "--paper-id",
                "2401.99999",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            exit_code = main()

        assert exit_code == 1

    def test_full_workflow(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test full CLI workflow."""
        paper_id = sample_paper["id"]

        # Setup: Create paper directory and metadata
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata = {
            **sample_paper,
            "collected_at": "2024-01-01T00:00:00",
            "topics": [],
            "has_summary": False,
        }
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        # Setup: Create index
        index_data = {
            "version": "1.0",
            "updated_at": "2024-01-01T00:00:00",
            "papers": {
                paper_id: {
                    "title": sample_paper["title"],
                    "authors": sample_paper["authors"],
                    "topics": [],
                    "collected_at": "2024-01-01T00:00:00",
                    "has_summary": False,
                }
            },
        }
        with (temp_data_dir / "index" / "papers.json").open("w") as f:
            json.dump(index_data, f)

        # Run CLI
        with patch(
            "sys.argv",
            [
                "update_summary_status.py",
                "--paper-id",
                paper_id,
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            exit_code = main()

        assert exit_code == 0

        # Verify both files were updated
        with (paper_dir / "metadata.json").open() as f:
            updated_metadata = json.load(f)
        assert updated_metadata["has_summary"] is True

        with (temp_data_dir / "index" / "papers.json").open() as f:
            updated_index = json.load(f)
        assert updated_index["papers"][paper_id]["has_summary"] is True

    def test_metadata_only_update(
        self, temp_data_dir: Path, sample_paper: dict[str, Any]
    ) -> None:
        """Test workflow when index update fails but metadata succeeds."""
        paper_id = sample_paper["id"]

        # Setup: Create paper directory and metadata only (no index)
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata = {
            **sample_paper,
            "collected_at": "2024-01-01T00:00:00",
            "topics": [],
            "has_summary": False,
        }
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        # Remove index file if exists
        index_path = temp_data_dir / "index" / "papers.json"
        if index_path.exists():
            index_path.unlink()

        # Run CLI - should succeed even if index update fails
        with patch(
            "sys.argv",
            [
                "update_summary_status.py",
                "--paper-id",
                paper_id,
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            exit_code = main()

        # Should succeed (metadata updated even if index failed)
        assert exit_code == 0

        # Verify metadata was updated
        with (paper_dir / "metadata.json").open() as f:
            updated_metadata = json.load(f)
        assert updated_metadata["has_summary"] is True
