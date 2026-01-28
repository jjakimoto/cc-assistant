"""Tests for export_papers.py script."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "paper-exporter" / "scripts"))

from export_papers import (
    export_csv,
    export_json,
    export_markdown,
    filter_papers,
    load_index,
    load_paper,
    load_summary,
    main,
    parse_timespan,
    tokenize,
    validate_arxiv_id,
    validate_format,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_4digit_id(self) -> None:
        """Test valid 4-digit arXiv IDs."""
        assert validate_arxiv_id("2401.1234") is True
        assert validate_arxiv_id("2312.5678") is True

    def test_valid_5digit_id(self) -> None:
        """Test valid 5-digit arXiv IDs."""
        assert validate_arxiv_id("2401.12345") is True
        assert validate_arxiv_id("2312.00001") is True

    def test_invalid_id_path_traversal(self) -> None:
        """Test that path traversal attempts are rejected."""
        assert validate_arxiv_id("../../../etc/passwd") is False
        assert validate_arxiv_id("2401.12345/../../../") is False

    def test_invalid_id_format(self) -> None:
        """Test various invalid ID formats."""
        assert validate_arxiv_id("") is False
        assert validate_arxiv_id("invalid") is False
        assert validate_arxiv_id("2401.123") is False  # Too short
        assert validate_arxiv_id("2401.123456") is False  # Too long
        assert validate_arxiv_id("240112345") is False  # No dot


class TestValidateFormat:
    """Tests for validate_format function."""

    def test_valid_formats(self) -> None:
        """Test valid format strings."""
        assert validate_format("markdown") == "markdown"
        assert validate_format("json") == "json"
        assert validate_format("csv") == "csv"

    def test_case_insensitive(self) -> None:
        """Test that format validation is case-insensitive."""
        assert validate_format("MARKDOWN") == "markdown"
        assert validate_format("JSON") == "json"
        assert validate_format("Csv") == "csv"

    def test_invalid_format(self) -> None:
        """Test that invalid formats raise error."""
        import argparse

        with pytest.raises(argparse.ArgumentTypeError):
            validate_format("pdf")
        with pytest.raises(argparse.ArgumentTypeError):
            validate_format("xml")
        with pytest.raises(argparse.ArgumentTypeError):
            validate_format("")


class TestParseTimespan:
    """Tests for parse_timespan function."""

    def test_parse_days(self) -> None:
        """Test parsing day format."""
        assert parse_timespan("1d") == timedelta(days=1)
        assert parse_timespan("7d") == timedelta(days=7)
        assert parse_timespan("30d") == timedelta(days=30)

    def test_parse_weeks(self) -> None:
        """Test parsing week format."""
        assert parse_timespan("1w") == timedelta(weeks=1)
        assert parse_timespan("2w") == timedelta(weeks=2)

    def test_parse_hours(self) -> None:
        """Test parsing hour format."""
        assert parse_timespan("24h") == timedelta(hours=24)
        assert parse_timespan("48h") == timedelta(hours=48)

    def test_parse_months(self) -> None:
        """Test parsing month format (approximated as 30 days)."""
        assert parse_timespan("1m") == timedelta(days=30)
        assert parse_timespan("2m") == timedelta(days=60)

    def test_case_insensitive(self) -> None:
        """Test that parsing is case insensitive."""
        assert parse_timespan("7D") == timedelta(days=7)
        assert parse_timespan("1W") == timedelta(weeks=1)

    def test_invalid_format(self) -> None:
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError):
            parse_timespan("invalid")
        with pytest.raises(ValueError):
            parse_timespan("7")
        with pytest.raises(ValueError):
            parse_timespan("")

    def test_zero_value(self) -> None:
        """Test that zero value raises ValueError."""
        with pytest.raises(ValueError):
            parse_timespan("0d")


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_valid_index(self, temp_data_dir: Path) -> None:
        """Test loading a valid index file."""
        index_data: dict[str, object] = {
            "version": "1.0",
            "updated_at": "2026-01-27T10:00:00Z",
            "papers": {"2401.12345": {"title": "Test Paper"}},
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        result = load_index(temp_data_dir)
        assert result == index_data

    def test_load_missing_index(self, temp_data_dir: Path) -> None:
        """Test loading when index file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_index(temp_data_dir)

    def test_load_invalid_json(self, temp_data_dir: Path) -> None:
        """Test loading invalid JSON file."""
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            f.write("invalid json")

        with pytest.raises(json.JSONDecodeError):
            load_index(temp_data_dir)


