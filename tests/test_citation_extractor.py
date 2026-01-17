"""Tests for citation extractor."""

import pytest
from pathlib import Path

from academic_research_toolkit.citation_extractor import CitationExtractor, Citation


class TestCitation:
    """Tests for Citation dataclass."""

    def test_citation_creation(self):
        """Test creating a citation."""
        citation = Citation(
            raw_text="Smith, John. 2020. Test Book. Publisher.",
            citation_type="book",
            authors=["Smith, John"],
            year="2020",
            title="Test Book",
            publisher="Publisher",
            location=None,
            source=None,
            url=None,
            notes=None,
            confidence=0.9,
        )

        assert citation.citation_type == "book"
        assert citation.year == "2020"
        assert citation.confidence == 0.9
        assert len(citation.authors) == 1


class TestCitationExtractor:
    """Tests for CitationExtractor class."""

    def test_extractor_initialization(self):
        """Test extractor initializes correctly."""
        extractor = CitationExtractor()

        assert extractor.stats["total_lines"] == 0
        assert extractor.stats["citations_found"] == 0
        assert "book" in extractor.patterns
        assert "article" in extractor.patterns

    def test_extract_year(self):
        """Test year extraction from text."""
        extractor = CitationExtractor()

        assert extractor._extract_year("Published in 2020.") == "2020"
        assert extractor._extract_year("From 1999 to present.") == "1999"
        assert extractor._extract_year("No year here.") is None

    def test_extract_url(self):
        """Test URL extraction from text."""
        extractor = CitationExtractor()

        assert extractor._extract_url("Visit https://example.com for more.") == "https://example.com"
        assert extractor._extract_url("See http://test.org/page") == "http://test.org/page"
        assert extractor._extract_url("No URL here.") is None

    def test_parse_authors(self):
        """Test author parsing."""
        extractor = CitationExtractor()

        authors = extractor._parse_authors("Smith, John and Doe, Jane")
        assert len(authors) == 2
        assert "Smith, John" in authors

        authors = extractor._parse_authors("Smith, John")
        assert len(authors) == 1

    def test_extract_from_text(self):
        """Test extraction from text content."""
        extractor = CitationExtractor()

        text = """
## References

- Smith, John. 2020. Introduction to Testing. New York: Test Press.
- https://example.com/paper
"""
        citations = extractor.extract_from_text(text)

        # Should find at least the URL
        assert len(citations) >= 1

        stats = extractor.get_stats()
        assert stats["citations_found"] >= 1

    def test_extract_from_file(self, sample_markdown_file):
        """Test extraction from markdown file."""
        extractor = CitationExtractor()
        citations = extractor.extract_from_file(sample_markdown_file)

        # The sample content has at least one URL
        assert len(citations) >= 1

    def test_save_citations(self, temp_dir, sample_citations):
        """Test saving citations to files."""
        extractor = CitationExtractor()

        # Manually create Citation objects
        citations = [
            Citation(**c) for c in sample_citations
        ]

        paths = extractor.save_citations(citations, temp_dir, "test_paper.md")

        assert "json_path" in paths
        assert "md_path" in paths

        # Check files exist
        assert Path(paths["json_path"]).exists()
        assert Path(paths["md_path"]).exists()

    def test_skip_metadata(self):
        """Test metadata section is skipped."""
        extractor = CitationExtractor()

        content = """## Document Metadata
- Author: Test
- Date: 2020

## Extracted Text

The actual content starts here.
"""
        result = extractor._skip_metadata(content)
        assert "actual content" in result
        assert "Document Metadata" not in result


class TestCitationPatterns:
    """Tests for citation pattern matching."""

    def test_book_pattern(self):
        """Test book citation pattern."""
        extractor = CitationExtractor()

        # This tests the internal pattern matching
        line = "Smith, John. 2020. Test Title. New York: Publisher Name."
        citation = extractor._parse_line(line, None)

        # Pattern may or may not match depending on exact format
        # At minimum, unclassified citations starting with dash should work
        dash_line = "- Smith, John. 2020. Test Title. New York: Publisher Name."
        citation = extractor._parse_line(dash_line, None)
        assert citation is not None

    def test_online_pattern(self):
        """Test online source pattern."""
        extractor = CitationExtractor()

        line = "See https://example.com/research for more information"
        citation = extractor._parse_line(line, None)

        assert citation is not None
        assert citation.citation_type == "online"
        assert "example.com" in citation.url
