"""Citation extraction and enrichment routes."""

from typing import Dict

from fastapi import APIRouter, HTTPException

from academic_research_toolkit.api.models import (
    CitationEnrichRequest,
    CitationEnrichResponse,
    CitationExtractionRequest,
    CitationExtractionResponse,
)

router = APIRouter(prefix="/citations", tags=["Citations"])


@router.post("/extract", response_model=CitationExtractionResponse)
async def extract_citations(request: CitationExtractionRequest) -> Dict:
    """
    Extract citations from provided text.

    - **text**: Text content containing citations to extract
    """
    from academic_research_toolkit.citation_extractor import CitationExtractor

    try:
        extractor = CitationExtractor()
        citations = extractor.extract_from_text(request.text)
        stats = extractor.get_stats()

        # Convert Citation objects to dicts
        citation_dicts = []
        for citation in citations:
            citation_dict = {
                "raw_text": citation.raw_text,
                "citation_type": citation.citation_type,
                "authors": citation.authors,
                "year": citation.year,
                "title": citation.title,
                "publisher": citation.publisher,
                "location": citation.location,
                "source": citation.source,
                "url": citation.url,
                "notes": citation.notes,
                "confidence": citation.confidence,
            }
            citation_dicts.append(citation_dict)

        return CitationExtractionResponse(
            citations=citation_dicts,
            count=len(citation_dicts),
            statistics=stats,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Citation extraction failed: {str(e)}"
        )


@router.post("/enrich", response_model=CitationEnrichResponse)
async def enrich_citations(request: CitationEnrichRequest) -> Dict:
    """
    Enrich citations using CrossRef API.

    Provide either:
    - **doi**: A single DOI to look up
    - **citations**: A list of citations to enrich (will look up DOIs or search by title)
    """
    from academic_research_toolkit.enrichment.crossref import CrossRefEnricher

    try:
        enricher = CrossRefEnricher(email=request.email)

        # Single DOI lookup
        if request.doi:
            metadata = enricher.lookup_doi(request.doi)
            if metadata:
                return CitationEnrichResponse(
                    citation=metadata,
                    enriched_count=1,
                )
            else:
                return CitationEnrichResponse(
                    citation={"doi": request.doi, "enriched": False},
                    enriched_count=0,
                )

        # Batch citation enrichment
        if request.citations:
            enriched = enricher.enrich_citations(request.citations)
            enriched_count = sum(1 for c in enriched if c.get("enriched"))

            return CitationEnrichResponse(
                citations=enriched,
                enriched_count=enriched_count,
            )

        raise HTTPException(
            status_code=400, detail="Either 'doi' or 'citations' must be provided"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Citation enrichment failed: {str(e)}"
        )