class TestLoadPaper:
    """Tests for load_paper function."""

    def test_load_valid_paper(self, temp_data_dir: Path) -> None:
        """Test loading valid paper metadata."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, object] = {"title": "Test Paper", "authors": ["Smith"]}
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        result = load_paper(paper_id, temp_data_dir)
        assert result == metadata

    def test_load_missing_paper(self, temp_data_dir: Path) -> None:
        """Test loading when paper doesn't exist."""
        result = load_paper("2401.12345", temp_data_dir)
        assert result is None

    def test_load_paper_invalid_id(self, temp_data_dir: Path) -> None:
        """Test that invalid IDs are rejected."""
        result = load_paper("../../../etc/passwd", temp_data_dir)
        assert result is None


class TestLoadSummary:
    """Tests for load_summary function."""

    def test_load_valid_summary(self, temp_data_dir: Path) -> None:
        """Test loading valid summary file."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        summary_content = "# Test Paper\n\n## Problem\nThis is a test."
        (paper_dir / "summary.md").write_text(summary_content)

        result = load_summary(paper_id, temp_data_dir)
        assert result == summary_content

    def test_load_missing_summary(self, temp_data_dir: Path) -> None:
        """Test loading when summary file doesn't exist."""
        result = load_summary("2401.12345", temp_data_dir)
        assert result is None

    def test_load_summary_invalid_id(self, temp_data_dir: Path) -> None:
        """Test that invalid IDs are rejected."""
        result = load_summary("../../../etc/passwd", temp_data_dir)
        assert result is None


