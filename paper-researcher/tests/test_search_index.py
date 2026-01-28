"""Unit tests for search_index.py."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-searcher" / "scripts")
)

from search_index import (
    calculate_relevance,
    count_matches,
    extract_excerpt,
    load_index,
    load_summary,
    main,
    positive_int,
    search_papers,
    tokenize,
    validate_arxiv_id,
)


class TestPositiveInt:
    """Tests for positive_int argparse type."""

    def test_valid_positive_integer(self) -> None:
        """Test valid positive integer conversion."""
        assert positive_int("1") == 1
        assert positive_int("10") == 10
        assert positive_int("100") == 100

    def test_zero_raises_error(self) -> None:
        """Test that zero raises ArgumentTypeError."""
        import argparse

        with pytest.raises(argparse.ArgumentTypeError, match="not a positive integer"):
            positive_int("0")

    def test_negative_raises_error(self) -> None:
        """Test that negative values raise ArgumentTypeError."""
        import argparse

        with pytest.raises(argparse.ArgumentTypeError, match="not a positive integer"):
            positive_int("-1")


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_arxiv_id(self) -> None:
        """Test valid arXiv ID formats."""
        assert validate_arxiv_id("2401.12345")
        assert validate_arxiv_id("2401.1234")
        assert validate_arxiv_id("9912.00001")

    def test_invalid_arxiv_id_format(self) -> None:
        """Test invalid arXiv ID formats."""
        assert not validate_arxiv_id("")
        assert not validate_arxiv_id("invalid")
        assert not validate_arxiv_id("12345")
        assert not validate_arxiv_id("2401.123")  # Too short
        assert not validate_arxiv_id("2401.123456")  # Too long
        assert not validate_arxiv_id("24a1.12345")  # Contains letter

    def test_path_traversal_rejected(self) -> None:
        """Test that path traversal attempts are rejected."""
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "2401.12345/../../../etc/passwd",
            "2401.12345/../../secret",
        ]
        for malicious_id in malicious_ids:
            assert not validate_arxiv_id(malicious_id)


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_valid_index(self, temp_data_dir: Path) -> None:
        """Test loading a valid index file."""
        index_data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "papers": {
                "2401.12345": {
                    "title": "Test Paper",
                    "authors": ["Author 1"],
                    "abstract": "Test abstract",
                    "topics": ["test"],
                    "has_summary": False,
                }
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index_data, f)

        result = load_index(temp_data_dir)

        assert result["version"] == "1.0"
        assert "2401.12345" in result["papers"]

    def test_load_missing_index_raises_error(self, temp_data_dir: Path) -> None:
        """Test that missing index file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_index(temp_data_dir)

    def test_load_invalid_json_raises_error(self, temp_data_dir: Path) -> None:
        """Test that invalid JSON raises JSONDecodeError."""
        index_path = temp_data_dir / "index" / "papers.json"
        index_path.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            load_index(temp_data_dir)


class TestLoadSummary:
    """Tests for load_summary function."""

    def test_load_existing_summary(self, temp_data_dir: Path) -> None:
        """Test loading an existing summary file."""
        paper_id = "2401.12345"
        paper_dir = temp_data_dir / "papers" / paper_id
        paper_dir.mkdir(parents=True)

        summary_content = "# Test Paper\n\nThis is a test summary."
        (paper_dir / "summary.md").write_text(summary_content)

        result = load_summary(paper_id, temp_data_dir)

        assert result == summary_content

    def test_load_missing_summary_returns_none(self, temp_data_dir: Path) -> None:
        """Test that missing summary returns None."""
        result = load_summary("2401.99999", temp_data_dir)
        assert result is None

    def test_malicious_paper_id_rejected(self, temp_data_dir: Path) -> None:
        """Test that path traversal attempts are rejected."""
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "2401.12345/../../../etc/passwd",
        ]
        for malicious_id in malicious_ids:
            result = load_summary(malicious_id, temp_data_dir)
            assert result is None


