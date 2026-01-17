"""PDF processing routes."""

import tempfile
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, HTTPException, UploadFile

from academic_research_toolkit.api.models import PDFExtractionResponse

router = APIRouter(prefix="/pdf", tags=["PDF Processing"])


@router.post("/extract", response_model=PDFExtractionResponse)
async def extract_pdf(file: UploadFile) -> Dict:
    """
    Extract text and metadata from an uploaded PDF file.

    - **file**: PDF file to process
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    from academic_research_toolkit.pdf_processor import PDFProcessor

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        processor = PDFProcessor()

        # Extract metadata
        metadata = processor.extract_metadata(tmp_path)

        # Extract text
        text = processor.extract_text(tmp_path)
        cleaned_text = processor.clean_text(text)

        return PDFExtractionResponse(
            text=cleaned_text,
            metadata=metadata,
            text_length=len(cleaned_text),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
    finally:
        # Clean up temp file
        tmp_path.unlink(missing_ok=True)
