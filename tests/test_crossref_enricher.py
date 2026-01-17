"""Tests for the CrossRef enricher."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from academic_research_toolkit.enrichment.crossref import CrossRefEnricher


@pytest.fixture
def enricher():
    """Create a CrossRefEnricher instance."""
    return CrossRefEnricher()


@pytest.fixture
def enricher_with_email():
    """Create a CrossRefEnricher instance with email."""
    return CrossRefEnricher(email="test@example.com")


@pytest.fixture
def sample_crossref_response():
    """Sample CrossRef API response for a DOI lookup."""
    return {
        "message": {
            "DOI": "10.1234/test.2020.001",
            "title": ["Machine Learning in Practice"],
            "author": [
                {"given": "John", "family": "Smith"},
                {"given": "Jane", "family": "Doe"},
            ],
            "published-print": {"date-parts": [[2020, 5, 15]]},
            "publisher": "Academic Press",
            "container-title": ["Journal of AI"],
            "volume": "10",
            "issue": "2",
            "page": "100-120",
            "URL": "https://doi.org/10.1234/test.2020.001",
            "type": "journal-article",
            "ISSN": ["1234-5678"],
        }
    }


@pytest.fixture
def sample_citation():
    """Sample citation for enrichment."""
    return {
        "authors": ["Smith, John"],
        "title": "Machine Learning in Practice",
        "year": "2020",
        "doi": "10.1234/test.2020.001",
    }


@pytest.fixture
def sample_citation_no_doi():
    """Sample citation without DOI."""
    return {
        "authors": ["Smith, John"],
        "title": "Machine Learning in Practice",
        "year": "2020",
    }


class TestCrossRefEnricherInit:
    """Tests for CrossRefEnricher initialization."""

    def test_init_without_email(self, enricher):
        """Test initialization without email."""
        assert enricher.email is None
        assert "AcademicResearchToolkit" in enricher.user_agent
        assert "mailto:" not in enricher.user_agent

    def test_init_with_email(self, enricher_with_email):
        """Test initialization with email."""
        assert enricher_with_email.email == "test@example.com"
        assert "mailto:test@example.com" in enricher_with_email.user_agent


class TestCrossRefEnricherDOICleaning:
    """Tests for DOI cleaning functionality."""

    def test_clean_doi_basic(self, enricher):
        """Test cleaning a basic DOI."""
        assert enricher._clean_doi("10.1234/test") == "10.1234/test"

    def test_clean_doi_with_https_prefix(self, enricher):
        """Test cleaning DOI with https://doi.org/ prefix."""
        assert enricher._clean_doi("https://doi.org/10.1234/test") == "10.1234/test"

    def test_clean_doi_with_http_prefix(self, enricher):
        """Test cleaning DOI with http://doi.org/ prefix."""
        assert enricher._clean_doi("http://doi.org/10.1234/test") == "10.1234/test"

    def test_clean_doi_with_dx_prefix(self, enricher):
        """Test cleaning DOI with dx.doi.org prefix."""
        assert enricher._clean_doi("https://dx.doi.org/10.1234/test") == "10.1234/test"

    def test_clean_doi_with_doi_prefix(self, enricher):
        """Test cleaning DOI with doi: prefix."""
        assert enricher._clean_doi("doi:10.1234/test") == "10.1234/test"

    def test_clean_doi_empty(self, enricher):
        """Test cleaning empty DOI."""
        assert enricher._clean_doi("") is None
        assert enricher._clean_doi(None) is None

    def test_clean_doi_invalid(self, enricher):
        """Test cleaning invalid DOI."""
        assert enricher._clean_doi("not-a-doi") is None
        assert enricher._clean_doi("https://example.com") is None