class TestTokenize:
    """Tests for tokenize function."""

    def test_basic_tokenization(self) -> None:
        """Test basic word tokenization."""
        tokens = tokenize("Hello World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_removes_punctuation(self) -> None:
        """Test that punctuation is removed."""
        tokens = tokenize("Hello, World! How are you?")
        assert "hello" in tokens
        assert "world" in tokens
        # Check no punctuation tokens
        assert "," not in tokens
        assert "!" not in tokens

    def test_lowercase(self) -> None:
        """Test that tokens are lowercased."""
        tokens = tokenize("UPPERCASE MiXeD")
        assert "uppercase" in tokens
        assert "mixed" in tokens

    def test_filters_short_words(self) -> None:
        """Test that single-char words are filtered (except common ones)."""
        tokens = tokenize("I am a developer")
        assert "am" in tokens
        assert "developer" in tokens


class TestFilterPapers:
    """Tests for filter_papers function."""

    def test_filter_all_papers(self) -> None:
        """Test filtering all papers without constraints."""
        papers: dict[str, dict[str, object]] = {
            "2401.12345": {"title": "Paper 1"},
            "2401.12346": {"title": "Paper 2"},
        }

        filtered = filter_papers(papers)
        assert len(filtered) == 2

    def test_filter_by_paper_id(self) -> None:
        """Test filtering by specific paper ID."""
        papers: dict[str, dict[str, object]] = {
            "2401.12345": {"title": "Paper 1"},
            "2401.12346": {"title": "Paper 2"},
        }

        filtered = filter_papers(papers, paper_id="2401.12345")
        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"

    def test_filter_by_query(self) -> None:
        """Test filtering by search query."""
        papers: dict[str, dict[str, object]] = {
            "2401.12345": {"title": "Attention Mechanisms", "abstract": "", "topics": []},
            "2401.12346": {"title": "Transformer Models", "abstract": "", "topics": []},
        }

        filtered = filter_papers(papers, query="attention")
        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"

    def test_filter_by_date(self) -> None:
        """Test filtering by collection date."""
        now = datetime.now(timezone.utc)
        papers: dict[str, dict[str, object]] = {
            "2401.12345": {
                "title": "Recent Paper",
                "collected_at": (now - timedelta(days=1)).isoformat(),
            },
            "2401.12346": {
                "title": "Old Paper",
                "collected_at": (now - timedelta(days=30)).isoformat(),
            },
        }

        since = now - timedelta(days=7)
        filtered = filter_papers(papers, since=since)

        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"

    def test_filter_invalid_ids(self) -> None:
        """Test that invalid IDs are filtered out."""
        papers: dict[str, dict[str, object]] = {
            "2401.12345": {"title": "Valid Paper"},
            "../invalid": {"title": "Invalid ID"},
        }

        filtered = filter_papers(papers)
        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"

    def test_filter_combined(self) -> None:
        """Test combining multiple filters."""
        now = datetime.now(timezone.utc)
        papers: dict[str, dict[str, object]] = {
            "2401.12345": {
                "title": "Attention Paper",
                "abstract": "",
                "topics": [],
                "collected_at": (now - timedelta(days=1)).isoformat(),
            },
            "2401.12346": {
                "title": "Attention Old",
                "abstract": "",
                "topics": [],
                "collected_at": (now - timedelta(days=30)).isoformat(),
            },
            "2401.12347": {
                "title": "Transformer New",
                "abstract": "",
                "topics": [],
                "collected_at": (now - timedelta(days=1)).isoformat(),
            },
        }

        since = now - timedelta(days=7)
        filtered = filter_papers(papers, query="attention", since=since)

        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"


class TestExportMarkdown:
    """Tests for export_markdown function."""

    def test_export_single_paper(self, temp_data_dir: Path) -> None:
        """Test exporting single paper to Markdown."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, object] = {
            "id": paper_id,
            "title": "Test Paper",
            "authors": ["Smith", "Jones"],
            "abstract": "Test abstract",
            "published": "2024-01-15",
            "categories": ["cs.CL"],
        }
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        papers: list[tuple[str, dict[str, object]]] = [(paper_id, {"title": "Test Paper"})]
        output_dir = temp_data_dir / "exports" / "markdown"

        count = export_markdown(papers, output_dir, False, temp_data_dir)

        assert count == 1
        assert (output_dir / f"paper_{paper_id}.md").exists()

        content = (output_dir / f"paper_{paper_id}.md").read_text()
        assert "Test Paper" in content
        assert "Smith" in content
        assert "2401.12345" in content

    def test_export_with_summary(self, temp_data_dir: Path) -> None:
        """Test exporting paper with summary included."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, object] = {
            "id": paper_id,
            "title": "Test Paper",
            "authors": ["Smith"],
            "abstract": "Test abstract",
        }
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        (paper_dir / "summary.md").write_text("## Summary\nThis is a summary.")

        papers: list[tuple[str, dict[str, object]]] = [(paper_id, {"title": "Test Paper"})]
        output_dir = temp_data_dir / "exports" / "markdown"

        count = export_markdown(papers, output_dir, True, temp_data_dir)

        assert count == 1
        content = (output_dir / f"paper_{paper_id}.md").read_text()
        assert "This is a summary" in content


class TestExportJson:
    """Tests for export_json function."""

    def test_export_papers(self, temp_data_dir: Path) -> None:
        """Test exporting papers to JSON."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, object] = {
            "id": paper_id,
            "title": "Test Paper",
            "authors": ["Smith"],
            "abstract": "Test abstract",
        }
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        papers: list[tuple[str, dict[str, object]]] = [(paper_id, {"title": "Test Paper"})]
        output_dir = temp_data_dir / "exports" / "json"

        count = export_json(papers, output_dir, False, temp_data_dir)

        assert count == 1
        assert (output_dir / "papers.json").exists()

        with (output_dir / "papers.json").open() as f:
            data = json.load(f)

        assert data["count"] == 1
        assert len(data["papers"]) == 1
        assert data["papers"][0]["title"] == "Test Paper"

    def test_export_with_summary(self, temp_data_dir: Path) -> None:
        """Test exporting with summary included."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, object] = {"id": paper_id, "title": "Test Paper"}
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        (paper_dir / "summary.md").write_text("This is a summary.")

        papers: list[tuple[str, dict[str, object]]] = [(paper_id, {})]
        output_dir = temp_data_dir / "exports" / "json"

        count = export_json(papers, output_dir, True, temp_data_dir)

        assert count == 1
        with (output_dir / "papers.json").open() as f:
            data = json.load(f)

        assert "summary_content" in data["papers"][0]
        assert data["papers"][0]["summary_content"] == "This is a summary."


