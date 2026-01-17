"""Tests for the RIS exporter."""

import json
from pathlib import Path

import pytest

from academic_research_toolkit.exporters.ris import RISExporter


@pytest.fixture
def exporter():
    """Create a RISExporter instance."""
    return RISExporter()


@pytest.fixture
def sample_book_citation():
    """Sample book citation."""
    return {
        "citation_type": "book",
        "authors": ["Smith, John", "Doe, Jane"],
        "title": "Introduction to Artificial Intelligence",
        "year": "2020",
        "publisher": "Academic Press",
        "location": "New York",
    }


@pytest.fixture
def sample_article_citation():
    """Sample journal article citation."""
    return {
        "citation_type": "article",
        "authors": ["Johnson, Robert"],
        "title": "Machine Learning Applications in Healthcare",
        "year": "2021",
        "source": "Journal of AI Research",
        "volume": "15",
        "issue": "3",
        "pages": "100-120",
        "doi": "10.1234/jair.2021.001",
    }


@pytest.fixture
def sample_citations(sample_book_citation, sample_article_citation):
    """List of sample citations."""
    return [sample_book_citation, sample_article_citation]


class TestRISExporter:
    """Tests for RISExporter class."""

    def test_export_book_citation(self, exporter, sample_book_citation):
        """Test exporting a single book citation."""
        result = exporter.export([sample_book_citation])

        assert "TY  - BOOK" in result
        assert "AU  - Smith, John" in result
        assert "AU  - Doe, Jane" in result
        assert "TI  - Introduction to Artificial Intelligence" in result
        assert "PY  - 2020" in result
        assert "PB  - Academic Press" in result
        assert "CY  - New York" in result
        assert "ER  - " in result

    def test_export_article_citation(self, exporter, sample_article_citation):
        """Test exporting a journal article citation."""
        result = exporter.export([sample_article_citation])

        assert "TY  - JOUR" in result
        assert "AU  - Johnson, Robert" in result
        assert "TI  - Machine Learning Applications in Healthcare" in result
        assert "PY  - 2021" in result
        assert "JO  - Journal of AI Research" in result
        assert "VL  - 15" in result
        assert "IS  - 3" in result
        assert "SP  - 100" in result
        assert "EP  - 120" in result
        assert "DO  - 10.1234/jair.2021.001" in result
        assert "ER  - " in result

    def test_export_multiple_citations(self, exporter, sample_citations):
        """Test exporting multiple citations."""
        result = exporter.export(sample_citations)

        assert "TY  - BOOK" in result
        assert "TY  - JOUR" in result
        # Both entries should have end markers
        assert result.count("ER  - ") == 2

    def test_type_mapping(self, exporter):
        """Test that citation types map correctly to RIS types."""
        types_to_test = [
            ("book", "BOOK"),
            ("article", "JOUR"),
            ("journal", "JOUR"),
            ("interview", "PCOMM"),
            ("online", "ELEC"),
            ("archival", "UNPB"),
            ("unclassified", "GEN"),
            ("unknown", "GEN"),  # Unknown types should default to GEN
        ]

        for citation_type, expected_ris in types_to_test:
            citation = {
                "citation_type": citation_type,
                "title": "Test",
                "year": "2020",
            }
            result = exporter.export([citation])
            assert f"TY  - {expected_ris}" in result

    def test_author_formatting_last_first(self, exporter):
        """Test that authors already in Last, First format are preserved."""
        citation = {
            "authors": ["Smith, John Q."],
            "title": "Test",
            "year": "2020",
        }
        result = exporter.export([citation])
        assert "AU  - Smith, John Q." in result

    def test_author_formatting_first_last(self, exporter):
        """Test that First Last format is converted to Last, First."""
        citation = {
            "authors": ["John Smith"],
            "title": "Test",
            "year": "2020",
        }
        result = exporter.export([citation])
        assert "AU  - Smith, John" in result

    def test_multiple_authors(self, exporter):
        """Test that multiple authors each get their own AU line."""
        citation = {
            "authors": ["Smith, John", "Doe, Jane", "Brown, Robert"],
            "title": "Test",
            "year": "2020",
        }
        result = exporter.export([citation])

        assert result.count("AU  - ") == 3
        assert "AU  - Smith, John" in result
        assert "AU  - Doe, Jane" in result
        assert "AU  - Brown, Robert" in result

    def test_page_range_parsing(self, exporter):
        """Test that page ranges are parsed into start and end pages."""
        citation = {
            "title": "Test",
            "year": "2020",
            "pages": "50-75",
        }
        result = exporter.export([citation])

        assert "SP  - 50" in result
        assert "EP  - 75" in result

    def test_page_range_en_dash(self, exporter):
        """Test page ranges with en-dash."""
        citation = {
            "title": "Test",
            "year": "2020",
            "pages": "50–75",  # En-dash
        }
        result = exporter.export([citation])

        assert "SP  - 50" in result
        assert "EP  - 75" in result

    def test_single_page(self, exporter):
        """Test single page number."""
        citation = {
            "title": "Test",
            "year": "2020",
            "pages": "42",
        }
        result = exporter.export([citation])

        assert "SP  - 42" in result
        assert "EP  - " not in result

    def test_url_field(self, exporter):
        """Test URL field inclusion."""
        citation = {
            "title": "Online Resource",
            "year": "2020",
            "url": "https://example.com/paper",
        }
        result = exporter.export([citation])
        assert "UR  - https://example.com/paper" in result

    def test_notes_field(self, exporter):
        """Test notes field inclusion."""
        citation = {
            "title": "Test",
            "year": "2020",
            "notes": "This is a special note",
        }
        result = exporter.export([citation])
        assert "N1  - This is a special note" in result

    def test_raw_text_as_note(self, exporter):
        """Test that raw_text is used as note when no notes field."""
        citation = {
            "title": "Test",
            "year": "2020",
            "raw_text": "Original citation text",
        }
        result = exporter.export([citation])
        assert "N1  - Original citation text" in result

    def test_save_to_file(self, exporter, sample_citations, tmp_path):
        """Test saving citations to a .ris file."""
        output_path = tmp_path / "test.ris"
        result = exporter.save(sample_citations, output_path)

        assert Path(result).exists()
        content = Path(result).read_text()
        assert "TY  - BOOK" in content
        assert "TY  - JOUR" in content

    def test_load_citations_from_list(self, exporter, tmp_path):
        """Test loading citations from JSON file with list format."""
        citations = [
            {"authors": ["Smith"], "title": "Test", "year": "2020"},
        ]
        json_path = tmp_path / "citations.json"
        json_path.write_text(json.dumps(citations))

        loaded = exporter.load_citations(json_path)
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Test"

    def test_load_citations_from_dict(self, exporter, tmp_path):
        """Test loading citations from JSON file with dict format."""
        data = {
            "citations": [
                {"authors": ["Smith"], "title": "Test", "year": "2020"},
            ]
        }
        json_path = tmp_path / "citations.json"
        json_path.write_text(json.dumps(data))

        loaded = exporter.load_citations(json_path)
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Test"

    def test_empty_citations(self, exporter):
        """Test exporting empty citation list."""
        result = exporter.export([])
        assert result == ""

    def test_minimal_citation(self, exporter):
        """Test exporting a citation with minimal fields."""
        citation = {"title": "Just a Title"}
        result = exporter.export([citation])

        assert "TY  - GEN" in result
        assert "TI  - Just a Title" in result
        assert "ER  - " in result

    def test_title_with_quotes(self, exporter):
        """Test that quotes are stripped from titles."""
        citation = {
            "title": '"Quoted Title"',
            "year": "2020",
        }
        result = exporter.export([citation])
        assert 'TI  - Quoted Title' in result

    def test_entry_format(self, exporter):
        """Test that entries follow RIS format specification."""
        citation = {
            "citation_type": "book",
            "authors": ["Smith, John"],
            "title": "Test Book",
            "year": "2020",
            "publisher": "Publisher",
        }
        result = exporter.export([citation])

        # Check format: "XX  - VALUE" (ER line may have trailing space or be empty after -)
        lines = result.strip().split("\n")
        for line in lines:
            # RIS format: two-letter tag, two spaces, hyphen, space, value
            # ER line is special - it has no value
            if line.startswith("ER"):
                assert line.startswith("ER  -"), f"ER line doesn't match format: {line}"
            else:
                assert "  - " in line, f"Line doesn't match RIS format: {line}"

        # TY must be first, ER must be last
        assert lines[0].startswith("TY  - ")
        assert lines[-1].startswith("ER  -")


