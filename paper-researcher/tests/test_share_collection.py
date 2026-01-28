"""Tests for share_collection.py script."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-collaborator" / "scripts")
)

from share_collection import (
    build_package,
    create_manifest,
    load_index,
    load_paper_metadata,
    main,
    sanitize_username,
    validate_arxiv_id,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_id_4_digits(self) -> None:
        """Test valid arXiv ID with 4 digits after dot."""
        assert validate_arxiv_id("2401.1234") is True

    def test_valid_id_5_digits(self) -> None:
        """Test valid arXiv ID with 5 digits after dot."""
        assert validate_arxiv_id("2401.12345") is True

    def test_invalid_path_traversal(self) -> None:
        """Test that path traversal attempts are rejected."""
        assert validate_arxiv_id("../etc/passwd") is False
        assert validate_arxiv_id("..") is False

    def test_invalid_format(self) -> None:
        """Test invalid formats are rejected."""
        assert validate_arxiv_id("invalid") is False
        assert validate_arxiv_id("2401.123") is False
        assert validate_arxiv_id("2401.123456") is False
        assert validate_arxiv_id("") is False


class TestSanitizeUsername:
    """Tests for sanitize_username function."""

    def test_valid_username(self) -> None:
        """Test valid usernames pass through."""
        assert sanitize_username("researcher") == "researcher"
        assert sanitize_username("user_name") == "user_name"
        assert sanitize_username("user-name") == "user-name"

    def test_special_characters_replaced(self) -> None:
        """Test special characters are replaced."""
        assert sanitize_username("user@email.com") == "user_email_com"
        assert sanitize_username("user name") == "user_name"
        assert sanitize_username("user.name") == "user_name"  # Dots also replaced

    def test_path_traversal_prevented(self) -> None:
        """Test path traversal is prevented."""
        assert ".." not in sanitize_username("../etc/passwd")
        assert sanitize_username("..") == "__"

    def test_empty_username(self) -> None:
        """Test empty username returns anonymous."""
        assert sanitize_username("") == "anonymous"

    def test_length_limited(self) -> None:
        """Test username length is limited."""
        long_name = "a" * 100
        assert len(sanitize_username(long_name)) == 50


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_existing_index(self, temp_data_dir: Path) -> None:
        """Test loading existing index."""
        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / "papers.json"
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Test Paper"}},
        }
        index_path.write_text(json.dumps(index_data), encoding="utf-8")

        # Load index
        index = load_index(temp_data_dir)
        assert index["version"] == "1.0"
        assert "2401.12345" in index["papers"]

    def test_missing_index(self, temp_data_dir: Path) -> None:
        """Test FileNotFoundError when index missing."""
        with pytest.raises(FileNotFoundError):
            load_index(temp_data_dir)


class TestLoadPaperMetadata:
    """Tests for load_paper_metadata function."""

    def test_load_existing_paper(self, temp_data_dir: Path) -> None:
        """Test loading existing paper metadata."""
        # Create paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        # Load metadata
        result = load_paper_metadata("2401.12345", temp_data_dir)
        assert result is not None
        assert result["title"] == "Test Paper"

    def test_missing_paper(self, temp_data_dir: Path) -> None:
        """Test None returned for missing paper."""
        result = load_paper_metadata("2401.12345", temp_data_dir)
        assert result is None

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test None returned for invalid paper ID."""
        result = load_paper_metadata("../invalid", temp_data_dir)
        assert result is None


class TestCreateManifest:
    """Tests for create_manifest function."""

    def test_basic_manifest(self) -> None:
        """Test basic manifest creation."""
        manifest = create_manifest(
            paper_ids=["2401.12345", "2401.12346"],
            username="researcher",
            include_summaries=True,
            include_annotations=False,
            description="Test collection",
        )

        assert manifest["version"] == "1.0"
        assert manifest["paper_count"] == 2
        assert manifest["created_by"] == "researcher"
        assert manifest["includes_summaries"] is True
        assert manifest["includes_annotations"] is False
        assert manifest["description"] == "Test collection"
        assert "created_at" in manifest


