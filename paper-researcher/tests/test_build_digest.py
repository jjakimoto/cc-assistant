"""Tests for build_digest.py script."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-digest" / "scripts")
)

from build_digest import (
    build_digest_content,
    extract_snippet,
    filter_papers,
    group_by_topic,
    load_index,
    load_metadata,
    load_summary,
    main,
    parse_timespan,
    validate_arxiv_id,
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


class TestParseTimespan:
    """Tests for parse_timespan function."""

    def test_parse_days(self) -> None:
        """Test parsing day format."""
        assert parse_timespan("1d") == timedelta(days=1)
        assert parse_timespan("7d") == timedelta(days=7)
        assert parse_timespan("30d") == timedelta(days=30)
        assert parse_timespan("14d") == timedelta(days=14)

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

    def test_with_whitespace(self) -> None:
        """Test that whitespace is handled."""
        assert parse_timespan("  7d  ") == timedelta(days=7)

    def test_invalid_format(self) -> None:
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError):
            parse_timespan("invalid")
        with pytest.raises(ValueError):
            parse_timespan("7")
        with pytest.raises(ValueError):
            parse_timespan("d7")
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
        index_data = {
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


class TestLoadMetadata:
    """Tests for load_metadata function."""

    def test_load_valid_metadata(self, temp_data_dir: Path) -> None:
        """Test loading valid metadata file."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        metadata = {"title": "Test Paper", "topics": ["Testing"]}
        with (paper_dir / "metadata.json").open("w") as f:
            json.dump(metadata, f)

        result = load_metadata(paper_id, temp_data_dir)
        assert result == metadata

    def test_load_missing_metadata(self, temp_data_dir: Path) -> None:
        """Test loading when metadata file doesn't exist."""
        result = load_metadata("2401.12345", temp_data_dir)
        assert result is None

    def test_load_invalid_json_metadata(self, temp_data_dir: Path) -> None:
        """Test loading invalid JSON metadata file."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        with (paper_dir / "metadata.json").open("w") as f:
            f.write("invalid json")

        result = load_metadata(paper_id, temp_data_dir)
        assert result is None  # Should return None, not raise

    def test_load_metadata_invalid_id(self, temp_data_dir: Path) -> None:
        """Test that invalid IDs are rejected."""
        result = load_metadata("../../../etc/passwd", temp_data_dir)
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


class TestExtractSnippet:
    """Tests for extract_snippet function."""

    def test_extract_problem_section(self) -> None:
        """Test extracting the Problem section."""
        summary = """# Test Paper

**Authors:** Smith

## Problem
This paper addresses the challenge of LLM agent coordination.

## Method
We propose a novel framework.
"""
        snippet = extract_snippet(summary)
        assert "LLM agent coordination" in snippet

    def test_fallback_to_content(self) -> None:
        """Test fallback when no Problem section."""
        summary = """# Test Paper

