"""Bibliography and export routes."""

from typing import Dict

from fastapi import APIRouter, HTTPException

from academic_research_toolkit.api.models import (
    BibliographyRequest,
    BibliographyResponse,
    ExportFormat,
    ExportRequest,
    ExportResponse,
)

router = APIRouter(prefix="/bibliography", tags=["Bibliography & Export"])


@router.post("/generate", response_model=BibliographyResponse)
async def generate_bibliography(request: BibliographyRequest) -> Dict:
    """
    Generate a formatted bibliography from citations.

    - **citations**: List of citation objects
    - **format**: Output format (apa, mla, chicago)
    """
    from academic_research_toolkit.bibliography_generator import BibliographyGenerator

    try:
        generator = BibliographyGenerator(format_style=request.format.value)
        bibliography = generator.generate_bibliography(request.citations)

        return BibliographyResponse(
            bibliography=bibliography,
            format=request.format.value,
            count=len(request.citations),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Bibliography generation failed: {str(e)}"
        )


@router.post("/export/{format}", response_model=ExportResponse)
async def export_citations(format: ExportFormat, request: ExportRequest) -> Dict:
    """
    Export citations to BibTeX or RIS format.

    - **format**: Export format (bibtex or ris)
    - **citations**: List of citation objects to export
    """
    try:
        if format == ExportFormat.BIBTEX:
            from academic_research_toolkit.exporters.bibtex import BibTeXExporter

            exporter = BibTeXExporter()
            content = exporter.export(request.citations)

        elif format == ExportFormat.RIS:
            from academic_research_toolkit.exporters.ris import RISExporter

            exporter = RISExporter()
            content = exporter.export(request.citations)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export format: {format}"
            )

        return ExportResponse(
            content=content,
            format=format.value,
            count=len(request.citations),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Export failed: {str(e)}"
        )
