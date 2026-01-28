"""Tests for list_annotations.py script."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-collaborator" / "scripts")
)

from list_annotations import (
    format_annotation_markdown,
    format_annotation_text,
    format_annotations,
    load_annotations,
    main,
    validate_arxiv_id,
    validate_format,
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


class TestValidateFormat:
    """Tests for validate_format function."""

    def test_valid_formats(self) -> None:
        """Test valid formats."""
        assert validate_format("json") == "json"
        assert validate_format("markdown") == "markdown"
        assert validate_format("text") == "text"
        assert validate_format("JSON") == "json"  # Case insensitive

    def test_invalid_format(self) -> None:
        """Test invalid format raises error."""
        import argparse

        with pytest.raises(argparse.ArgumentTypeError):
            validate_format("invalid")


class TestLoadAnnotations:
    """Tests for load_annotations function."""

    def test_load_empty(self, temp_data_dir: Path) -> None:
        """Test loading with no annotations."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)

        annotations = load_annotations("2401.12345", temp_data_dir)
        assert annotations == []

    def test_load_multiple(self, temp_data_dir: Path) -> None:
        """Test loading multiple annotations."""
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        ann_dir.mkdir(parents=True)

        # Create annotations with different timestamps
        for i in range(3):
            annotation: dict[str, Any] = {
                "id": f"ann{i}",
                "content": f"Note {i}",
                "created_at": f"2026-01-2{i}T10:00:00Z",
            }
            (ann_dir / f"note_{i}.json").write_text(
                json.dumps(annotation), encoding="utf-8"
            )

        annotations = load_annotations("2401.12345", temp_data_dir)
        assert len(annotations) == 3

        # Verify sorted by date (newest first)
        assert annotations[0]["id"] == "ann2"

    def test_load_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test loading with invalid paper ID returns empty."""
        annotations = load_annotations("../invalid", temp_data_dir)
        assert annotations == []

    def test_load_skips_invalid_json(self, temp_data_dir: Path) -> None:
        """Test that invalid JSON files are skipped."""
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        ann_dir.mkdir(parents=True)

        # Create valid annotation
        valid: dict[str, Any] = {"id": "valid", "content": "Valid note"}
        (ann_dir / "valid.json").write_text(json.dumps(valid), encoding="utf-8")

        # Create invalid JSON
        (ann_dir / "invalid.json").write_text("not valid json", encoding="utf-8")

        annotations = load_annotations("2401.12345", temp_data_dir)
        assert len(annotations) == 1
        assert annotations[0]["id"] == "valid"


class TestFormatAnnotationText:
    """Tests for format_annotation_text function."""

    def test_basic_format(self) -> None:
        """Test basic text formatting."""
        annotation: dict[str, Any] = {
            "type": "note",
            "author": "researcher",
            "created_at": "2026-01-27T10:00:00Z",
            "content": "This is a test note.",
        }

        result = format_annotation_text(annotation)
        assert "[NOTE]" in result
        assert "researcher" in result
        assert "This is a test note." in result


class TestFormatAnnotationMarkdown:
    """Tests for format_annotation_markdown function."""

    def test_basic_format(self) -> None:
        """Test basic markdown formatting."""
        annotation: dict[str, Any] = {
            "type": "note",
            "author": "researcher",
            "created_at": "2026-01-27T10:00:00Z",
            "content": "This is a test note.",
        }

        result = format_annotation_markdown(annotation)
        assert "### Note" in result
        assert "**Author:** researcher" in result
        assert "This is a test note." in result


class TestFormatAnnotations:
    """Tests for format_annotations function."""

    def test_json_format(self) -> None:
        """Test JSON output format."""
        annotations: list[dict[str, Any]] = [
            {"id": "ann1", "content": "Note 1"},
            {"id": "ann2", "content": "Note 2"},
        ]

        result = format_annotations(annotations, "2401.12345", "json")
        parsed: dict[str, Any] = json.loads(result)

        assert parsed["paper_id"] == "2401.12345"
        assert parsed["count"] == 2
        assert len(parsed["annotations"]) == 2

    def test_markdown_format(self) -> None:
        """Test Markdown output format."""
        annotations: list[dict[str, Any]] = [
            {"id": "ann1", "type": "note", "author": "test", "content": "Note 1"},
        ]

        result = format_annotations(annotations, "2401.12345", "markdown")
        assert "# Annotations for Paper 2401.12345" in result
        assert "Total annotations:** 1" in result

    def test_text_format(self) -> None:
        """Test text output format."""
        annotations: list[dict[str, Any]] = [
            {"id": "ann1", "type": "note", "author": "test", "content": "Note 1"},
        ]

        result = format_annotations(annotations, "2401.12345", "text")
        assert "Annotations for Paper 2401.12345" in result
        assert "Total: 1" in result


class TestMainFunction:
    """Tests for CLI interface."""

    def test_list_annotations(self, temp_data_dir: Path) -> None:
        """Test listing annotations."""
        # Create paper with annotations
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        ann_dir.mkdir(parents=True)
        annotation: dict[str, Any] = {"id": "ann1", "content": "Test note"}
        (ann_dir / "note.json").write_text(json.dumps(annotation), encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "list_annotations.py",
                "--paper-id",
                "2401.12345",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_list_empty(self, temp_data_dir: Path) -> None:
        """Test listing with no annotations."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)

        with patch(
            "sys.argv",
            [
                "list_annotations.py",
                "--paper-id",
                "2401.12345",
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
                "list_annotations.py",
                "--paper-id",
                "../invalid",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_paper_not_found(self, temp_data_dir: Path) -> None:
        """Test paper not in collection."""
        with patch(
            "sys.argv",
            [
                "list_annotations.py",
                "--paper-id",
                "2401.12345",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_json_format_output(self, temp_data_dir: Path) -> None:
        """Test JSON format output."""
        # Create paper with annotations
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        ann_dir.mkdir(parents=True)
        annotation: dict[str, Any] = {"id": "ann1", "content": "Test note"}
        (ann_dir / "note.json").write_text(json.dumps(annotation), encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "list_annotations.py",
                "--paper-id",
                "2401.12345",
                "--format",
                "json",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_markdown_format_output(self, temp_data_dir: Path) -> None:
        """Test Markdown format output."""
        # Create paper with annotations
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        ann_dir.mkdir(parents=True)
        annotation: dict[str, Any] = {
            "id": "ann1",
            "type": "note",
            "author": "test",
            "content": "Test note",
            "created_at": "2026-01-27T10:00:00Z",
        }
        (ann_dir / "note.json").write_text(json.dumps(annotation), encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "list_annotations.py",
                "--paper-id",
                "2401.12345",
                "--format",
                "markdown",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0
