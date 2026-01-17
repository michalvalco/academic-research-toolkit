"""API route modules."""

from academic_research_toolkit.api.routes.pdf import router as pdf_router
from academic_research_toolkit.api.routes.citations import router as citations_router
from academic_research_toolkit.api.routes.themes import router as themes_router
from academic_research_toolkit.api.routes.export import router as export_router

__all__ = ["pdf_router", "citations_router", "themes_router", "export_router"]
