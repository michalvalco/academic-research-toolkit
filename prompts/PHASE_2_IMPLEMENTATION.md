# Phase 2 Implementation Prompt: Integration Layer

## Objective
Enable external tool connections by adding export formats, API access, and citation enrichment to the Academic Research Toolkit.

## Prerequisites
Phase 1 is complete. The package is installed at `academic_research_toolkit/` with:
- Unified CLI (`research-toolkit` command)
- 5 core modules (pdf_processor, citation_extractor, theme_analyzer, affiliation_extractor, bibliography_generator)
- Test suite (85 tests passing)
- `pyproject.toml` for packaging

## Implementation Tasks

### Task 1: BibTeX Export
Add BibTeX export to bibliography generator.

**File:** `academic_research_toolkit/exporters/bibtex.py`

```python
class BibTeXExporter:
    """Export citations to BibTeX format."""

    def export(self, citations: List[Dict]) -> str:
        """Convert citations to BibTeX entries."""
        # Generate @book, @article, @misc entries
        # Handle special characters (LaTeX escaping)
        # Generate unique citation keys (author_year_title)

    def save(self, citations: List[Dict], output_path: Path) -> str:
        """Save citations to .bib file."""
```

**BibTeX Format:**
```bibtex
@book{smith_2020_introduction,
    author = {Smith, John},
    title = {Introduction to AI},
    year = {2020},
    publisher = {Academic Press},
    address = {New York}
}
```

### Task 2: RIS Export
Add RIS format export for reference managers.

**File:** `academic_research_toolkit/exporters/ris.py`

```python
class RISExporter:
    """Export citations to RIS format."""

    def export(self, citations: List[Dict]) -> str:
        """Convert citations to RIS entries."""
        # TY - TYPE, AU - Author, TI - Title, PY - Year, etc.

    def save(self, citations: List[Dict], output_path: Path) -> str:
        """Save citations to .ris file."""
```

**RIS Format:**
```
TY  - BOOK
AU  - Smith, John
TI  - Introduction to AI
PY  - 2020
PB  - Academic Press
CY  - New York
ER  -
```

### Task 3: CrossRef DOI Enrichment
Add DOI-based metadata enrichment using CrossRef API.

**File:** `academic_research_toolkit/enrichment/crossref.py`

```python
class CrossRefEnricher:
    """Enrich citations using CrossRef API."""

    CROSSREF_API = "https://api.crossref.org/works/"

    def lookup_doi(self, doi: str) -> Optional[Dict]:
        """Fetch metadata for a DOI."""
        # GET https://api.crossref.org/works/{doi}
        # Parse response, extract author, title, year, journal, etc.

    def enrich_citation(self, citation: Dict) -> Dict:
        """Enrich a citation if DOI is present."""

    def search_by_title(self, title: str, author: str = None) -> List[Dict]:
        """Search CrossRef for matching works."""
        # GET https://api.crossref.org/works?query.title={title}
```

**No API key required** - CrossRef API is free (polite pool with email in User-Agent).

### Task 4: REST API (FastAPI)
Create REST API wrapper for all toolkit functionality.

**File:** `academic_research_toolkit/api/main.py`

```python
from fastapi import FastAPI, UploadFile, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(
    title="Academic Research Toolkit API",
    version="1.0.0",
    description="REST API for processing academic PDFs"
)

# Endpoints:
# POST /pdf/extract - Upload PDF, get extracted text
# POST /citations/extract - Extract citations from text
# POST /citations/enrich - Enrich citations via CrossRef
# POST /themes/analyze - Analyze themes in text
# POST /bibliography/generate - Generate formatted bibliography
# GET  /bibliography/export/{format} - Export to BibTeX/RIS
# POST /process - Full pipeline (background task)
# GET  /jobs/{job_id} - Check job status
```

**Models:**
```python
class ExtractionRequest(BaseModel):
    text: str

class CitationResponse(BaseModel):
    citations: List[Dict]
    count: int

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    result_url: Optional[str]
```

### Task 5: Batch Upload Endpoint
Add endpoint for processing multiple files.

```python
@app.post("/batch/upload")
async def batch_upload(
    files: List[UploadFile],
    background_tasks: BackgroundTasks
) -> Dict:
    """Upload multiple PDFs for batch processing."""
    job_id = str(uuid.uuid4())
    background_tasks.add_task(process_batch, job_id, files)
    return {"job_id": job_id, "status": "queued", "file_count": len(files)}
```

### Task 6: CLI Export Commands
Add export subcommands to CLI.

```bash
research-toolkit export bibtex -i citations.json -o refs.bib
research-toolkit export ris -i citations.json -o refs.ris
research-toolkit enrich -i citations.json -o enriched.json
```

### Task 7: Update pyproject.toml
Add new dependencies.

```toml
[project.optional-dependencies]
api = [
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
    "python-multipart>=0.0.6",
]
enrichment = [
    "httpx>=0.24.0",  # For async HTTP requests
]
```

### Task 8: Tests
Add tests for new functionality.

```
tests/
├── test_bibtex_exporter.py
├── test_ris_exporter.py
├── test_crossref_enricher.py
├── test_api.py  # FastAPI TestClient tests
└── fixtures/
    └── sample_citations.json
```

## Directory Structure After Phase 2

```
academic_research_toolkit/
├── __init__.py
├── cli.py                    # Updated with export commands
├── pdf_processor.py
├── citation_extractor.py
├── theme_analyzer.py
├── affiliation_extractor.py
├── bibliography_generator.py
├── utils/
│   ├── exceptions.py
│   └── validation.py
├── exporters/               # NEW
│   ├── __init__.py
│   ├── bibtex.py
│   └── ris.py
├── enrichment/              # NEW
│   ├── __init__.py
│   └── crossref.py
└── api/                     # NEW
    ├── __init__.py
    ├── main.py
    ├── routes/
    │   ├── pdf.py
    │   ├── citations.py
    │   ├── themes.py
    │   └── export.py
    └── models.py
```

## Success Criteria

1. `research-toolkit export bibtex -i citations.json -o refs.bib` works
2. `research-toolkit export ris -i citations.json -o refs.ris` works
3. `research-toolkit enrich -i citations.json` enriches via CrossRef
4. `uvicorn academic_research_toolkit.api.main:app` starts API server
5. API endpoints return proper JSON responses
6. All new tests pass
7. Existing 85 tests still pass

## Execution Order

1. Create exporters directory with BibTeX exporter
2. Add RIS exporter
3. Create enrichment directory with CrossRef client
4. Update CLI with export and enrich commands
5. Create API directory structure
6. Implement FastAPI routes
7. Add background job processing
8. Write tests for all new functionality
9. Update pyproject.toml with new dependencies
10. Verify everything works together

## API Usage Examples

```bash
# Start API server
uvicorn academic_research_toolkit.api.main:app --reload

# Extract citations from text
curl -X POST http://localhost:8000/citations/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Smith, J. (2020). Introduction to AI. Academic Press."}'

# Export to BibTeX
curl http://localhost:8000/bibliography/export/bibtex \
  -H "Content-Type: application/json" \
  -d '{"citations": [...]}'

# Enrich citation with DOI
curl -X POST http://localhost:8000/citations/enrich \
  -H "Content-Type: application/json" \
  -d '{"doi": "10.1000/xyz123"}'
```

## Notes

- CrossRef API is free but rate-limited; add polite delay between requests
- Use httpx for async HTTP in API, requests for CLI
- BibTeX keys should be unique and URL-safe
- RIS format uses specific two-letter tags (TY, AU, TI, PY, etc.)
- FastAPI auto-generates OpenAPI docs at /docs