class TestCrossRefEnricherParsing:
    """Tests for CrossRef response parsing."""

    def test_parse_work_complete(self, enricher, sample_crossref_response):
        """Test parsing a complete CrossRef work response."""
        result = enricher._parse_work(sample_crossref_response["message"])

        assert result["doi"] == "10.1234/test.2020.001"
        assert result["title"] == "Machine Learning in Practice"
        assert result["authors"] == ["Smith, John", "Doe, Jane"]
        assert result["year"] == "2020"
        assert result["publisher"] == "Academic Press"
        assert result["source"] == "Journal of AI"
        assert result["volume"] == "10"
        assert result["issue"] == "2"
        assert result["pages"] == "100-120"
        assert result["citation_type"] == "article"

    def test_parse_work_minimal(self, enricher):
        """Test parsing a minimal CrossRef response."""
        data = {"title": ["Test Title"]}
        result = enricher._parse_work(data)

        assert result["title"] == "Test Title"
        assert "authors" not in result
        assert "year" not in result

    def test_parse_work_author_family_only(self, enricher):
        """Test parsing author with family name only."""
        data = {"author": [{"family": "Smith"}]}
        result = enricher._parse_work(data)

        assert result["authors"] == ["Smith"]

    def test_parse_work_multiple_date_fields(self, enricher):
        """Test that year is extracted from available date fields."""
        # Should prefer published-print
        data = {
            "published-print": {"date-parts": [[2020]]},
            "created": {"date-parts": [[2019]]},
        }
        result = enricher._parse_work(data)
        assert result["year"] == "2020"

    def test_parse_work_type_mapping(self, enricher):
        """Test citation type mapping."""
        types_to_test = [
            ("journal-article", "article"),
            ("book", "book"),
            ("book-chapter", "book"),
            ("proceedings-article", "article"),
            ("posted-content", "online"),
            ("unknown-type", "unclassified"),
        ]

        for crossref_type, expected_type in types_to_test:
            data = {"type": crossref_type}
            result = enricher._parse_work(data)
            assert result.get("citation_type") == expected_type


class TestCrossRefEnricherMerging:
    """Tests for metadata merging."""

    def test_merge_metadata_fills_missing(self, enricher):
        """Test that merge fills in missing fields."""
        original = {"title": "Original Title", "year": "2020"}
        enriched = {"title": "Enriched Title", "doi": "10.1234/test", "volume": "5"}

        result = enricher._merge_metadata(original, enriched)

        # Original values preserved
        assert result["title"] == "Original Title"
        assert result["year"] == "2020"
        # Missing fields filled
        assert result["doi"] == "10.1234/test"
        assert result["volume"] == "5"

    def test_merge_metadata_preserves_original(self, enricher):
        """Test that original values are not overwritten."""
        original = {"title": "Original", "year": "2020", "doi": "10.1234/original"}
        enriched = {"title": "Different", "year": "2021", "doi": "10.1234/different"}

        result = enricher._merge_metadata(original, enriched)

        assert result["title"] == "Original"
        assert result["year"] == "2020"
        assert result["doi"] == "10.1234/original"


class TestCrossRefEnricherLookup:
    """Tests for DOI lookup functionality."""

    @patch.object(CrossRefEnricher, "_make_request")
    def test_lookup_doi_success(self, mock_request, enricher, sample_crossref_response):
        """Test successful DOI lookup."""
        mock_request.return_value = sample_crossref_response

        result = enricher.lookup_doi("10.1234/test.2020.001")

        assert result is not None
        assert result["doi"] == "10.1234/test.2020.001"
        assert result["title"] == "Machine Learning in Practice"

    @patch.object(CrossRefEnricher, "_make_request")
    def test_lookup_doi_not_found(self, mock_request, enricher):
        """Test DOI lookup when not found."""
        mock_request.return_value = None

        result = enricher.lookup_doi("10.1234/nonexistent")
        assert result is None

    def test_lookup_doi_invalid(self, enricher):
        """Test lookup with invalid DOI."""
        result = enricher.lookup_doi("not-a-doi")
        assert result is None


class TestCrossRefEnricherEnrichment:
    """Tests for citation enrichment."""

    @patch.object(CrossRefEnricher, "lookup_doi")
    def test_enrich_citation_with_doi(self, mock_lookup, enricher, sample_citation):
        """Test enriching a citation that has a DOI."""
        mock_lookup.return_value = {
            "doi": "10.1234/test.2020.001",
            "title": "Machine Learning in Practice",
            "publisher": "Academic Press",
            "volume": "10",
        }

        result = enricher.enrich_citation(sample_citation)

        assert result["enriched"] is True
        assert result["enrichment_source"] == "crossref"
        assert result["publisher"] == "Academic Press"
        mock_lookup.assert_called_once_with("10.1234/test.2020.001")

    @patch.object(CrossRefEnricher, "search_by_title")
    def test_enrich_citation_without_doi(
        self, mock_search, enricher, sample_citation_no_doi
    ):
        """Test enriching a citation without DOI (searches by title)."""
        mock_search.return_value = [
            {
                "doi": "10.1234/found",
                "title": "Machine Learning in Practice",
                "publisher": "Academic Press",
            }
        ]

        result = enricher.enrich_citation(sample_citation_no_doi)

        assert result["enriched"] is True
        assert result["enrichment_source"] == "crossref_search"
        assert result["publisher"] == "Academic Press"
        mock_search.assert_called_once()

    @patch.object(CrossRefEnricher, "lookup_doi")
    def test_enrich_citation_doi_not_found(self, mock_lookup, enricher, sample_citation):
        """Test enriching when DOI lookup fails."""
        mock_lookup.return_value = None

        result = enricher.enrich_citation(sample_citation)

        # Should return original without enrichment
        assert "enriched" not in result or result.get("enriched") is not True
        assert result["title"] == sample_citation["title"]

    @patch.object(CrossRefEnricher, "enrich_citation")
    def test_enrich_citations_batch(self, mock_enrich, enricher):
        """Test batch enrichment."""
        mock_enrich.side_effect = lambda c: {**c, "enriched": True}

        citations = [
            {"title": "Title 1"},
            {"title": "Title 2"},
            {"title": "Title 3"},
        ]

        results = enricher.enrich_citations(citations)

        assert len(results) == 3
        assert all(r["enriched"] for r in results)
        assert mock_enrich.call_count == 3


