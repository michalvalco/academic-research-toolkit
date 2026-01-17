"""Tests for bibliography generator."""

import pytest
import json
from pathlib import Path

from academic_research_toolkit.bibliography_generator import BibliographyGenerator
from academic_research_toolkit.utils.exceptions import InvalidInputError


class TestBibliographyGenerator:
    """Tests for BibliographyGenerator class."""

    def test_initialization_apa(self):
        """Test initialization with APA format."""
        generator = BibliographyGenerator("apa")
        assert generator.format_style == "apa"

    def test_initialization_mla(self):
        """Test initialization with MLA format."""
        generator = BibliographyGenerator("mla")
        assert generator.format_style == "mla"

    def test_initialization_chicago(self):
        """Test initialization with Chicago format."""
        generator = BibliographyGenerator("chicago")
        assert generator.format_style == "chicago"

    def test_initialization_case_insensitive(self):
        """Test format is case-insensitive."""
        generator = BibliographyGenerator("APA")
        assert generator.format_style == "apa"

    def test_initialization_invalid_format(self):
        """Test initialization with invalid format raises error."""
        with pytest.raises(InvalidInputError):
            BibliographyGenerator("harvard")

    def test_extract_last_name_comma_format(self):
        """Test last name extraction from 'Last, First' format."""
        generator = BibliographyGenerator()
        assert generator._extract_last_name("Smith, John") == "Smith"
        assert generator._extract_last_name("Doe, Jane Marie") == "Doe"

    def test_extract_last_name_space_format(self):
        """Test last name extraction from 'First Last' format."""
        generator = BibliographyGenerator()
        assert generator._extract_last_name("John Smith") == "Smith"
        assert generator._extract_last_name("Jane Marie Doe") == "Doe"

    def test_get_initials(self):
        """Test initials generation."""
        generator = BibliographyGenerator()
        assert generator._get_initials("John") == "J."
        assert generator._get_initials("John Michael") == "J. M."
        assert generator._get_initials("Anna Maria Theresa") == "A. M. T."

    def test_format_apa_single_author(self):
        """Test APA single author formatting."""
        generator = BibliographyGenerator("apa")

        # From "First Last" format
        result = generator._format_apa_single_author("John Smith")
        assert result == "Smith, J."

        # From "Last, First" format
        result = generator._format_apa_single_author("Smith, John")
        assert result == "Smith, J."

    def test_format_apa_authors_single(self):
        """Test APA formatting with single author."""
        generator = BibliographyGenerator("apa")
        result = generator._format_apa_authors(["John Smith"])
        assert result == "Smith, J."

    def test_format_apa_authors_two(self):
        """Test APA formatting with two authors."""
        generator = BibliographyGenerator("apa")
        result = generator._format_apa_authors(["John Smith", "Jane Doe"])
        assert "Smith, J." in result
        assert "Doe, J." in result
        assert "&" in result

    def test_format_apa_authors_multiple(self):
        """Test APA formatting with multiple authors."""
        generator = BibliographyGenerator("apa")
        authors = ["John Smith", "Jane Doe", "Bob Wilson"]
        result = generator._format_apa_authors(authors)
        assert "Smith, J." in result
        assert "&" in result

    def test_generate_bibliography(self, sample_citations):
        """Test bibliography generation."""
        generator = BibliographyGenerator("apa")
        bibliography = generator.generate_bibliography(sample_citations)

        assert len(bibliography) > 0
        # Should contain author names
        assert "Smith" in bibliography or "Johnson" in bibliography

    def test_sort_citations(self, sample_citations):
        """Test citation sorting."""
        generator = BibliographyGenerator()

        # Create citations with different authors
        citations = [
            {"authors": ["Zebra, Alice"], "title": "Last"},
            {"authors": ["Adams, Bob"], "title": "First"},
            {"authors": ["Miller, Carol"], "title": "Middle"},
        ]

        sorted_citations = generator._sort_citations(citations)

        # Should be alphabetically sorted by last name
        assert sorted_citations[0]["authors"][0] == "Adams, Bob"
        assert sorted_citations[2]["authors"][0] == "Zebra, Alice"

    def test_sort_citations_no_author(self):
        """Test sorting citations without authors."""
        generator = BibliographyGenerator()

        citations = [
            {"authors": [], "title": "Zebra Book"},
            {"authors": ["Adams, Bob"], "title": "First"},
            {"authors": [], "title": "Aardvark Study"},
        ]

        sorted_citations = generator._sort_citations(citations)

        # No-author citations sort by title
        # "Aardvark Study" (title) < "Adams, Bob" (author) < "Zebra Book" (title)
        assert sorted_citations[0]["title"] == "Aardvark Study"
        assert sorted_citations[1]["authors"] == ["Adams, Bob"]
        assert sorted_citations[2]["title"] == "Zebra Book"