class TestTokenize:
    """Tests for tokenize function."""

    def test_basic_tokenization(self) -> None:
        """Test basic word tokenization."""
        result = tokenize("Hello World")
        assert result == ["hello", "world"]

    def test_removes_punctuation(self) -> None:
        """Test that punctuation is removed."""
        result = tokenize("Hello, World! How are you?")
        assert "hello" in result
        assert "world" in result
        assert "," not in result

    def test_lowercase_conversion(self) -> None:
        """Test that tokens are lowercase."""
        result = tokenize("LLM Agents TRANSFORMER")
        assert result == ["llm", "agents", "transformer"]

    def test_empty_string(self) -> None:
        """Test tokenization of empty string."""
        result = tokenize("")
        assert result == []

    def test_filters_short_words(self) -> None:
        """Test that very short words are filtered."""
        result = tokenize("a b c the in")
        # Single char words are filtered except 'a' and 'i'
        assert "a" in result
        assert "b" not in result
        assert "in" in result  # 'in' has 2 chars, kept

    def test_handles_numbers(self) -> None:
        """Test that numbers are preserved."""
        result = tokenize("GPT4 is version 2024")
        assert "gpt4" in result
        assert "2024" in result


class TestCountMatches:
    """Tests for count_matches function."""

    def test_single_match(self) -> None:
        """Test counting single match."""
        result = count_matches("This is about attention mechanisms", ["attention"])
        assert result == 1

    def test_multiple_matches(self) -> None:
        """Test counting multiple matches."""
        result = count_matches(
            "Attention and more attention mechanisms",
            ["attention", "mechanisms"],
        )
        assert result == 2

    def test_no_matches(self) -> None:
        """Test counting with no matches."""
        result = count_matches("This is about transformers", ["attention"])
        assert result == 0

    def test_case_insensitive(self) -> None:
        """Test that matching is case-insensitive."""
        result = count_matches("ATTENTION Attention attention", ["attention"])
        assert result == 1  # Counts term presence, not occurrences


class TestCalculateRelevance:
    """Tests for calculate_relevance function."""

    def test_title_match_weighted(self) -> None:
        """Test that title matches are weighted highest."""
        paper = {
            "title": "attention mechanisms study",
            "abstract": "",
            "topics": [],
        }
        score = calculate_relevance(["attention"], paper, None)
        assert score == 3.0  # WEIGHT_TITLE = 3.0

    def test_abstract_match_weighted(self) -> None:
        """Test that abstract matches have medium weight."""
        paper = {
            "title": "some other title",
            "abstract": "attention mechanisms study",
            "topics": [],
        }
        score = calculate_relevance(["attention"], paper, None)
        assert score == 2.0  # WEIGHT_ABSTRACT = 2.0

    def test_summary_match_weighted(self) -> None:
        """Test that summary matches have weight."""
        paper = {
            "title": "some other title",
            "abstract": "some abstract",
            "topics": [],
        }
        score = calculate_relevance(["attention"], paper, "attention mechanisms")
        assert score == 1.5  # WEIGHT_SUMMARY = 1.5

    def test_combined_scores(self) -> None:
        """Test that scores from different fields combine."""
        paper = {
            "title": "attention study",
            "abstract": "about attention",
            "topics": ["attention"],
        }
        score = calculate_relevance(["attention"], paper, "attention summary")
        # title=3.0 + abstract=2.0 + summary=1.5 + topic=1.0 = 7.5
        assert score == 7.5

    def test_no_matches_returns_zero(self) -> None:
        """Test that no matches returns zero score."""
        paper = {
            "title": "transformers",
            "abstract": "about transformers",
            "topics": [],
        }
        score = calculate_relevance(["attention"], paper, None)
        assert score == 0.0

    def test_empty_query_terms(self) -> None:
        """Test that empty query terms returns zero."""
        paper = {"title": "test", "abstract": "test", "topics": []}
        score = calculate_relevance([], paper, None)
        assert score == 0.0


