"""Tests for save_blog_post.py script."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

# Add the scripts directory to the path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-blogger" / "scripts")
)

from save_blog_post import (  # noqa: E402
    load_index,
    load_metadata,
    main,
    save_blog_post,
    update_index,
    update_metadata,
    validate_arxiv_id,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_4digit_id(self) -> None:
        """Test valid 4-digit arXiv ID."""
        assert validate_arxiv_id("2401.1234") is True

    def test_valid_5digit_id(self) -> None:
        """Test valid 5-digit arXiv ID."""
        assert validate_arxiv_id("2401.12345") is True

    def test_invalid_format_no_dot(self) -> None:
        """Test invalid format without dot."""
        assert validate_arxiv_id("240112345") is False

    def test_invalid_format_letters(self) -> None:
        """Test invalid format with letters."""
        assert validate_arxiv_id("2401.abcde") is False

    def test_invalid_format_path_traversal(self) -> None:
        """Test path traversal attempt is rejected."""
        assert validate_arxiv_id("../etc/passwd") is False
        assert validate_arxiv_id("2401.12345/../..") is False

    def test_empty_string(self) -> None:
        """Test empty string is rejected."""
        assert validate_arxiv_id("") is False


class TestLoadMetadata:
    """Tests for load_metadata function."""

    def test_load_existing_metadata(self, temp_data_dir: Path) -> None:
        """Test loading existing metadata."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata = {
            "id": paper_id,
            "title": "Test Paper",
            "has_summary": True,
        }
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))

        result = load_metadata(paper_id, temp_data_dir)
        assert result is not None
        assert result["id"] == paper_id
        assert result["has_summary"] is True

    def test_load_nonexistent_metadata(self, temp_data_dir: Path) -> None:
        """Test loading non-existent metadata returns None."""
        result = load_metadata("2401.12345", temp_data_dir)
        assert result is None

    def test_load_invalid_json(self, temp_data_dir: Path) -> None:
        """Test loading invalid JSON returns None."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        (paper_dir / "metadata.json").write_text("not valid json")

        result = load_metadata(paper_id, temp_data_dir)
        assert result is None

    def test_load_with_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test loading with invalid paper ID returns None."""
        result = load_metadata("../invalid", temp_data_dir)
        assert result is None


