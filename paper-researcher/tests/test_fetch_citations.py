"""Unit tests for fetch_citations.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import responses

# Add scripts directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "paper-citation" / "scripts")
)

from fetch_citations import (
    S2_BASE_URL,
    extract_arxiv_ids,
    filter_in_collection,
    load_index,
    main,
    update_metadata,
    validate_arxiv_id,
)


class TestValidateArxivId:
    """Tests for validate_arxiv_id function."""

    def test_valid_4_digit_id(self) -> None:
        """Test valid 4-digit suffix ID."""
        assert validate_arxiv_id("2401.1234") is True

    def test_valid_5_digit_id(self) -> None:
        """Test valid 5-digit suffix ID."""
        assert validate_arxiv_id("2401.12345") is True

    def test_invalid_empty(self) -> None:
        """Test empty string is invalid."""
        assert validate_arxiv_id("") is False

    def test_invalid_format(self) -> None:
        """Test invalid format is rejected."""
        assert validate_arxiv_id("not-an-id") is False
        assert validate_arxiv_id("2401") is False
        assert validate_arxiv_id("2401.123") is False  # Too short
        assert validate_arxiv_id("2401.123456") is False  # Too long

    def test_invalid_with_version(self) -> None:
        """Test ID with version suffix is invalid."""
        assert validate_arxiv_id("2401.12345v1") is False


class TestExtractArxivIds:
    """Tests for extract_arxiv_ids function."""

    def test_extract_from_references(self) -> None:
        """Test extracting arXiv IDs from references list."""
        papers = [
            {"paperId": "abc", "externalIds": {"ArXiv": "2301.5432"}},
            {"paperId": "def", "externalIds": {"ArXiv": "2312.9876"}},
        ]
        ids = extract_arxiv_ids(papers)
        assert ids == ["2301.5432", "2312.9876"]

    def test_skip_non_arxiv_papers(self) -> None:
        """Test that papers without arXiv IDs are skipped."""
        papers = [
            {"paperId": "abc", "externalIds": {"ArXiv": "2301.5432"}},
            {"paperId": "def", "externalIds": {"DOI": "10.1234/example"}},
            {"paperId": "ghi", "externalIds": {}},
        ]
        ids = extract_arxiv_ids(papers)
        assert ids == ["2301.5432"]

    def test_empty_list(self) -> None:
        """Test empty input returns empty list."""
        assert extract_arxiv_ids([]) == []
        assert extract_arxiv_ids(None) == []

    def test_skip_invalid_ids(self) -> None:
        """Test that invalid arXiv IDs are skipped."""
        papers = [
            {"paperId": "abc", "externalIds": {"ArXiv": "2301.5432"}},
            {"paperId": "def", "externalIds": {"ArXiv": "invalid"}},
        ]
        ids = extract_arxiv_ids(papers)
        assert ids == ["2301.5432"]


class TestFilterInCollection:
    """Tests for filter_in_collection function."""

    def test_filter_to_collection(self) -> None:
        """Test filtering to papers in collection."""
        index: dict[str, Any] = {"papers": {"2301.5432": {}, "2312.9876": {}}}
        arxiv_ids = ["2301.5432", "2312.9876", "2401.1234"]
        filtered = filter_in_collection(arxiv_ids, index)
        assert filtered == ["2301.5432", "2312.9876"]

    def test_empty_collection(self) -> None:
        """Test with empty collection."""
        index: dict[str, Any] = {"papers": {}}
        arxiv_ids = ["2301.5432"]
        filtered = filter_in_collection(arxiv_ids, index)
        assert filtered == []

    def test_no_matches(self) -> None:
        """Test when no IDs match collection."""
        index: dict[str, Any] = {"papers": {"2301.5432": {}}}
        arxiv_ids = ["2401.1234", "2402.1111"]
        filtered = filter_in_collection(arxiv_ids, index)
        assert filtered == []


class TestLoadIndex:
    """Tests for load_index function."""

    def test_load_existing_index(self, temp_data_dir: Path) -> None:
        """Test loading existing index."""
        index_data = {"papers": {"2401.12345": {"title": "Test"}}}
        index_path = temp_data_dir / "index" / "papers.json"
        index_path.write_text(json.dumps(index_data))

        result = load_index(temp_data_dir)
        assert result == index_data

    def test_missing_index(self, temp_data_dir: Path) -> None:
        """Test handling missing index file."""
        result = load_index(temp_data_dir)
        assert result == {"papers": {}}

    def test_invalid_json(self, temp_data_dir: Path) -> None:
        """Test handling invalid JSON in index."""
        index_path = temp_data_dir / "index" / "papers.json"
        index_path.write_text("not valid json {{{")

        result = load_index(temp_data_dir)
        assert result == {"papers": {}}


class TestUpdateMetadata:
    """Tests for update_metadata function."""

    def test_update_with_citation_data(self, temp_data_dir: Path) -> None:
        """Test updating metadata with citation data."""
        # Create paper directory and metadata
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata = {"id": "2401.12345", "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))

        # Create index
        index: dict[str, Any] = {"papers": {"2401.12345": {}, "2301.5432": {}}}

        # Citation data from S2
        citation_data = {
            "citationCount": 42,
            "referenceCount": 25,
            "references": [{"paperId": "abc", "externalIds": {"ArXiv": "2301.5432"}}],
            "citations": [],
        }

        result = update_metadata("2401.12345", citation_data, temp_data_dir, index)
        assert result is True

        # Verify metadata was updated
        updated = json.loads((paper_dir / "metadata.json").read_text())
        assert "citation_data" in updated
        assert updated["citation_data"]["source"] == "semantic_scholar"
        assert updated["citation_data"]["citation_count"] == 42
        assert updated["citation_data"]["references_in_collection"] == ["2301.5432"]

    def test_update_with_unavailable_data(self, temp_data_dir: Path) -> None:
        """Test updating metadata when paper not in S2."""
        paper_dir = temp_data_dir / "papers" / "2401.12345"
        paper_dir.mkdir(parents=True)
        metadata = {"id": "2401.12345", "title": "Test Paper"}
        (paper_dir / "metadata.json").write_text(json.dumps(metadata))

        index: dict[str, Any] = {"papers": {"2401.12345": {}}}

        result = update_metadata("2401.12345", None, temp_data_dir, index)
        assert result is True

        updated = json.loads((paper_dir / "metadata.json").read_text())
        assert updated["citation_data"]["source"] == "unavailable"

    def test_invalid_paper_id(self, temp_data_dir: Path) -> None:
        """Test with invalid paper ID."""
        index: dict[str, Any] = {"papers": {}}
        result = update_metadata("invalid", {}, temp_data_dir, index)
        assert result is False

    def test_missing_metadata(self, temp_data_dir: Path) -> None:
        """Test with missing metadata file."""
        index: dict[str, Any] = {"papers": {}}
        result = update_metadata("2401.12345", {}, temp_data_dir, index)
        assert result is False


class TestFetchWithRetry:
    """Tests for fetch_with_retry function."""

    @responses.activate
    def test_successful_fetch(self) -> None:
        """Test successful fetch from S2 API."""
        s2_response: dict[str, Any] = {
            "paperId": "abc",
            "citationCount": 10,
            "referenceCount": 5,
            "references": [],
            "citations": [],
        }
        responses.add(
            responses.GET,
            f"{S2_BASE_URL}/paper/arXiv:2401.12345",
            json=s2_response,
            status=200,
        )

        from fetch_citations import fetch_with_retry

        with patch("fetch_citations.time.sleep"):
            result = fetch_with_retry("2401.12345")

        assert result is not None
        assert result["citationCount"] == 10

    @responses.activate
    def test_not_found_returns_none(self) -> None:
        """Test 404 returns None."""
        responses.add(
            responses.GET,
            f"{S2_BASE_URL}/paper/arXiv:2401.99999",
            status=404,
        )

        from fetch_citations import fetch_with_retry

        with patch("fetch_citations.time.sleep"):
            result = fetch_with_retry("2401.99999")

        assert result is None

    @responses.activate
    def test_rate_limited_retries(self) -> None:
        """Test 429 rate limit handling."""
        responses.add(
            responses.GET,
            f"{S2_BASE_URL}/paper/arXiv:2401.12345",
            status=429,
        )
        responses.add(
            responses.GET,
            f"{S2_BASE_URL}/paper/arXiv:2401.12345",
            json={"paperId": "abc", "citationCount": 5},
            status=200,
        )

        from fetch_citations import fetch_with_retry

        with patch("fetch_citations.time.sleep"):
            result = fetch_with_retry("2401.12345")

        assert result is not None
        assert len(responses.calls) == 2


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_requires_paper_id_or_all(self) -> None:
        """Test that either --paper-id or --all is required."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["fetch_citations.py", "--data-dir", "/tmp"]):
                main()

    def test_mutually_exclusive(self) -> None:
        """Test --paper-id and --all are mutually exclusive."""
        with pytest.raises(SystemExit):
            with patch(
                "sys.argv",
                [
                    "fetch_citations.py",
                    "--paper-id",
                    "2401.12345",
                    "--all",
                    "--data-dir",
                    "/tmp",
                ],
            ):
                main()

    def test_requires_data_dir(self) -> None:
        """Test --data-dir is required."""
        with pytest.raises(SystemExit):
            with patch(
                "sys.argv", ["fetch_citations.py", "--paper-id", "2401.12345"]
            ):
                main()
