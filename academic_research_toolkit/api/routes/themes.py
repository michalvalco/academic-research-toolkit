"""Theme analysis routes."""

from typing import Dict

from fastapi import APIRouter, HTTPException

from academic_research_toolkit.api.models import (
    ThemeAnalysisRequest,
    ThemeAnalysisResponse,
)

router = APIRouter(prefix="/themes", tags=["Theme Analysis"])


@router.post("/analyze", response_model=ThemeAnalysisResponse)
async def analyze_themes(request: ThemeAnalysisRequest) -> Dict:
    """
    Analyze themes in the provided text.

    - **text**: Text content to analyze for themes
    """
    from academic_research_toolkit.theme_analyzer import ThemeAnalyzer

    try:
        analyzer = ThemeAnalyzer()
        analyzer.analyze_text(request.text, document_name="api_input")
        insights = analyzer.generate_insights()

        return ThemeAnalysisResponse(
            dominant_themes=insights.get("dominant_themes", []),
            corpus_statistics=insights.get("corpus_statistics", {}),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Theme analysis failed: {str(e)}"
        )
