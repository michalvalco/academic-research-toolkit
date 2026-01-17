"""Tests for the FastAPI REST API."""

from unittest.mock import MagicMock, patch

import pytest

# Check if FastAPI is available
try:
    from fastapi.testclient import TestClient
    from academic_research_toolkit.api.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# Skip all tests in this module if FastAPI is not installed
pytestmark = pytest.mark.skipif(
    not FASTAPI_AVAILABLE,
    reason="FastAPI not installed. Install with: pip install fastapi uvicorn python-multipart"
)


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_text():
    """Sample academic text with citations."""
    return """
    This paper explores artificial intelligence applications.

    References:
    Smith, J. (2020). Introduction to AI. Academic Press.
    Johnson, R. (2021). "Machine Learning in Healthcare." Journal of AI Research, 15(3), 100-120.
    """


@pytest.fixture
def sample_citations():
    """Sample citations for testing."""
    return [
        {
            "citation_type": "book",
            "authors": ["Smith, John"],
            "title": "Introduction to AI",
            "year": "2020",
            "publisher": "Academic Press",
        },
        {
            "citation_type": "article",
            "authors": ["Johnson, Robert"],
            "title": "Machine Learning in Healthcare",
            "year": "2021",
            "source": "Journal of AI Research",
            "volume": "15",
            "issue": "3",
            "pages": "100-120",
        },
    ]


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns health status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCitationEndpoints:
    """Tests for citation extraction and enrichment endpoints."""

    def test_extract_citations(self, client, sample_text):
        """Test citation extraction endpoint."""
        response = client.post(
            "/citations/extract",
            json={"text": sample_text}
        )
        assert response.status_code == 200
        data = response.json()
        assert "citations" in data
        assert "count" in data
        assert data["count"] >= 0

    def test_extract_citations_empty_text(self, client):
        """Test citation extraction with empty text."""
        response = client.post(
            "/citations/extract",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    @patch("academic_research_toolkit.enrichment.crossref.CrossRefEnricher")
    def test_enrich_citation_doi(self, mock_enricher_class, client):
        """Test citation enrichment by DOI."""
        mock_enricher = MagicMock()
        mock_enricher.lookup_doi.return_value = {
            "doi": "10.1234/test",
            "title": "Test Title",
            "authors": ["Smith, John"],
        }
        mock_enricher_class.return_value = mock_enricher

        response = client.post(
            "/citations/enrich",
            json={"doi": "10.1234/test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "citation" in data or "citations" in data

    @patch("academic_research_toolkit.enrichment.crossref.CrossRefEnricher")
    def test_enrich_citations_batch(self, mock_enricher_class, client, sample_citations):
        """Test batch citation enrichment."""
        mock_enricher = MagicMock()
        mock_enricher.enrich_citations.return_value = [
            {**c, "enriched": True} for c in sample_citations
        ]
        mock_enricher_class.return_value = mock_enricher

        response = client.post(
            "/citations/enrich",
            json={"citations": sample_citations}
        )
        assert response.status_code == 200
        data = response.json()
        assert "citations" in data
        assert "enriched_count" in data

    def test_enrich_citation_missing_params(self, client):
        """Test enrichment endpoint with missing parameters."""
        response = client.post(
            "/citations/enrich",
            json={}
        )
        assert response.status_code == 400


class TestThemeEndpoints:
    """Tests for theme analysis endpoints."""

    def test_analyze_themes(self, client, sample_text):
        """Test theme analysis endpoint."""
        response = client.post(
            "/themes/analyze",
            json={"text": sample_text}
        )
        assert response.status_code == 200
        data = response.json()
        assert "dominant_themes" in data
        assert "corpus_statistics" in data

    def test_analyze_themes_empty_text(self, client):
        """Test theme analysis with empty text."""
        response = client.post(
            "/themes/analyze",
            json={"text": ""}
        )
        assert response.status_code == 200


class TestBibliographyEndpoints:
    """Tests for bibliography generation endpoints."""

    def test_generate_bibliography(self, client, sample_citations):
        """Test bibliography generation endpoint."""
        response = client.post(
            "/bibliography/generate",
            json={"citations": sample_citations, "format": "apa"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "bibliography" in data
        assert data["format"] == "apa"
        assert data["count"] == len(sample_citations)

    def test_generate_bibliography_mla(self, client, sample_citations):
        """Test bibliography generation with MLA format."""
        response = client.post(
            "/bibliography/generate",
            json={"citations": sample_citations, "format": "mla"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "mla"

    def test_generate_bibliography_chicago(self, client, sample_citations):
        """Test bibliography generation with Chicago format."""
        response = client.post(
            "/bibliography/generate",
            json={"citations": sample_citations, "format": "chicago"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "chicago"


class TestExportEndpoints:
    """Tests for citation export endpoints."""

    def test_export_bibtex(self, client, sample_citations):
        """Test BibTeX export endpoint."""
        response = client.post(
            "/bibliography/export/bibtex",
            json={"citations": sample_citations}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["format"] == "bibtex"
        assert "@book{" in data["content"] or "@article{" in data["content"]

    def test_export_ris(self, client, sample_citations):
        """Test RIS export endpoint."""
        response = client.post(
            "/bibliography/export/ris",
            json={"citations": sample_citations}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["format"] == "ris"
        assert "TY  - " in data["content"]

    def test_export_empty_citations(self, client):
        """Test export with empty citations list."""
        response = client.post(
            "/bibliography/export/bibtex",
            json={"citations": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


class TestPDFEndpoints:
    """Tests for PDF processing endpoints."""

    def test_extract_pdf_invalid_file(self, client):
        """Test PDF extraction with non-PDF file."""
        # Create a fake text file
        response = client.post(
            "/pdf/extract",
            files={"file": ("test.txt", b"Not a PDF", "text/plain")}
        )
        assert response.status_code == 400

    def test_extract_pdf_no_file(self, client):
        """Test PDF extraction without file."""
        response = client.post("/pdf/extract")
        assert response.status_code == 422  # Validation error


class TestJobEndpoints:
    """Tests for background job endpoints."""

    def test_get_job_status_not_found(self, client):
        """Test getting status of non-existent job."""
        response = client.get("/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_batch_upload_no_files(self, client):
        """Test batch upload with no files."""
        response = client.post("/batch/upload", files=[])
        assert response.status_code == 422  # Validation error

    def test_batch_upload_invalid_files(self, client):
        """Test batch upload with non-PDF files."""
        response = client.post(
            "/batch/upload",
            files=[("files", ("test.txt", b"Not a PDF", "text/plain"))]
        )
        assert response.status_code == 400


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_docs(self, client):
        """Test OpenAPI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_docs(self, client):
        """Test ReDoc documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "Academic Research Toolkit API"


class TestAPIModels:
    """Tests for API model validation."""

    def test_invalid_citation_format(self, client, sample_citations):
        """Test bibliography generation with invalid format."""
        response = client.post(
            "/bibliography/generate",
            json={"citations": sample_citations, "format": "invalid"}
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_export_format(self, client, sample_citations):
        """Test export with invalid format."""
        response = client.post(
            "/bibliography/export/invalid",
            json={"citations": sample_citations}
        )
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self, client):
        """Test endpoint with missing required fields."""
        response = client.post(
            "/citations/extract",
            json={}
        )
        assert response.status_code == 422  # Validation error
