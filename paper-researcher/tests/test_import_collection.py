"""Tests for import_collection.py script."""

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

from import_collection import (
    import_package,
    load_index,
    main,
    save_index,
    validate_arxiv_id,
    validate_manifest,
    validate_zip_path,
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


class TestValidateZipPath:
    """Tests for validate_zip_path function."""

    def test_valid_paths(self) -> None:
        """Test valid ZIP paths."""
        assert validate_zip_path("papers/2401.12345/metadata.json") is True
        assert validate_zip_path("manifest.json") is True
        assert validate_zip_path("index/papers.json") is True

    def test_path_traversal_rejected(self) -> None:
        """Test path traversal is rejected."""
        assert validate_zip_path("../etc/passwd") is False
        assert validate_zip_path("papers/../../../etc/passwd") is False

    def test_absolute_paths_rejected(self) -> None:
        """Test absolute paths are rejected."""
        assert validate_zip_path("/etc/passwd") is False
        assert validate_zip_path("\\windows\\system32") is False

    def test_windows_paths_rejected(self) -> None:
        """Test Windows-style paths are rejected."""
        assert validate_zip_path("C:\\Windows\\System32") is False


class TestValidateManifest:
    """Tests for validate_manifest function."""

    def test_valid_manifest(self) -> None:
        """Test valid manifest."""
        manifest: dict[str, Any] = {
            "version": "1.0",
            "created_at": "2026-01-27T10:00:00Z",
            "paper_count": 5,
        }
        is_valid, error = validate_manifest(manifest)
        assert is_valid is True
        assert error == ""

    def test_missing_version(self) -> None:
        """Test missing version field."""
        manifest: dict[str, Any] = {
            "created_at": "2026-01-27T10:00:00Z",
            "paper_count": 5,
        }
        is_valid, error = validate_manifest(manifest)
        assert is_valid is False
        assert "version" in error

    def test_missing_paper_count(self) -> None:
        """Test missing paper_count field."""
        manifest: dict[str, Any] = {
            "version": "1.0",
            "created_at": "2026-01-27T10:00:00Z",
        }
        is_valid, error = validate_manifest(manifest)
        assert is_valid is False
        assert "paper_count" in error

    def test_invalid_paper_count_type(self) -> None:
        """Test paper_count must be integer."""
        manifest: dict[str, Any] = {
            "version": "1.0",
            "created_at": "2026-01-27T10:00:00Z",
            "paper_count": "five",
        }
        is_valid, error = validate_manifest(manifest)
        assert is_valid is False
        assert "integer" in error

    def test_negative_paper_count(self) -> None:
        """Test paper_count must be non-negative."""
        manifest: dict[str, Any] = {
            "version": "1.0",
            "created_at": "2026-01-27T10:00:00Z",
            "paper_count": -1,
        }
        is_valid, error = validate_manifest(manifest)
        assert is_valid is False
        assert "non-negative" in error


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_existing_index(self, temp_data_dir: Path) -> None:
        """Test loading existing index."""
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Test"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        index = load_index(temp_data_dir)
        assert "2401.12345" in index["papers"]

    def test_missing_index_returns_empty(self, temp_data_dir: Path) -> None:
        """Test missing index returns empty structure."""
        index = load_index(temp_data_dir)
        assert index["papers"] == {}


class TestSaveIndex:
    """Tests for save_index function."""

    def test_save_index(self, temp_data_dir: Path) -> None:
        """Test saving index."""
        index: dict[str, Any] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Test"}},
        }

        save_index(index, temp_data_dir)

        index_path = temp_data_dir / "index" / "papers.json"
        assert index_path.exists()

        saved = json.loads(index_path.read_text(encoding="utf-8"))
        assert "2401.12345" in saved["papers"]
        assert "updated_at" in saved


