"""Tests for save_annotation.py script."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-collaborator" / "scripts")
)

from save_annotation import (
    count_annotations,
    load_metadata,
    main,
    sanitize_username,
    save_annotation,
    update_metadata,
    validate_arxiv_id,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_id(self) -> None:
        """Test valid arXiv IDs."""
        assert validate_arxiv_id("2401.12345") is True
        assert validate_arxiv_id("2401.1234") is True

    def test_invalid_id(self) -> None:
        """Test invalid arXiv IDs."""
        assert validate_arxiv_id("../etc/passwd") is False
        assert validate_arxiv_id("invalid") is False
        assert validate_arxiv_id("") is False


class TestSanitizeUsername:
    """Tests for sanitize_username function."""

    def test_valid_username(self) -> None:
        """Test valid usernames."""
        assert sanitize_username("researcher") == "researcher"
        assert sanitize_username("user_name") == "user_name"

    def test_special_characters(self) -> None:
        """Test special characters are sanitized."""
        assert sanitize_username("user@email") == "user_email"
        assert sanitize_username("user name") == "user_name"

    def test_path_traversal(self) -> None:
        """Test path traversal is prevented."""
        result = sanitize_username("../etc/passwd")
        assert ".." not in result

    def test_empty_username(self) -> None:
        """Test empty username returns anonymous."""
        assert sanitize_username("") == "anonymous"


class TestLoadMetadata:
    """Tests for load_metadata function."""

    def test_load_existing(self, temp_data_dir: Path) -> None:
        """Test loading existing metadata."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        result = load_metadata("2401.12345", temp_data_dir)
        assert result is not None
        assert result["title"] == "Test"

    def test_missing_paper(self, temp_data_dir: Path) -> None:
        """Test None for missing paper."""
        result = load_metadata("2401.12345", temp_data_dir)
        assert result is None

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test None for invalid paper ID."""
        result = load_metadata("../invalid", temp_data_dir)
        assert result is None


class TestCountAnnotations:
    """Tests for count_annotations function."""

    def test_count_zero(self, temp_data_dir: Path) -> None:
        """Test count with no annotations."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)

        count = count_annotations("2401.12345", temp_data_dir)
        assert count == 0

    def test_count_multiple(self, temp_data_dir: Path) -> None:
        """Test count with multiple annotations."""
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        ann_dir.mkdir(parents=True)

        for i in range(3):
            (ann_dir / f"note_{i}.json").write_text("{}", encoding="utf-8")

        count = count_annotations("2401.12345", temp_data_dir)
        assert count == 3


class TestUpdateMetadata:
    """Tests for update_metadata function."""

    def test_update_success(self, temp_data_dir: Path) -> None:
        """Test successful metadata update."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        result = update_metadata("2401.12345", temp_data_dir, 5)
        assert result is True

        # Verify update
        updated = json.loads((paper_dir / "metadata.json").read_text(encoding="utf-8"))
        assert updated["annotation_count"] == 5
        assert "last_annotated_at" in updated

    def test_update_missing_paper(self, temp_data_dir: Path) -> None:
        """Test update for missing paper."""
        result = update_metadata("2401.12345", temp_data_dir, 1)
        assert result is False

    def test_update_invalid_id(self, temp_data_dir: Path) -> None:
        """Test update with invalid paper ID."""
        result = update_metadata("../invalid", temp_data_dir, 1)
        assert result is False


class TestSaveAnnotation:
    """Tests for save_annotation function."""

    def test_save_success(self, temp_data_dir: Path) -> None:
        """Test successful annotation save."""
        # Create paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        success, result = save_annotation(
            paper_id="2401.12345",
            content="This is a test note.",
            username="researcher",
            data_dir=temp_data_dir,
            annotation_type="note",
        )

        assert success is True
        assert len(result) == 8  # UUID prefix

        # Verify annotation file created
        ann_dir = paper_dir / "annotations"
        assert ann_dir.exists()
        assert len(list(ann_dir.glob("*.json"))) == 1

    def test_save_paper_not_found(self, temp_data_dir: Path) -> None:
        """Test save for non-existent paper."""
        success, error = save_annotation(
            paper_id="2401.12345",
            content="Note",
            username="test",
            data_dir=temp_data_dir,
        )

        assert success is False
        assert "not found" in error

    def test_save_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test save with invalid paper ID."""
        success, error = save_annotation(
            paper_id="../invalid",
            content="Note",
            username="test",
            data_dir=temp_data_dir,
        )

        assert success is False
        assert "Invalid" in error


class TestMainFunction:
    """Tests for CLI interface."""

    def test_valid_annotation(self, temp_data_dir: Path) -> None:
        """Test valid annotation save."""
        # Create paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "2401.12345",
                "--content",
                "Test annotation content",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test invalid paper ID."""
        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "../invalid",
                "--content",
                "Note",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_paper_not_found(self, temp_data_dir: Path) -> None:
        """Test paper not found."""
        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "2401.12345",
                "--content",
                "Note",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_empty_content(self, temp_data_dir: Path) -> None:
        """Test empty content rejected."""
        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "2401.12345",
                "--content",
                "",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_content_file(self, temp_data_dir: Path) -> None:
        """Test content from file."""
        # Create paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        # Create content file
        content_file = temp_data_dir / "notes.txt"
        content_file.write_text("Content from file", encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "2401.12345",
                "--content-file",
                str(content_file),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_content_file_not_found(self, temp_data_dir: Path) -> None:
        """Test content file not found."""
        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "2401.12345",
                "--content-file",
                str(temp_data_dir / "nonexistent.txt"),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_annotation_type(self, temp_data_dir: Path) -> None:
        """Test different annotation types."""
        # Create paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "save_annotation.py",
                "--paper-id",
                "2401.12345",
                "--content",
                "A question about this paper",
                "--type",
                "question",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

        # Verify annotation type
        ann_dir = paper_dir / "annotations"
        ann_files = list(ann_dir.glob("*.json"))
        assert len(ann_files) == 1

        ann_data: dict[str, Any] = json.loads(ann_files[0].read_text(encoding="utf-8"))
        assert ann_data["type"] == "question"