This paper presents research findings about attention mechanisms.
"""
        snippet = extract_snippet(summary)
        assert "attention mechanisms" in snippet

    def test_truncation(self) -> None:
        """Test that long snippets are truncated."""
        long_text = "word " * 100
        summary = f"## Problem\n{long_text}"
        snippet = extract_snippet(summary, max_length=50)
        assert len(snippet) <= 55  # 50 + "..."
        assert snippet.endswith("...")

    def test_empty_summary(self) -> None:
        """Test handling empty summary."""
        assert extract_snippet("") == ""
        assert extract_snippet(None) == ""  # type: ignore[arg-type]


class TestFilterPapers:
    """Tests for filter_papers function."""

    def test_filter_by_date(self) -> None:
        """Test filtering papers by collection date."""
        now = datetime.now(timezone.utc)
        papers = {
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
        filtered = filter_papers(papers, since, now)

        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"

    def test_filter_invalid_ids(self) -> None:
        """Test that invalid IDs are filtered out."""
        now = datetime.now(timezone.utc)
        papers = {
            "2401.12345": {
                "title": "Valid Paper",
                "collected_at": now.isoformat(),
            },
            "../invalid": {
                "title": "Invalid ID",
                "collected_at": now.isoformat(),
            },
        }

        since = now - timedelta(days=7)
        filtered = filter_papers(papers, since, now)

        assert len(filtered) == 1
        assert filtered[0][0] == "2401.12345"

    def test_filter_missing_collected_at(self) -> None:
        """Test that papers without collected_at are excluded."""
        now = datetime.now(timezone.utc)
        papers = {
            "2401.12345": {"title": "No Date"},
        }

        since = now - timedelta(days=7)
        filtered = filter_papers(papers, since, now)

        assert len(filtered) == 0

    def test_filter_sorted_by_date(self) -> None:
        """Test that filtered papers are sorted by date (newest first)."""
        now = datetime.now(timezone.utc)
        papers = {
            "2401.12345": {
                "title": "Older Paper",
                "collected_at": (now - timedelta(days=3)).isoformat(),
            },
            "2401.12346": {
                "title": "Newest Paper",
                "collected_at": (now - timedelta(days=1)).isoformat(),
            },
            "2401.12347": {
                "title": "Middle Paper",
                "collected_at": (now - timedelta(days=2)).isoformat(),
            },
        }

        since = now - timedelta(days=7)
        filtered = filter_papers(papers, since, now)

        assert len(filtered) == 3
        assert filtered[0][0] == "2401.12346"  # Newest first
        assert filtered[1][0] == "2401.12347"
        assert filtered[2][0] == "2401.12345"


class TestGroupByTopic:
    """Tests for group_by_topic function."""

    def test_group_papers_with_topics(self, temp_data_dir: Path) -> None:
        """Test grouping papers with topics."""
        papers = [
            ("2401.12345", {"title": "Paper 1", "topics": ["LLM Agents"]}),
            ("2401.12346", {"title": "Paper 2", "topics": ["LLM Agents"]}),
            ("2401.12347", {"title": "Paper 3", "topics": ["Transformers"]}),
        ]

        grouped = group_by_topic(papers, temp_data_dir)

        assert "LLM Agents" in grouped
        assert "Transformers" in grouped
        assert len(grouped["LLM Agents"]) == 2
        assert len(grouped["Transformers"]) == 1

    def test_group_papers_uncategorized(self, temp_data_dir: Path) -> None:
        """Test that papers without topics go to Uncategorized."""
        papers = [
            ("2401.12345", {"title": "Paper 1", "topics": []}),
        ]

        grouped = group_by_topic(papers, temp_data_dir)

        assert "Uncategorized" in grouped
        assert len(grouped["Uncategorized"]) == 1

    def test_uncategorized_last(self, temp_data_dir: Path) -> None:
        """Test that Uncategorized is sorted last."""
        papers = [
            ("2401.12345", {"title": "Paper 1", "topics": []}),
            ("2401.12346", {"title": "Paper 2", "topics": ["Zebra Topic"]}),
            ("2401.12347", {"title": "Paper 3", "topics": ["Alpha Topic"]}),
        ]

        grouped = group_by_topic(papers, temp_data_dir)
        topic_list = list(grouped.keys())

        assert topic_list[-1] == "Uncategorized"
        assert topic_list[0] == "Alpha Topic"


class TestBuildDigestContent:
    """Tests for build_digest_content function."""

    def test_build_content_with_papers(self, temp_data_dir: Path) -> None:
        """Test building digest content."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)
        grouped = {
            "LLM Agents": [
                (
                    "2401.12345",
                    {
                        "title": "Test Paper",
                        "authors": ["Smith", "Jones"],
                        "has_summary": False,
                        "abstract": "A test abstract.",
                    },
                ),
            ],
        }

        content = build_digest_content(grouped, since, now, temp_data_dir)

        assert "# Research Paper Digest" in content
        assert "LLM Agents" in content
        assert "Test Paper" in content
        assert "Smith" in content

    def test_build_content_empty(self, temp_data_dir: Path) -> None:
        """Test building content with no papers."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        content = build_digest_content({}, since, now, temp_data_dir)

        assert "# Research Paper Digest" in content
        assert "No papers collected in this time period" in content


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_default_arguments(self, temp_data_dir: Path) -> None:
        """Test default argument values."""
        # Create empty index
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump({"version": "1.0", "papers": {}}, f)

        with patch(
            "sys.argv", ["build_digest.py", "--data-dir", str(temp_data_dir)]
        ):
            result = main()
            assert result == 0

    def test_since_argument(self, temp_data_dir: Path) -> None:
        """Test --since argument."""
        # Create empty index
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump({"version": "1.0", "papers": {}}, f)

        with patch(
            "sys.argv",
            ["build_digest.py", "--since", "14d", "--data-dir", str(temp_data_dir)],
        ):
            result = main()
            assert result == 0

    def test_invalid_since_argument(self, temp_data_dir: Path) -> None:
        """Test invalid --since argument."""
        # Create empty index
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump({"version": "1.0", "papers": {}}, f)

        with patch(
            "sys.argv",
            ["build_digest.py", "--since", "invalid", "--data-dir", str(temp_data_dir)],
        ):
            result = main()
            assert result == 1  # Should fail


class TestMainFunction:
    """Tests for main function integration."""

    def test_main_with_papers(self, temp_data_dir: Path) -> None:
        """Test main function with papers in index."""
        now = datetime.now(timezone.utc)

        # Create index with a recent paper
        index_data = {
            "version": "1.0",
            "updated_at": now.isoformat(),
            "papers": {
                "2401.12345": {
                    "title": "Test Paper",
                    "authors": ["Smith"],
                    "abstract": "Test abstract",
                    "topics": ["Testing"],
                    "collected_at": (now - timedelta(hours=1)).isoformat(),
                    "has_summary": False,
                },
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        # Create digests directory
        (temp_data_dir / "digests").mkdir(exist_ok=True)

        with patch(
            "sys.argv", ["build_digest.py", "--data-dir", str(temp_data_dir)]
        ):
            result = main()
            assert result == 0

        # Check digest was created
        digest_files = list((temp_data_dir / "digests").glob("*.md"))
        assert len(digest_files) == 1

    def test_main_no_papers_in_range(self, temp_data_dir: Path) -> None:
        """Test main function with no papers in date range."""
        now = datetime.now(timezone.utc)

        # Create index with an old paper
        index_data = {
            "version": "1.0",
            "papers": {
                "2401.12345": {
                    "title": "Old Paper",
                    "collected_at": (now - timedelta(days=30)).isoformat(),
                },
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        with patch(
            "sys.argv",
            ["build_digest.py", "--since", "1d", "--data-dir", str(temp_data_dir)],
        ):
            result = main()
            assert result == 0  # Should succeed with message

    def test_main_missing_index(self, temp_data_dir: Path) -> None:
        """Test main function with missing index file."""
        with patch(
            "sys.argv", ["build_digest.py", "--data-dir", str(temp_data_dir)]
        ):
            result = main()
            assert result == 1  # Should fail