class TestSaveBlogPost:
    """Tests for save_blog_post function."""

    def test_save_valid_blog_post(self, temp_data_dir: Path) -> None:
        """Test saving a valid blog post."""
        paper_id = "2401.12345"
        content = "# Test Blog Post\n\nThis is a test blog post content."

        result = save_blog_post(paper_id, content, temp_data_dir)
        assert result is not None
        assert result.exists()
        assert result.name == "2401.12345.md"
        assert result.read_text() == content

    def test_save_creates_directory(self, temp_data_dir: Path) -> None:
        """Test that save creates blog-posts directory if needed."""
        paper_id = "2401.12345"
        content = "# Test Content"
        # Remove blog-posts dir if it exists
        blog_dir = temp_data_dir / "blog-posts"
        if blog_dir.exists():
            blog_dir.rmdir()

        result = save_blog_post(paper_id, content, temp_data_dir)
        assert result is not None
        assert blog_dir.exists()

    def test_save_overwrites_existing(self, temp_data_dir: Path) -> None:
        """Test that save overwrites existing blog post."""
        paper_id = "2401.12345"
        blog_dir = temp_data_dir / "blog-posts"
        blog_dir.mkdir(parents=True)
        existing_path = blog_dir / f"{paper_id}.md"
        existing_path.write_text("old content")

        new_content = "new content"
        result = save_blog_post(paper_id, new_content, temp_data_dir)
        assert result is not None
        assert result.read_text() == new_content

    def test_save_with_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test saving with invalid paper ID returns None."""
        result = save_blog_post("../invalid", "content", temp_data_dir)
        assert result is None


class TestUpdateMetadata:
    """Tests for update_metadata function."""

    def test_update_existing_metadata(self, temp_data_dir: Path) -> None:
        """Test updating existing metadata."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, Any] = {"id": paper_id, "title": "Test"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))

        result = update_metadata(paper_id, temp_data_dir)
        assert result is True

        # Verify update
        updated = json.loads((paper_dir / "metadata.json").read_text())
        assert updated["has_blog_post"] is True
        assert "blog_post_generated_at" in updated

    def test_update_nonexistent_metadata(self, temp_data_dir: Path) -> None:
        """Test updating non-existent metadata returns False."""
        result = update_metadata("2401.12345", temp_data_dir)
        assert result is False

    def test_update_with_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test updating with invalid paper ID returns False."""
        result = update_metadata("../invalid", temp_data_dir)
        assert result is False


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_existing_index(self, temp_data_dir: Path) -> None:
        """Test loading existing index."""
        index: dict[str, Any] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Test"}},
        }
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        result = load_index(temp_data_dir)
        assert result is not None
        assert result["version"] == "1.0"
        assert "2401.12345" in result["papers"]

    def test_load_nonexistent_index(self, temp_data_dir: Path) -> None:
        """Test loading non-existent index returns None."""
        result = load_index(temp_data_dir)
        assert result is None


class TestUpdateIndex:
    """Tests for update_index function."""

    def test_update_existing_index(self, temp_data_dir: Path) -> None:
        """Test updating existing index."""
        paper_id = "2401.12345"
        index: dict[str, Any] = {
            "version": "1.0",
            "papers": {paper_id: {"title": "Test", "has_summary": True}},
        }
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        result = update_index(paper_id, temp_data_dir)
        assert result is True

        # Verify update
        updated = json.loads((temp_data_dir / "index" / "papers.json").read_text())
        assert updated["papers"][paper_id]["has_blog_post"] is True
        assert "updated_at" in updated

    def test_update_paper_not_in_index(self, temp_data_dir: Path) -> None:
        """Test updating paper not in index returns False."""
        index: dict[str, Any] = {"version": "1.0", "papers": {}}
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        result = update_index("2401.12345", temp_data_dir)
        assert result is False

    def test_update_nonexistent_index(self, temp_data_dir: Path) -> None:
        """Test updating non-existent index returns False."""
        result = update_index("2401.12345", temp_data_dir)
        assert result is False


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_valid_arguments_with_content(self, temp_data_dir: Path) -> None:
        """Test valid CLI arguments with --content."""
        # Set up paper with summary
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "has_summary": True}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))
        (paper_dir / "summary.md").write_text("# Summary")

        # Set up index
        index: dict[str, Any] = {"version": "1.0", "papers": {paper_id: {}}}
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        content = "# Blog Post\n\n" + "x" * 100  # Ensure min length

        with patch(
            "sys.argv",
            [
                "save_blog_post.py",
                "--paper-id",
                paper_id,
                "--content",
                content,
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_invalid_paper_id(self) -> None:
        """Test invalid paper ID format."""
        with patch(
            "sys.argv",
            [
                "save_blog_post.py",
                "--paper-id",
                "invalid",
                "--content",
                "test content",
            ],
        ):
            result = main()
            assert result == 1

    def test_paper_not_found(self, temp_data_dir: Path) -> None:
        """Test paper not found error."""
        with patch(
            "sys.argv",
            [
                "save_blog_post.py",
                "--paper-id",
                "2401.12345",
                "--content",
                "test content",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_no_summary_error(self, temp_data_dir: Path) -> None:
        """Test paper without summary error."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "has_summary": False}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))

        with patch(
            "sys.argv",
            [
                "save_blog_post.py",
                "--paper-id",
                paper_id,
                "--content",
                "test content",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_content_too_short(self, temp_data_dir: Path) -> None:
        """Test content too short error."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "has_summary": True}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))
        (paper_dir / "summary.md").write_text("# Summary")

        with patch(
            "sys.argv",
            [
                "save_blog_post.py",
                "--paper-id",
                paper_id,
                "--content",
                "short",  # Less than 100 chars
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_content_file_argument(self, temp_data_dir: Path) -> None:
        """Test --content-file argument."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": paper_id, "has_summary": True}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))
        (paper_dir / "summary.md").write_text("# Summary")

        # Set up index
        index: dict[str, Any] = {"version": "1.0", "papers": {paper_id: {}}}
        (temp_data_dir / "index" / "papers.json").write_text(json.dumps(index))

        # Create content file
        content_file = temp_data_dir / "blog_content.md"
        content_file.write_text("# Blog Post\n\n" + "x" * 100)

        with patch(
            "sys.argv",
            [
                "save_blog_post.py",
                "--paper-id",
                paper_id,
                "--content-file",
                str(content_file),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0