class TestImportPackage:
    """Tests for import_package function."""

    def create_test_package(
        self,
        output_path: Path,
        paper_ids: list[str],
        include_summary: bool = False,
        include_annotations: bool = False,
    ) -> None:
        """Helper to create test ZIP package."""
        with zipfile.ZipFile(output_path, "w") as zf:
            # Add manifest
            manifest: dict[str, Any] = {
                "version": "1.0",
                "created_at": "2026-01-27T10:00:00Z",
                "created_by": "test",
                "paper_count": len(paper_ids),
            }
            zf.writestr("manifest.json", json.dumps(manifest))

            # Add papers
            for paper_id in paper_ids:
                metadata: dict[str, Any] = {
                    "id": paper_id,
                    "title": f"Paper {paper_id}",
                    "authors": ["Test Author"],
                    "abstract": "Test abstract",
                    "collected_at": "2026-01-27T10:00:00Z",
                }
                zf.writestr(
                    f"papers/{paper_id}/metadata.json",
                    json.dumps(metadata),
                )

                if include_summary:
                    zf.writestr(
                        f"papers/{paper_id}/summary.md",
                        "# Summary\n\nTest summary.",
                    )

                if include_annotations:
                    annotation: dict[str, Any] = {"id": "abc", "content": "Note"}
                    zf.writestr(
                        f"papers/{paper_id}/annotations/note.json",
                        json.dumps(annotation),
                    )

            # Add index
            index_data: dict[str, Any] = {
                "version": "1.0",
                "papers": {pid: {"title": f"Paper {pid}"} for pid in paper_ids},
            }
            zf.writestr("index/papers.json", json.dumps(index_data))

    def test_import_basic_package(self, temp_data_dir: Path) -> None:
        """Test importing a basic package."""
        package_path = temp_data_dir / "test.zip"
        self.create_test_package(package_path, ["2401.12345"])

        imported, skipped, annotations, ids = import_package(
            package_path, temp_data_dir, overwrite=False
        )

        assert imported == 1
        assert skipped == 0
        assert "2401.12345" in ids

        # Verify paper was imported
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        assert paper_dir.exists()
        assert (paper_dir / "metadata.json").exists()

    def test_import_with_summaries(self, temp_data_dir: Path) -> None:
        """Test importing package with summaries."""
        package_path = temp_data_dir / "test.zip"
        self.create_test_package(package_path, ["2401.12345"], include_summary=True)

        import_package(package_path, temp_data_dir, overwrite=False)

        # Verify summary was imported
        summary_path = temp_data_dir / "papers" / "2401.12345" / "summary.md"
        assert summary_path.exists()

    def test_import_with_annotations(self, temp_data_dir: Path) -> None:
        """Test importing package with annotations."""
        package_path = temp_data_dir / "test.zip"
        self.create_test_package(
            package_path, ["2401.12345"], include_annotations=True
        )

        imported, skipped, annotations, ids = import_package(
            package_path, temp_data_dir, overwrite=False
        )

        assert annotations == 1

        # Verify annotation was imported
        ann_dir = temp_data_dir / "papers" / "2401.12345" / "annotations"
        assert ann_dir.exists()
        assert len(list(ann_dir.glob("*.json"))) == 1

    def test_skip_duplicate_papers(self, temp_data_dir: Path) -> None:
        """Test skipping duplicate papers."""
        # Create existing paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Existing Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Existing Paper"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        # Create package with same paper
        package_path = temp_data_dir / "test.zip"
        self.create_test_package(package_path, ["2401.12345"])

        imported, skipped, annotations, ids = import_package(
            package_path, temp_data_dir, overwrite=False
        )

        assert imported == 0
        assert skipped == 1

    def test_overwrite_duplicate_papers(self, temp_data_dir: Path) -> None:
        """Test overwriting duplicate papers."""
        # Create existing paper
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata: dict[str, Any] = {"id": "2401.12345", "title": "Existing Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        # Create index
        index_dir = temp_data_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_data: dict[str, Any] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Existing Paper"}},
        }
        (index_dir / "papers.json").write_text(json.dumps(index_data), encoding="utf-8")

        # Create package with same paper
        package_path = temp_data_dir / "test.zip"
        self.create_test_package(package_path, ["2401.12345"])

        imported, skipped, annotations, ids = import_package(
            package_path, temp_data_dir, overwrite=True
        )

        assert imported == 1
        assert skipped == 0

    def test_missing_package(self, temp_data_dir: Path) -> None:
        """Test error for missing package."""
        package_path = temp_data_dir / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            import_package(package_path, temp_data_dir, overwrite=False)

    def test_invalid_package_no_manifest(self, temp_data_dir: Path) -> None:
        """Test error for package without manifest."""
        package_path = temp_data_dir / "test.zip"

        with zipfile.ZipFile(package_path, "w") as zf:
            zf.writestr("papers/2401.12345/metadata.json", "{}")

        with pytest.raises(ValueError, match="manifest"):
            import_package(package_path, temp_data_dir, overwrite=False)

    def test_path_traversal_rejected(self, temp_data_dir: Path) -> None:
        """Test path traversal in ZIP is rejected."""
        package_path = temp_data_dir / "test.zip"

        with zipfile.ZipFile(package_path, "w") as zf:
            manifest: dict[str, Any] = {
                "version": "1.0",
                "created_at": "2026-01-27",
                "paper_count": 1,
            }
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("../../../etc/passwd", "malicious")

        with pytest.raises(ValueError, match="Invalid path"):
            import_package(package_path, temp_data_dir, overwrite=False)


class TestMainFunction:
    """Tests for CLI interface."""

    def create_test_package(self, output_path: Path) -> None:
        """Helper to create test package."""
        with zipfile.ZipFile(output_path, "w") as zf:
            manifest: dict[str, Any] = {
                "version": "1.0",
                "created_at": "2026-01-27",
                "paper_count": 1,
            }
            zf.writestr("manifest.json", json.dumps(manifest))

            metadata: dict[str, Any] = {
                "id": "2401.12345",
                "title": "Test Paper",
                "authors": [],
                "abstract": "",
                "collected_at": "2026-01-27",
            }
            zf.writestr("papers/2401.12345/metadata.json", json.dumps(metadata))

            index_data: dict[str, Any] = {
                "version": "1.0",
                "papers": {"2401.12345": {"title": "Test"}},
            }
            zf.writestr("index/papers.json", json.dumps(index_data))

    def test_valid_import(self, temp_data_dir: Path) -> None:
        """Test valid import."""
        package_path = temp_data_dir / "test.zip"
        self.create_test_package(package_path)

        with patch(
            "sys.argv",
            [
                "import_collection.py",
                "--input",
                str(package_path),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_missing_file(self, temp_data_dir: Path) -> None:
        """Test error for missing file."""
        with patch(
            "sys.argv",
            [
                "import_collection.py",
                "--input",
                str(temp_data_dir / "nonexistent.zip"),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1

    def test_invalid_zip(self, temp_data_dir: Path) -> None:
        """Test error for invalid ZIP."""
        bad_file = temp_data_dir / "bad.zip"
        bad_file.write_text("not a zip file")

        with patch(
            "sys.argv",
            [
                "import_collection.py",
                "--input",
                str(bad_file),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1