class TestRISExporterHelpers:
    """Tests for RISExporter helper methods."""

    def test_format_author_comma_format(self, exporter):
        """Test formatting author already in Last, First format."""
        assert exporter._format_author("Smith, John") == "Smith, John"

    def test_format_author_space_format(self, exporter):
        """Test converting First Last to Last, First."""
        assert exporter._format_author("John Smith") == "Smith, John"

    def test_format_author_middle_name(self, exporter):
        """Test converting First Middle Last to Last, First Middle."""
        assert exporter._format_author("John Q. Smith") == "Smith, John Q."

    def test_format_author_single_name(self, exporter):
        """Test single name handling."""
        assert exporter._format_author("Aristotle") == "Aristotle"

    def test_format_author_empty(self, exporter):
        """Test empty author handling."""
        assert exporter._format_author("") == "Unknown"

    def test_parse_pages_range(self, exporter):
        """Test parsing page range."""
        assert exporter._parse_pages("100-120") == ("100", "120")

    def test_parse_pages_en_dash(self, exporter):
        """Test parsing page range with en-dash."""
        assert exporter._parse_pages("100–120") == ("100", "120")

    def test_parse_pages_em_dash(self, exporter):
        """Test parsing page range with em-dash."""
        assert exporter._parse_pages("100—120") == ("100", "120")

    def test_parse_pages_single(self, exporter):
        """Test parsing single page."""
        assert exporter._parse_pages("42") == ("42", None)
