"""
Academic Research Toolkit REST API

FastAPI-based REST API for processing academic PDFs and managing citations.

Usage:
    uvicorn academic_research_toolkit.api.main:app --reload
"""

import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile

from academic_research_toolkit import __version__
from academic_research_toolkit.api.models import (
    BatchUploadResponse,
    HealthResponse,
    JobStatus,
    JobStatusResponse,
)
from academic_research_toolkit.api.routes import (
    citations_router,
    export_router,
    pdf_router,
    themes_router,
    visualization_router,
)

app = FastAPI(
    title="Academic Research Toolkit API",
    version=__version__,
    description="REST API for processing academic PDFs, extracting citations, "
    "analyzing themes, and generating bibliographies.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
app.include_router(pdf_router)
app.include_router(citations_router)
app.include_router(themes_router)
app.include_router(export_router)
app.include_router(visualization_router)

# In-memory job storage (use Redis or database in production)
_jobs: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_model=HealthResponse)
async def root() -> Dict:
    """API health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> Dict:
    """API health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
    )


@app.post("/process", response_model=BatchUploadResponse)
async def process_full_pipeline(
    file: UploadFile,
    background_tasks: BackgroundTasks,
) -> Dict:
    """
    Process a single PDF through the full pipeline (background task).

    - **file**: PDF file to process

    Returns a job ID that can be used to check status via GET /jobs/{job_id}
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    job_id = str(uuid.uuid4())

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    # Initialize job status
    _jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "result": None,
        "error": None,
        "file_path": str(tmp_path),
        "filename": file.filename,
    }

    # Add background task
    background_tasks.add_task(process_single_pdf, job_id, tmp_path)

    return BatchUploadResponse(
        job_id=job_id,
        status="queued",
        file_count=1,
    )


@app.post("/batch/upload", response_model=BatchUploadResponse)
async def batch_upload(
    files: List[UploadFile],
    background_tasks: BackgroundTasks,
) -> Dict:
    """
    Upload multiple PDFs for batch processing.

    - **files**: List of PDF files to process

    Returns a job ID that can be used to check status via GET /jobs/{job_id}
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Validate all files are PDFs
    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"All files must be PDFs. Invalid file: {file.filename}",
            )

    job_id = str(uuid.uuid4())

    # Save all uploaded files to temp locations
    file_paths = []
    for file in files:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            file_paths.append({
                "path": Path(tmp.name),
                "filename": file.filename,
            })

    # Initialize job status
    _jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "result": None,
        "error": None,
        "files": file_paths,
        "file_count": len(files),
    }

    # Add background task
    background_tasks.add_task(process_batch, job_id, file_paths)

    return BatchUploadResponse(
        job_id=job_id,
        status="queued",
        file_count=len(files),
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> Dict:
    """
    Check the status of a processing job.

    - **job_id**: The job ID returned from /process or /batch/upload
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    job = _jobs[job_id]

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        result=job.get("result"),
        error=job.get("error"),
    )


async def process_single_pdf(job_id: str, pdf_path: Path) -> None:
    """Background task to process a single PDF through the full pipeline."""
    from academic_research_toolkit.citation_extractor import CitationExtractor
    from academic_research_toolkit.pdf_processor import PDFProcessor
    from academic_research_toolkit.theme_analyzer import ThemeAnalyzer

    try:
        _jobs[job_id]["status"] = JobStatus.PROCESSING
        _jobs[job_id]["progress"] = 0

        result = {}

        # Step 1: Extract PDF text and metadata (25%)
        processor = PDFProcessor()
        metadata = processor.extract_metadata(pdf_path)
        text = processor.extract_text(pdf_path)
        cleaned_text = processor.clean_text(text)

        result["pdf"] = {
            "metadata": metadata,
            "text_length": len(cleaned_text),
        }
        _jobs[job_id]["progress"] = 25

        # Step 2: Extract citations (50%)
        extractor = CitationExtractor()
        citations = extractor.extract_from_text(cleaned_text)
        citation_dicts = []
        for citation in citations:
            citation_dicts.append({
                "raw_text": citation.raw_text,
                "citation_type": citation.citation_type,
                "authors": citation.authors,
                "year": citation.year,
                "title": citation.title,
                "publisher": citation.publisher,
                "confidence": citation.confidence,
            })

        result["citations"] = {
            "count": len(citation_dicts),
            "citations": citation_dicts,
        }
        _jobs[job_id]["progress"] = 50

        # Step 3: Analyze themes (75%)
        analyzer = ThemeAnalyzer()
        analyzer.analyze_text(cleaned_text, document_name="uploaded_pdf")
        insights = analyzer.generate_insights()

        result["themes"] = {
            "dominant_themes": insights.get("dominant_themes", [])[:10],
            "corpus_statistics": insights.get("corpus_statistics", {}),
        }
        _jobs[job_id]["progress"] = 75

        # Step 4: Complete (100%)
        _jobs[job_id]["status"] = JobStatus.COMPLETED
        _jobs[job_id]["progress"] = 100
        _jobs[job_id]["result"] = result

    except Exception as e:
        _jobs[job_id]["status"] = JobStatus.FAILED
        _jobs[job_id]["error"] = str(e)
    finally:
        # Clean up temp file
        pdf_path.unlink(missing_ok=True)


async def process_batch(job_id: str, file_paths: List[Dict]) -> None:
    """Background task to process multiple PDFs."""
    from academic_research_toolkit.citation_extractor import CitationExtractor
    from academic_research_toolkit.pdf_processor import PDFProcessor
    from academic_research_toolkit.theme_analyzer import ThemeAnalyzer

    try:
        _jobs[job_id]["status"] = JobStatus.PROCESSING
        _jobs[job_id]["progress"] = 0

        total_files = len(file_paths)
        results = []
        all_citations = []
        analyzer = ThemeAnalyzer()

        for i, file_info in enumerate(file_paths):
            pdf_path = file_info["path"]
            filename = file_info["filename"]

            try:
                # Process PDF
                processor = PDFProcessor()
                metadata = processor.extract_metadata(pdf_path)
                text = processor.extract_text(pdf_path)
                cleaned_text = processor.clean_text(text)

                # Extract citations
                extractor = CitationExtractor()
                citations = extractor.extract_from_text(cleaned_text)
                citation_dicts = []
                for citation in citations:
                    citation_dict = {
                        "raw_text": citation.raw_text,
                        "citation_type": citation.citation_type,
                        "authors": citation.authors,
                        "year": citation.year,
                        "title": citation.title,
                    }
                    citation_dicts.append(citation_dict)
                    all_citations.append(citation_dict)

                # Add text to theme analyzer
                analyzer.analyze_text(cleaned_text, document_name=filename)

                results.append({
                    "filename": filename,
                    "success": True,
                    "text_length": len(cleaned_text),
                    "citations_count": len(citation_dicts),
                    "metadata": metadata,
                })

            except Exception as e:
                results.append({
                    "filename": filename,
                    "success": False,
                    "error": str(e),
                })
            finally:
                # Clean up temp file
                pdf_path.unlink(missing_ok=True)

            # Update progress
            _jobs[job_id]["progress"] = int((i + 1) / total_files * 100)

        # Generate combined theme analysis
        insights = analyzer.generate_insights()

        _jobs[job_id]["status"] = JobStatus.COMPLETED
        _jobs[job_id]["progress"] = 100
        _jobs[job_id]["result"] = {
            "files_processed": len([r for r in results if r.get("success")]),
            "files_failed": len([r for r in results if not r.get("success")]),
            "total_citations": len(all_citations),
            "file_results": results,
            "combined_themes": {
                "dominant_themes": insights.get("dominant_themes", [])[:10],
                "corpus_statistics": insights.get("corpus_statistics", {}),
            },
        }

    except Exception as e:
        _jobs[job_id]["status"] = JobStatus.FAILED
        _jobs[job_id]["error"] = str(e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
