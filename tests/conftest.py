"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Sample Academic Paper

## Document Metadata

- **Filename:** sample_paper.pdf
- **Author:** John Doe
- **Pages:** 10

## Extracted Text

This is a sample academic paper about artificial intelligence and machine learning.

The field of artificial intelligence has grown significantly in recent years.
Machine learning algorithms are now used in many applications.

## References

- Smith, John. 2020. Introduction to AI. New York: Academic Press.
- Johnson, Mary and Brown, Robert. 2021. "Deep Learning Methods." Journal of AI 15(3): 45-67.
- https://example.com/research/ai-paper

## Author Information

Dr. Jane Smith
Department of Computer Science
University of Technology
email: jane.smith@university.edu
"""


@pytest.fixture
def sample_citations():
    """Sample citation data for testing."""
    return [
        {
            "raw_text": "- Smith, John. 2020. Introduction to AI. New York: Academic Press.",
            "citation_type": "book",
            "authors": ["Smith, John"],
            "year": "2020",
            "title": "Introduction to AI",
            "publisher": "Academic Press",
            "location": "New York",
            "source": None,
            "url": None,
            "notes": None,
            "confidence": 0.9,
        },
        {
            "raw_text": '- Johnson, Mary. 2021. "Deep Learning Methods." Journal of AI 15(3): 45-67.',
            "citation_type": "article",
            "authors": ["Johnson, Mary"],
            "year": "2021",
            "title": "Deep Learning Methods",
            "publisher": None,
            "location": None,
            "source": "Journal of AI",
            "url": None,
            "notes": "Vol 15 (3): 45-67",
            "confidence": 0.9,
        },
    ]


@pytest.fixture
def sample_markdown_file(temp_dir, sample_markdown_content):
    """Create a sample markdown file for testing."""
    md_path = temp_dir / "sample_paper.md"
    md_path.write_text(sample_markdown_content, encoding="utf-8")
    return md_path
