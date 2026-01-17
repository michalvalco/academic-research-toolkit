"""Pydantic models for the REST API."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats."""

    BIBTEX = "bibtex"
    RIS = "ris"


class CitationFormat(str, Enum):
    """Supported citation formats."""

    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"


class JobStatus(str, Enum):
    """Job processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models


class TextExtractionRequest(BaseModel):
    """Request model for text extraction."""

    text: str = Field(..., description="Text content to process")


class CitationExtractionRequest(BaseModel):
    """Request model for citation extraction from text."""

    text: str = Field(..., description="Text content containing citations")


class CitationEnrichRequest(BaseModel):
    """Request model for citation enrichment."""

    doi: Optional[str] = Field(None, description="DOI to look up")
    citations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Citations to enrich"
    )
    email: Optional[str] = Field(
        None, description="Email for CrossRef polite pool (recommended)"
    )


class ThemeAnalysisRequest(BaseModel):
    """Request model for theme analysis."""

    text: str = Field(..., description="Text content to analyze")


class BibliographyRequest(BaseModel):
    """Request model for bibliography generation."""

    citations: List[Dict[str, Any]] = Field(..., description="List of citations")
    format: CitationFormat = Field(
        CitationFormat.APA, description="Output format (apa, mla, chicago)"
    )


class ExportRequest(BaseModel):
    """Request model for citation export."""

    citations: List[Dict[str, Any]] = Field(..., description="List of citations")


# Response Models


class CitationData(BaseModel):
    """Individual citation data."""

    raw_text: Optional[str] = None
    citation_type: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[str] = None
    title: Optional[str] = None
    publisher: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[float] = None
    enriched: Optional[bool] = None
    enrichment_source: Optional[str] = None


class CitationExtractionResponse(BaseModel):
    """Response model for citation extraction."""

    citations: List[Dict[str, Any]] = Field(..., description="Extracted citations")
    count: int = Field(..., description="Number of citations extracted")
    statistics: Optional[Dict[str, Any]] = Field(
        None, description="Extraction statistics"
    )


class CitationEnrichResponse(BaseModel):
    """Response model for citation enrichment."""

    citation: Optional[Dict[str, Any]] = Field(
        None, description="Enriched citation (single)"
    )
    citations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Enriched citations (batch)"
    )
    enriched_count: int = Field(0, description="Number of citations that were enriched")


class ThemeAnalysisResponse(BaseModel):
    """Response model for theme analysis."""

    dominant_themes: List[Dict[str, Any]] = Field(
        ..., description="Dominant themes found"
    )
    corpus_statistics: Dict[str, Any] = Field(..., description="Corpus statistics")


class BibliographyResponse(BaseModel):
    """Response model for bibliography generation."""

    bibliography: str = Field(..., description="Formatted bibliography text")
    format: str = Field(..., description="Format used")
    count: int = Field(..., description="Number of citations in bibliography")


class ExportResponse(BaseModel):
    """Response model for citation export."""

    content: str = Field(..., description="Exported content (BibTeX or RIS)")
    format: str = Field(..., description="Export format used")
    count: int = Field(..., description="Number of entries exported")


class PDFExtractionResponse(BaseModel):
    """Response model for PDF extraction."""

    text: str = Field(..., description="Extracted text content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="PDF metadata")
    text_length: int = Field(..., description="Length of extracted text")


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchUploadResponse(BaseModel):
    """Response model for batch upload."""

    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Initial status (queued)")
    file_count: int = Field(..., description="Number of files queued for processing")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="API health status")
    version: str = Field(..., description="API version")