class TestCrossRefEnricherSearch:
    """Tests for title search functionality."""

    @patch.object(CrossRefEnricher, "_make_request")
    def test_search_by_title_success(self, mock_request, enricher):
        """Test successful title search."""
        mock_request.return_value = {
            "message": {
                "items": [
                    {"title": ["Test Title"], "DOI": "10.1234/test1"},
                    {"title": ["Another Title"], "DOI": "10.1234/test2"},
                ]
            }
        }

        results = enricher.search_by_title("Test Title")

        assert len(results) == 2
        assert results[0]["title"] == "Test Title"

    @patch.object(CrossRefEnricher, "_make_request")
    def test_search_by_title_with_author(self, mock_request, enricher):
        """Test title search with author filter."""
        mock_request.return_value = {"message": {"items": []}}

        enricher.search_by_title("Test Title", author="Smith")

        # Verify the request was made with author parameter
        call_args = mock_request.call_args[0][0]
        assert "query.title=" in call_args
        assert "query.author=" in call_args

    @patch.object(CrossRefEnricher, "_make_request")
    def test_search_by_title_no_results(self, mock_request, enricher):
        """Test title search with no results."""
        mock_request.return_value = {"message": {"items": []}}

        results = enricher.search_by_title("Nonexistent Title")
        assert results == []

    @patch.object(CrossRefEnricher, "_make_request")
    def test_search_by_title_request_fails(self, mock_request, enricher):
        """Test title search when request fails."""
        mock_request.return_value = None

        results = enricher.search_by_title("Test Title")
        assert results == []


class TestCrossRefEnricherFileOperations:
    """Tests for file operations."""

    def test_load_citations_list_format(self, enricher, tmp_path):
        """Test loading citations from list format JSON."""
        citations = [
            {"title": "Title 1"},
            {"title": "Title 2"},
        ]
        json_path = tmp_path / "citations.json"
        json_path.write_text(json.dumps(citations))

        loaded = enricher.load_citations(json_path)
        assert len(loaded) == 2

    def test_load_citations_dict_format(self, enricher, tmp_path):
        """Test loading citations from dict format JSON."""
        data = {
            "citations": [
                {"title": "Title 1"},
                {"title": "Title 2"},
            ]
        }
        json_path = tmp_path / "citations.json"
        json_path.write_text(json.dumps(data))

        loaded = enricher.load_citations(json_path)
        assert len(loaded) == 2

    def test_load_citations_empty(self, enricher, tmp_path):
        """Test loading empty citations."""
        json_path = tmp_path / "empty.json"
        json_path.write_text("{}")

        loaded = enricher.load_citations(json_path)
        assert loaded == []

    @patch.object(CrossRefEnricher, "enrich_citations")
    def test_save_enriched(self, mock_enrich, enricher, tmp_path):
        """Test saving enriched citations."""
        mock_enrich.return_value = [
            {"title": "Title 1", "enriched": True},
            {"title": "Title 2", "enriched": True},
        ]

        citations = [{"title": "Title 1"}, {"title": "Title 2"}]
        output_path = tmp_path / "enriched.json"

        result = enricher.save_enriched(citations, output_path)

        assert Path(result).exists()
        saved = json.loads(output_path.read_text())
        assert len(saved) == 2
        assert all(c["enriched"] for c in saved)