class TestBuildPackage:
    """Tests for build_package function."""

    def test_build_empty_collection(self, temp_data_dir: Path) -> None:
        """Test building package with no papers."""
        # Create empty index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {"version": "1.0", "papers": {}}
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        output_path = temp_data_dir / "test.zip"
        count, ids = build_package(
            data_dir=temp_data_dir,
            output_path=output_path,
            paper_ids=None,
            include_summaries=False,
            include_annotations=False,
            username="test",
            description=None,
        )

        assert count == 0
        assert ids == []
        assert not output_path.exists()

    def test_build_with_papers(self, temp_data_dir: Path) -> None:
        """Test building package with papers."""
        # Create paper
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {paper_id: {"title": "Test Paper"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        # Build package
        output_path = temp_data_dir / "test.zip"
        count, ids = build_package(
            data_dir=temp_data_dir,
            output_path=output_path,
            paper_ids=None,
            include_summaries=False,
            include_annotations=False,
            username="test",
            description="Test",
        )

        assert count == 1
        assert paper_id in ids
        assert output_path.exists()

        # Verify ZIP contents
        with zipfile.ZipFile(output_path, "r") as zf:
            assert "manifest.json" in zf.namelist()
            assert f"papers/{paper_id}/metadata.json" in zf.namelist()
            assert "index/papers.json" in zf.namelist()

    def test_build_with_summaries(self, temp_data_dir: Path) -> None:
        """Test including summaries in package."""
        # Create paper with summary
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        (paper_dir / "summary.md").write_text("# Summary\n\nTest summary.", encoding="utf-8")

        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {paper_id: {"title": "Test Paper"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        # Build package with summaries
        output_path = temp_data_dir / "test.zip"
        count, ids = build_package(
            data_dir=temp_data_dir,
            output_path=output_path,
            paper_ids=None,
            include_summaries=True,
            include_annotations=False,
            username="test",
            description=None,
        )

        # Verify summary included
        with zipfile.ZipFile(output_path, "r") as zf:
            assert f"papers/{paper_id}/summary.md" in zf.namelist()

    def test_build_with_annotations(self, temp_data_dir: Path) -> None:
        """Test including annotations in package."""
        # Create paper with annotation
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        annotations_dir = paper_dir / "annotations"
        annotations_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        annotation: dict[str, Any] = {"id": "abc123", "content": "Test note"}
        (annotations_dir / "test_annotation.json").write_text(
            json.dumps(annotation), encoding="utf-8"
        )

        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {paper_id: {"title": "Test Paper"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        # Build package with annotations
        output_path = temp_data_dir / "test.zip"
        build_package(
            data_dir=temp_data_dir,
            output_path=output_path,
            paper_ids=None,
            include_summaries=False,
            include_annotations=True,
            username="test",
            description=None,
        )

        # Verify annotation included
        with zipfile.ZipFile(output_path, "r") as zf:
            names = zf.namelist()
            assert any("annotations" in name for name in names)


class TestMainFunction:
    """Tests for CLI interface."""

    def test_valid_arguments(self, temp_data_dir: Path) -> None:
        """Test valid CLI arguments."""
        # Create paper
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {paper_id: {"title": "Test Paper"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        output_path = temp_data_dir / "output.zip"

        with patch(
            "sys.argv",
            [
                "share_collection.py",
                "--output",
                str(output_path),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0
            assert output_path.exists()

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test invalid paper ID argument."""
        output_path = temp_data_dir / "output.zip"

        with patch(
            "sys.argv",
            [
                "share_collection.py",
                "--output",
                str(output_path),
                "--paper-id",
                "../invalid",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_missing_index(self, temp_data_dir: Path) -> None:
        """Test error when no papers collected."""
        output_path = temp_data_dir / "output.zip"

        with patch(
            "sys.argv",
            [
                "share_collection.py",
                "--output",
                str(output_path),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1
