"""Pytest configuration and fixtures for paper-researcher tests."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_paper() -> dict[str, Any]:
    """Sample paper metadata for testing."""
    return {
        "id": "2401.12345",
        "title": "Test Paper: A Study on LLM Agents",
        "authors": ["John Smith", "Jane Doe"],
        "abstract": (
            "This paper presents a comprehensive study on LLM agents "
            "and their applications in various domains."
        ),
        "published": "2024-01-15",
        "updated": "2024-01-20",
        "categories": ["cs.CL", "cs.AI"],
        "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
    }


@pytest.fixture
def sample_papers() -> list[dict[str, Any]]:
    """List of sample papers for testing."""
    return [
        {
            "id": "2401.12345",
            "title": "Test Paper 1: LLM Agents",
            "authors": ["John Smith"],
            "abstract": "Abstract for paper 1",
            "published": "2024-01-15",
            "categories": ["cs.CL"],
            "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
        },
        {
            "id": "2401.12346",
            "title": "Test Paper 2: Transformer Models",
            "authors": ["Jane Doe", "Bob Wilson"],
            "abstract": "Abstract for paper 2",
            "published": "2024-01-16",
            "categories": ["cs.AI"],
            "pdf_url": "https://arxiv.org/pdf/2401.12346.pdf",
        },
        {
            "id": "2401.12347",
            "title": "Test Paper 3: Attention Mechanisms",
            "authors": ["Alice Brown"],
            "abstract": "Abstract for paper 3",
            "published": "2024-01-17",
            "categories": ["cs.LG"],
            "pdf_url": "https://arxiv.org/pdf/2401.12347.pdf",
        },
    ]


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        (data_dir / "papers").mkdir(parents=True)
        (data_dir / "index").mkdir(parents=True)
        yield data_dir


@pytest.fixture
def arxiv_response_xml() -> str:
    """Sample arXiv API response XML."""
    # Long lines in XML are expected for realistic test fixtures  # noqa: E501
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <link href="http://arxiv.org/api/query" rel="self" type="application/atom+xml"/>
  <title type="html">ArXiv Query: search_query=all:LLM agents</title>
  <id>http://arxiv.org/api/test</id>
  <updated>2024-01-20T00:00:00-05:00</updated>
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <updated>2024-01-20T00:00:00Z</updated>
    <published>2024-01-15T00:00:00Z</published>
    <title>Test Paper: A Study on LLM Agents</title>
    <summary>This paper presents a comprehensive study on LLM agents.</summary>
    <author>
      <name>John Smith</name>
    </author>
    <author>
      <name>Jane Doe</name>
    </author>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate"/>
    <link title="pdf" href="http://arxiv.org/pdf/2401.12345v1" rel="related"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2401.12346v1</id>
    <updated>2024-01-21T00:00:00Z</updated>
    <published>2024-01-16T00:00:00Z</published>
    <title>Multi-Agent Systems in NLP</title>
    <summary>A study on multi-agent systems in NLP.</summary>
    <author>
      <name>Bob Wilson</name>
    </author>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <link href="http://arxiv.org/abs/2401.12346v1" rel="alternate"/>
    <link title="pdf" href="http://arxiv.org/pdf/2401.12346v1" rel="related"/>
  </entry>
</feed>"""


@pytest.fixture
def fetch_output_json(sample_papers: list[dict[str, Any]]) -> dict[str, Any]:
    """Sample output from fetch_arxiv.py."""
    return {
        "success": True,
        "count": len(sample_papers),
        "query": "LLM agents",
        "days": 7,
        "papers": sample_papers,
    }


@pytest.fixture
def temp_fetch_output(temp_data_dir: Path, fetch_output_json: dict[str, Any]) -> Path:
    """Create a temporary fetch output file."""
    output_path = temp_data_dir / "papers.json"
    with output_path.open("w") as f:
        json.dump(fetch_output_json, f)
    return output_path