class TestBibliographyFormats:
    """Tests for different bibliography formats."""

    @pytest.fixture
    def book_citation(self):
        """Sample book citation."""
        return {
            "citation_type": "book",
            "authors": ["John Smith"],
            "year": "2020",
            "title": "Introduction to Testing",
            "publisher": "Academic Press",
            "location": "New York",
            "source": None,
            "url": None,
            "notes": None,
            "raw_text": "",
        }

    @pytest.fixture
    def article_citation(self):
        """Sample article citation."""
        return {
            "citation_type": "article",
            "authors": ["Jane Doe"],
            "year": "2021",
            "title": "Testing Methods",
            "publisher": None,
            "location": None,
            "source": "Journal of Testing",
            "url": None,
            "notes": "Vol 15 (3): 45-67",
            "raw_text": "",
        }

    def test_apa_book_format(self, book_citation):
        """Test APA book formatting."""
        generator = BibliographyGenerator("apa")
        result = generator._format_apa(book_citation, "book")

        assert "Smith, J." in result
        assert "(2020)" in result
        assert "Introduction to Testing" in result
        assert "Academic Press" in result

    def test_apa_article_format(self, article_citation):
        """Test APA article formatting."""
        generator = BibliographyGenerator("apa")
        result = generator._format_apa(article_citation, "article")

        assert "Doe, J." in result
        assert "(2021)" in result
        assert "Testing Methods" in result
        assert "Journal of Testing" in result

    def test_mla_book_format(self, book_citation):
        """Test MLA book formatting."""
        generator = BibliographyGenerator("mla")
        result = generator._format_mla(book_citation, "book")

        assert "Smith, John" in result
        assert "Introduction to Testing" in result
        assert "2020" in result

    def test_chicago_book_format(self, book_citation):
        """Test Chicago book formatting."""
        generator = BibliographyGenerator("chicago")
        result = generator._format_chicago(book_citation, "book")

        assert "John Smith" in result
        assert "Introduction to Testing" in result
        assert "2020" in result


class TestBibliographyIO:
    """Tests for bibliography file I/O."""

    def test_generate_from_file(self, temp_dir, sample_citations):
        """Test generating from JSON file."""
        # Create JSON file
        json_path = temp_dir / "citations.json"
        with open(json_path, "w") as f:
            json.dump(sample_citations, f)

        generator = BibliographyGenerator("apa")
        bibliography = generator.generate_from_file(json_path)

        assert len(bibliography) > 0

    def test_save_bibliography(self, temp_dir):
        """Test saving bibliography to file."""
        generator = BibliographyGenerator("apa")
        bibliography = "Test bibliography content"

        output_path = temp_dir / "bibliography.md"
        result = generator.save_bibliography(bibliography, output_path)

        assert Path(result).exists()

        content = Path(result).read_text()
        assert "APA" in content
        assert "Test bibliography content" in content

    def test_empty_citations(self):
        """Test handling empty citations list."""
        generator = BibliographyGenerator()
        bibliography = generator.generate_bibliography([])

        assert bibliography == ""
