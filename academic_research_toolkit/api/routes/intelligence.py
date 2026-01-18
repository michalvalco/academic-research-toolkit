"""Intelligence API routes for AI-powered research assistance."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


# Request Models
class SearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)
    threshold: float = Field(0.0, description="Minimum similarity score", ge=0.0, le=1.0)


class AskRequest(BaseModel):
    """Request model for AI Q&A."""
    question: str = Field(..., description="Research question to ask")
    context: Optional[List[Dict[str, Any]]] = Field(
        None, description="Optional context documents"
    )
    use_rag: bool = Field(True, description="Use RAG if vector store is available")


class SummarizeRequest(BaseModel):
    """Request model for paper summarization."""
    citations: List[Dict[str, Any]] = Field(..., description="List of citations to summarize")
    focus: Optional[str] = Field(None, description="Focus area for summary")


class CompareRequest(BaseModel):
    """Request model for paper comparison."""
    paper_a: Dict[str, Any] = Field(..., description="First paper data")
    paper_b: Dict[str, Any] = Field(..., description="Second paper data")


class GapsRequest(BaseModel):
    """Request model for gap detection."""
    citations: List[Dict[str, Any]] = Field(..., description="List of citations")
    themes: Optional[Dict[str, Any]] = Field(None, description="Optional theme analysis data")
    use_ai: bool = Field(False, description="Use AI for enhanced analysis")


class IndexDocumentRequest(BaseModel):
    """Request model for indexing a document."""
    doc_id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Document text content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    chunk: bool = Field(True, description="Whether to chunk the document")


class IndexCitationsRequest(BaseModel):
    """Request model for indexing citations."""
    citations: List[Dict[str, Any]] = Field(..., description="Citations to index")


# Response Models
class SearchResponse(BaseModel):
    """Response model for semantic search."""
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results returned")


class AskResponse(BaseModel):
    """Response model for AI Q&A."""
    answer: str = Field(..., description="Generated answer")
    sources: Optional[List[Dict[str, Any]]] = Field(
        None, description="Source documents used"
    )
    token_usage: Optional[Dict[str, int]] = Field(
        None, description="Token usage statistics"
    )


class SummarizeResponse(BaseModel):
    """Response model for summarization."""
    summary: str = Field(..., description="Generated summary")
    paper_count: int = Field(..., description="Number of papers summarized")
    token_usage: Optional[Dict[str, int]] = Field(
        None, description="Token usage statistics"
    )


class CompareResponse(BaseModel):
    """Response model for paper comparison."""
    comparison: Dict[str, Any] = Field(..., description="Comparison results")


class GapsResponse(BaseModel):
    """Response model for gap detection."""
    summary: Dict[str, Any] = Field(..., description="Gap analysis summary")
    temporal_gaps: List[Dict[str, Any]] = Field(
        ..., description="Temporal gaps found"
    )
    methodological_gaps: List[Dict[str, Any]] = Field(
        ..., description="Methodological gaps found"
    )
    geographic_gaps: List[Dict[str, Any]] = Field(
        ..., description="Geographic gaps found"
    )
    research_questions: List[Dict[str, Any]] = Field(
        ..., description="Suggested research questions"
    )
    recommendations: List[str] = Field(
        ..., description="Recommendations based on gaps"
    )


class IndexResponse(BaseModel):
    """Response model for indexing operations."""
    success: bool = Field(..., description="Whether indexing succeeded")
    documents_indexed: int = Field(..., description="Number of documents indexed")
    total_documents: int = Field(..., description="Total documents in store")


router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

# In-memory vector store (use persistent storage in production)
_vector_store = None


def _get_vector_store():
    """Get or create the in-memory vector store."""
    global _vector_store
    if _vector_store is None:
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            _vector_store = VectorStore(embedding_provider="local")
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Intelligence module not available: {e}"
            )
    return _vector_store


@router.post("/index/document", response_model=IndexResponse)
async def index_document(request: IndexDocumentRequest) -> Dict:
    """
    Index a single document for semantic search.

    - **doc_id**: Unique identifier for the document
    - **text**: Document text content
    - **metadata**: Optional metadata (title, authors, year)
    - **chunk**: Whether to chunk the document (default: true)
    """
    try:
        store = _get_vector_store()
        chunks_added = store.add_document(
            doc_id=request.doc_id,
            text=request.text,
            metadata=request.metadata,
            chunk=request.chunk,
        )

        return IndexResponse(
            success=True,
            documents_indexed=chunks_added,
            total_documents=len(store.documents),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/index/citations", response_model=IndexResponse)
async def index_citations(request: IndexCitationsRequest) -> Dict:
    """
    Index multiple citations for semantic search.

    - **citations**: List of citation dictionaries to index
    """
    try:
        store = _get_vector_store()
        count = store.add_citations(request.citations)

        return IndexResponse(
            success=True,
            documents_indexed=count,
            total_documents=len(store.documents),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> Dict:
    """
    Perform semantic search over indexed documents.

    - **query**: Search query text
    - **top_k**: Number of results to return (default: 5)
    - **threshold**: Minimum similarity score (default: 0.0)
    """
    try:
        store = _get_vector_store()

        if not store.documents:
            return SearchResponse(results=[], count=0)

        results = store.search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
        )

        return SearchResponse(
            results=results,
            count=len(results),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> Dict:
    """
    Answer a research question using AI.

    - **question**: Research question to ask
    - **context**: Optional context documents
    - **use_rag**: Whether to use RAG (default: true)
    """
    try:
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI module not available: {e}. Install with: pip install academic-research-toolkit[ai]"
        )

    try:
        store = _get_vector_store() if request.use_rag else None
        assistant = ResearchAssistant(vector_store=store)

        answer = assistant.ask(
            question=request.question,
            context=request.context,
            use_rag=request.use_rag,
        )

        return AskResponse(
            answer=answer,
            sources=request.context,
            token_usage=assistant.get_token_usage(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_papers(request: SummarizeRequest) -> Dict:
    """
    Generate a synthesis summary of multiple papers.

    - **citations**: List of citations to summarize
    - **focus**: Optional focus area for the summary
    """
    try:
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI module not available: {e}. Install with: pip install academic-research-toolkit[ai]"
        )

    if not request.citations:
        raise HTTPException(status_code=400, detail="No citations provided")

    try:
        assistant = ResearchAssistant()
        summary = assistant.summarize_papers(
            citations=request.citations,
            focus=request.focus,
        )

        return SummarizeResponse(
            summary=summary,
            paper_count=len(request.citations),
            token_usage=assistant.get_token_usage(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/compare", response_model=CompareResponse)
async def compare_papers(request: CompareRequest) -> Dict:
    """
    Compare two papers.

    - **paper_a**: First paper data
    - **paper_b**: Second paper data
    """
    try:
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI module not available: {e}. Install with: pip install academic-research-toolkit[ai]"
        )

    try:
        assistant = ResearchAssistant()
        comparison = assistant.compare_papers(
            paper_a=request.paper_a,
            paper_b=request.paper_b,
        )

        return CompareResponse(comparison=comparison)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post("/gaps", response_model=GapsResponse)
async def detect_gaps(request: GapsRequest) -> Dict:
    """
    Detect research gaps in citations.

    - **citations**: List of citations to analyze
    - **themes**: Optional theme analysis data
    - **use_ai**: Whether to use AI for enhanced analysis (default: false)
    """
    try:
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Intelligence module not available: {e}"
        )

    if not request.citations:
        raise HTTPException(status_code=400, detail="No citations provided")

    try:
        # Optional AI enhancement
        assistant = None
        if request.use_ai:
            try:
                from academic_research_toolkit.intelligence.assistant import ResearchAssistant
                assistant = ResearchAssistant()
            except ImportError:
                pass  # Fall back to rule-based analysis

        detector = GapDetector(assistant=assistant, use_ai=request.use_ai)
        report = detector.generate_gap_report(
            citations=request.citations,
            themes=request.themes,
        )

        return GapsResponse(
            summary=report["summary"],
            temporal_gaps=report["temporal_gaps"],
            methodological_gaps=report["methodological_gaps"],
            geographic_gaps=report["geographic_gaps"],
            research_questions=report["suggested_research_questions"],
            recommendations=report["recommendations"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap detection failed: {str(e)}")


@router.get("/stats")
async def get_store_stats() -> Dict:
    """Get statistics about the vector store."""
    try:
        store = _get_vector_store()
        return store.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/index")
async def clear_index() -> Dict:
    """Clear all documents from the vector store."""
    global _vector_store
    try:
        if _vector_store is not None:
            _vector_store.clear()
        return {"success": True, "message": "Index cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear index: {str(e)}")
