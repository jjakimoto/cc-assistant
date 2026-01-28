"""Unit tests for fetch_arxiv.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import responses

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "paper-collector" / "scripts"))

from fetch_arxiv import (
    ARXIV_BASE_URL,
    build_query,
    main,
    parse_response,
)


class TestBuildQuery:
    """Tests for build_query function."""

    def test_basic_query(self) -> None:
        """Test basic query construction."""
        query = build_query("LLM agents", 7)
        assert "all:LLM agents" in query
        assert "submittedDate:" in query

    def test_query_with_special_characters(self) -> None:
        """Test query with special characters are sanitized."""
        query = build_query("LLM; DROP TABLE papers;", 7)
        # Special characters should be removed
        assert ";" not in query
        assert "DROP TABLE" in query  # Text preserved, special chars removed

    def test_date_range_in_query(self) -> None:
        """Test that date range is included in query."""
        query = build_query("test", 30)
        # Should have date filter
        assert "submittedDate:[" in query
        assert " TO " in query
        assert "]" in query

    def test_different_days(self) -> None:
        """Test query with different day ranges."""
        query_7 = build_query("test", 7)
        query_30 = build_query("test", 30)
        # Both should have date filters
        assert "submittedDate:" in query_7
        assert "submittedDate:" in query_30


class TestParseResponse:
    """Tests for parse_response function."""

    def test_parse_valid_response(self, arxiv_response_xml: str) -> None:
        """Test parsing valid arXiv XML response."""
        papers = parse_response(arxiv_response_xml)

        assert len(papers) == 2

        # Check first paper
        paper1 = papers[0]
        assert paper1["id"] == "2401.12345"
        assert paper1["title"] == "Test Paper: A Study on LLM Agents"
        assert "John Smith" in paper1["authors"]
        assert "Jane Doe" in paper1["authors"]
        assert "cs.CL" in paper1["categories"]
        assert paper1["published"] == "2024-01-15"

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response."""
        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title type="html">ArXiv Query</title>
        </feed>"""

        papers = parse_response(empty_xml)
        assert papers == []

    def test_parse_malformed_entry(self) -> None:
        """Test that malformed entries are skipped."""
        xml_with_bad_entry = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <id>invalid-id-without-arxiv-format</id>
                <title>Bad Entry</title>
            </entry>
            <entry>
                <id>http://arxiv.org/abs/2401.99999v1</id>
                <title>Good Entry</title>
                <summary>Abstract</summary>
                <published>2024-01-20T00:00:00Z</published>
            </entry>
        </feed>"""

        papers = parse_response(xml_with_bad_entry)
        # Should skip the bad entry and parse the good one
        assert len(papers) == 1
        assert papers[0]["id"] == "2401.99999"

    def test_pdf_url_construction(self, arxiv_response_xml: str) -> None:
        """Test that PDF URL is correctly constructed."""
        papers = parse_response(arxiv_response_xml)
        for paper in papers:
            assert paper["pdf_url"].startswith("https://arxiv.org/pdf/")
            assert paper["id"] in paper["pdf_url"]


class TestRetryLogic:
    """Tests for retry logic in fetch_with_retry."""

    @responses.activate
    def test_successful_request(self, arxiv_response_xml: str) -> None:
        """Test successful request without retries."""
        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=arxiv_response_xml,
            status=200,
        )

        from fetch_arxiv import fetch_with_retry

        result = fetch_with_retry("test query", 10)
        assert result == arxiv_response_xml
        assert len(responses.calls) == 1

    @responses.activate
    def test_retry_on_503(self, arxiv_response_xml: str) -> None:
        """Test retry on 503 error."""
        # First two calls fail, third succeeds
        responses.add(responses.GET, ARXIV_BASE_URL, status=503)
        responses.add(responses.GET, ARXIV_BASE_URL, status=503)
        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=arxiv_response_xml,
            status=200,
        )

        from fetch_arxiv import fetch_with_retry

        with patch("fetch_arxiv.time.sleep"):  # Skip actual sleep
            result = fetch_with_retry("test query", 10)

        assert result == arxiv_response_xml
        assert len(responses.calls) == 3

    @responses.activate
    def test_all_retries_fail(self) -> None:
        """Test that exception is raised when all retries fail."""
        responses.add(responses.GET, ARXIV_BASE_URL, status=503)
        responses.add(responses.GET, ARXIV_BASE_URL, status=503)
        responses.add(responses.GET, ARXIV_BASE_URL, status=503)

        import requests
        from fetch_arxiv import fetch_with_retry

        with patch("fetch_arxiv.time.sleep"):
            with pytest.raises(requests.RequestException):
                fetch_with_retry("test query", 10)


class TestErrorHandling:
    """Tests for error handling."""

    @responses.activate
    def test_network_timeout(self) -> None:
        """Test handling of network timeout."""
        import requests

        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=requests.exceptions.Timeout("Connection timed out"),
        )
        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=requests.exceptions.Timeout("Connection timed out"),
        )
        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=requests.exceptions.Timeout("Connection timed out"),
        )

        from fetch_arxiv import fetch_with_retry

        with patch("fetch_arxiv.time.sleep"):
            with pytest.raises(requests.exceptions.Timeout):
                fetch_with_retry("test query", 10)

    def test_invalid_xml_response(self) -> None:
        """Test handling of invalid XML response."""
        invalid_xml = "not valid xml at all <<<"
        papers = parse_response(invalid_xml)
        # Should return empty list, not crash
        assert papers == []


class TestCliArguments:
    """Tests for CLI argument parsing."""

    def test_required_query_argument(self) -> None:
        """Test that --query is required."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["fetch_arxiv.py"]):
                main()

    @responses.activate
    def test_all_arguments(self, arxiv_response_xml: str, tmp_path: Path) -> None:
        """Test all CLI arguments work correctly."""
        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=arxiv_response_xml,
            status=200,
        )

        output_file = tmp_path / "output.json"

        with patch("fetch_arxiv.time.sleep"):
            with patch(
                "sys.argv",
                [
                    "fetch_arxiv.py",
                    "--query",
                    "LLM agents",
                    "--days",
                    "14",
                    "--max",
                    "25",
                    "--output",
                    str(output_file),
                ],
            ):
                exit_code = main()

        assert exit_code == 0
        assert output_file.exists()

        import json

        with output_file.open() as f:
            data = json.load(f)

        assert data["success"] is True
        assert data["query"] == "LLM agents"
        assert data["days"] == 14

    @responses.activate
    def test_default_arguments(self, arxiv_response_xml: str) -> None:
        """Test default values for optional arguments."""
        responses.add(
            responses.GET,
            ARXIV_BASE_URL,
            body=arxiv_response_xml,
            status=200,
        )

        with patch("fetch_arxiv.time.sleep"):
            with patch(
                "sys.argv",
                ["fetch_arxiv.py", "--query", "test"],
            ):
                exit_code = main()

        assert exit_code == 0
        # Verify the call was made with expected default parameters
        assert len(responses.calls) == 1
        call = responses.calls[0]
        assert call.request.url is not None
        assert "max_results=50" in call.request.url
        assert "start=0" in call.request.url