class TestExportCsv:
    """Tests for export_csv function."""

    def test_export_papers(self, temp_data_dir: Path) -> None:
        """Test exporting papers to CSV."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata: dict[str, object] = {
            "id": paper_id,
            "title": "Test Paper",
            "authors": ["Smith", "Jones"],
            "published": "2024-01-15",
            "categories": ["cs.CL", "cs.AI"],
            "has_summary": True,
            "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
            "collected_at": "2026-01-27T10:00:00Z",
        }
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        papers: list[tuple[str, dict[str, object]]] = [(paper_id, {})]
        output_dir = temp_data_dir / "exports" / "csv"

        count = export_csv(papers, output_dir, temp_data_dir)

        assert count == 1
        assert (output_dir / "papers.csv").exists()

        with (output_dir / "papers.csv").open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["id"] == paper_id
        assert rows[0]["title"] == "Test Paper"
        assert "Smith" in rows[0]["authors"]
        assert "Jones" in rows[0]["authors"]


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_export_all_markdown(self, temp_data_dir: Path) -> None:
        """Test --all with markdown format."""
        # Create index with a paper
        index_data: dict[str, object] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Test Paper"}},
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Create paper metadata
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump({"title": "Test Paper", "authors": []}, f)

        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "markdown",
                "--all",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_export_single_paper(self, temp_data_dir: Path) -> None:
        """Test --paper-id argument."""
        # Create index with a paper
        index_data: dict[str, object] = {
            "version": "1.0",
            "papers": {"2401.12345": {"title": "Test Paper"}},
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Create paper metadata
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump({"title": "Test Paper", "authors": []}, f)

        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "json",
                "--paper-id",
                "2401.12345",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_export_with_query(self, temp_data_dir: Path) -> None:
        """Test --query argument."""
        # Create index with papers
        index_data: dict[str, object] = {
            "version": "1.0",
            "papers": {
                "2401.12345": {
                    "title": "Attention Paper",
                    "abstract": "",
                    "topics": [],
                },
                "2401.12346": {
                    "title": "Transformer Paper",
                    "abstract": "",
                    "topics": [],
                },
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "csv",
                "--query",
                "attention",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test invalid paper ID format."""
        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "markdown",
                "--paper-id",
                "invalid",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1  # Should fail

    def test_missing_index(self, temp_data_dir: Path) -> None:
        """Test with missing index file."""
        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "json",
                "--all",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 1  # Should fail


class TestEmptyCollection:
    """Tests for empty collection handling."""

    def test_empty_index(self, temp_data_dir: Path) -> None:
        """Test export with empty index."""
        index_data: dict[str, object] = {"version": "1.0", "papers": {}}
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "markdown",
                "--all",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0  # Should succeed with message

    def test_no_matching_papers(self, temp_data_dir: Path) -> None:
        """Test when query matches no papers."""
        index_data: dict[str, object] = {
            "version": "1.0",
            "papers": {
                "2401.12345": {
                    "title": "Transformer Paper",
                    "abstract": "",
                    "topics": [],
                },
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "json",
                "--query",
                "nonexistent",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0  # Should succeed with message


class TestDateFilter:
    """Tests for date filtering."""

    def test_since_filter(self, temp_data_dir: Path) -> None:
        """Test --since filter."""
        now = datetime.now(timezone.utc)

        index_data: dict[str, object] = {
            "version": "1.0",
            "papers": {
                "2401.12345": {
                    "title": "Recent Paper",
                    "collected_at": (now - timedelta(days=1)).isoformat(),
                },
                "2401.12346": {
                    "title": "Old Paper",
                    "collected_at": (now - timedelta(days=30)).isoformat(),
                },
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Create paper metadata
        for pid in ["2401.12345", "2401.12346"]:
            paper_dir = temp_data_dir / "papers" / pid
            paper_dir.mkdir(parents=True)
            with (paper_dir / "metadata.json").open("w") as f:
                json.dump({"title": "Test", "authors": []}, f)

        output_dir = temp_data_dir / "exports" / "json"

        with patch(
            "sys.argv",
            [
                "export_papers.py",
                "--format",
                "json",
                "--all",
                "--since",
                "7d",
                "--output",
                str(output_dir),
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            result = main()
            assert result == 0

        # Check only recent paper was exported
        with (output_dir / "papers.json").open() as f:
            data = json.load(f)
        assert data["count"] == 1