class TestExtractExcerpt:
    """Tests for extract_excerpt function."""

    def test_basic_excerpt(self) -> None:
        """Test basic excerpt extraction."""
        text = "This is a paper about attention mechanisms and their applications."
        result = extract_excerpt(["attention"], text)
        assert "attention" in result.lower()

    def test_excerpt_with_ellipsis(self) -> None:
        """Test that long text gets ellipsis."""
        text = "A" * 100 + " attention " + "B" * 100
        result = extract_excerpt(["attention"], text)
        assert "..." in result

    def test_no_match_returns_start(self) -> None:
        """Test that no match returns start of text."""
        text = "This is a paper about transformers."
        result = extract_excerpt(["attention"], text, max_length=20)
        assert result.startswith("This")

    def test_empty_text(self) -> None:
        """Test empty text returns empty string."""
        result = extract_excerpt(["attention"], "")
        assert result == ""

    def test_empty_query_terms(self) -> None:
        """Test empty query terms returns empty string."""
        result = extract_excerpt([], "some text")
        assert result == ""


class TestSearchPapers:
    """Tests for search_papers function."""

    @pytest.fixture
    def populated_index(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> Path:
        """Create a populated paper index for search tests."""
        index = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "papers": {
                paper["id"]: {
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "abstract": paper["abstract"],
                    "topics": ["test topic"],
                    "collected_at": datetime.now().isoformat(),
                    "has_summary": False,
                }
                for paper in sample_papers
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index, f)
        return temp_data_dir

    def test_search_returns_results(self, populated_index: Path) -> None:
        """Test that search returns matching results."""
        results, total = search_papers("LLM Agents", populated_index, limit=10)

        assert total == 3  # 3 sample papers
        assert len(results) >= 1

    def test_search_ranks_by_relevance(self, populated_index: Path) -> None:
        """Test that results are ranked by relevance."""
        results, _ = search_papers("LLM Agents", populated_index, limit=10)

        # Results should be sorted by score descending
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_respects_limit(self, populated_index: Path) -> None:
        """Test that search respects the limit parameter."""
        results, _ = search_papers("paper", populated_index, limit=1)

        assert len(results) <= 1

    def test_search_empty_query_raises_error(self, populated_index: Path) -> None:
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search_papers("", populated_index)

    def test_search_missing_index_raises_error(self, temp_data_dir: Path) -> None:
        """Test that missing index raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            search_papers("test", temp_data_dir)

    def test_search_no_matches(self, populated_index: Path) -> None:
        """Test search with no matching results."""
        results, total = search_papers("xyznonexistent", populated_index)

        assert len(results) == 0
        assert total == 3  # Total papers still counted


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_missing_query_exits(self) -> None:
        """Test that missing query argument causes exit."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["search_index.py"]):
                main()

    def test_successful_search(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]]
    ) -> None:
        """Test full CLI workflow with valid arguments."""
        # Create index
        index = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "papers": {
                paper["id"]: {
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "abstract": paper["abstract"],
                    "topics": ["test topic"],
                    "collected_at": datetime.now().isoformat(),
                    "has_summary": False,
                }
                for paper in sample_papers
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index, f)

        with patch(
            "sys.argv",
            [
                "search_index.py",
                "--query",
                "LLM Agents",
                "--data-dir",
                str(temp_data_dir),
                "--limit",
                "5",
            ],
        ):
            exit_code = main()

        assert exit_code == 0

    def test_missing_index_returns_error(self, temp_data_dir: Path) -> None:
        """Test that missing index returns error exit code."""
        with patch(
            "sys.argv",
            [
                "search_index.py",
                "--query",
                "test",
                "--data-dir",
                str(temp_data_dir),
            ],
        ):
            exit_code = main()

        assert exit_code == 1

    def test_custom_limit(
        self, temp_data_dir: Path, sample_papers: list[dict[str, Any]], capsys: Any
    ) -> None:
        """Test that custom limit is respected."""
        # Create index with multiple papers
        index = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "papers": {
                paper["id"]: {
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "abstract": paper["abstract"],
                    "topics": ["test topic"],
                    "collected_at": datetime.now().isoformat(),
                    "has_summary": False,
                }
                for paper in sample_papers
            },
        }
        index_path = temp_data_dir / "index" / "papers.json"
        with index_path.open("w") as f:
            json.dump(index, f)

        with patch(
            "sys.argv",
            [
                "search_index.py",
                "--query",
                "Test Paper",
                "--data-dir",
                str(temp_data_dir),
                "--limit",
                "1",
            ],
        ):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output["results"]) <= 1
