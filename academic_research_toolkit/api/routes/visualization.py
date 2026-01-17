"""Visualization routes for the REST API."""

from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/visualization", tags=["Visualization"])


class GraphType(str, Enum):
    """Types of graphs that can be generated."""

    KNOWLEDGE = "knowledge"
    CITATION = "citation"


class ExportFormat(str, Enum):
    """Supported graph export formats."""

    JSON = "json"
    GRAPHML = "graphml"
    GEXF = "gexf"
    DOT = "dot"
    CYTOSCAPE = "cytoscape"


class DashboardType(str, Enum):
    """Types of dashboards that can be generated."""

    CITATION = "citation"
    KNOWLEDGE = "knowledge"
    THEME = "theme"


class GraphRequest(BaseModel):
    """Request model for graph generation."""

    citations: List[Dict[str, Any]] = Field(..., description="List of citations")
    graph_type: GraphType = Field(
        GraphType.CITATION, description="Type of graph to build"
    )
    source_paper: Optional[str] = Field(
        None, description="Source paper title for citation networks"
    )


class GraphExportRequest(BaseModel):
    """Request model for graph export."""

    citations: List[Dict[str, Any]] = Field(..., description="List of citations")
    graph_type: GraphType = Field(
        GraphType.CITATION, description="Type of graph to build"
    )
    export_format: ExportFormat = Field(
        ExportFormat.JSON, description="Export format"
    )
    source_paper: Optional[str] = Field(None, description="Source paper title")


class DashboardRequest(BaseModel):
    """Request model for dashboard generation."""

    citations: List[Dict[str, Any]] = Field(..., description="List of citations")
    dashboard_type: DashboardType = Field(
        DashboardType.CITATION, description="Type of dashboard"
    )
    title: Optional[str] = Field(
        "Academic Research Dashboard", description="Dashboard title"
    )
    source_paper: Optional[str] = Field(None, description="Source paper title")
    theme_data: Optional[Dict[str, Any]] = Field(
        None, description="Theme analysis data for theme dashboards"
    )


class GraphResponse(BaseModel):
    """Response model for graph generation."""

    graph_type: str = Field(..., description="Type of graph")
    nodes: List[Dict[str, Any]] = Field(..., description="Graph nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Graph edges")
    statistics: Dict[str, Any] = Field(..., description="Graph statistics")


class GraphExportResponse(BaseModel):
    """Response model for graph export."""

    content: str = Field(..., description="Exported content")
    format: str = Field(..., description="Export format used")
    graph_type: str = Field(..., description="Type of graph")


@router.post("/graph", response_model=GraphResponse)
async def build_graph(request: GraphRequest) -> Dict:
    """
    Build a knowledge graph or citation network from citations.

    - **citations**: List of citation objects
    - **graph_type**: Type of graph (knowledge or citation)
    - **source_paper**: Source paper title (for citation networks)
    """
    try:
        if request.graph_type == GraphType.KNOWLEDGE:
            from academic_research_toolkit.visualization.knowledge_graph import (
                KnowledgeGraphBuilder,
            )

            builder = KnowledgeGraphBuilder()
            builder.build_from_citations(request.citations)
            graph_data = builder.to_dict()

            return GraphResponse(
                graph_type="knowledge",
                nodes=graph_data["entities"],
                edges=graph_data["relationships"],
                statistics=graph_data["statistics"],
            )

        else:  # citation
            from academic_research_toolkit.visualization.citation_network import (
                CitationNetworkBuilder,
            )

            builder = CitationNetworkBuilder()
            source_paper = request.source_paper or "Source Document"
            builder.build_from_citations(source_paper, request.citations)
            network_data = builder.to_dict()

            return GraphResponse(
                graph_type="citation",
                nodes=network_data["nodes"],
                edges=network_data["edges"],
                statistics=network_data["metrics"],
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Graph generation failed: {str(e)}"
        )


@router.post("/graph/export", response_model=GraphExportResponse)
async def export_graph(request: GraphExportRequest) -> Dict:
    """
    Export a graph to various formats.

    - **citations**: List of citation objects
    - **graph_type**: Type of graph (knowledge or citation)
    - **export_format**: Export format (json, graphml, gexf, dot, cytoscape)
    """
    from academic_research_toolkit.visualization.exporters import GraphExporter

    try:
        exporter = GraphExporter()

        if request.graph_type == GraphType.KNOWLEDGE:
            from academic_research_toolkit.visualization.knowledge_graph import (
                KnowledgeGraphBuilder,
            )

            builder = KnowledgeGraphBuilder()
            builder.build_from_citations(request.citations)
            graph_data = builder.to_dict()
            content = exporter.export_from_knowledge_graph(
                graph_data, request.export_format.value
            )

        else:  # citation
            from academic_research_toolkit.visualization.citation_network import (
                CitationNetworkBuilder,
            )

            builder = CitationNetworkBuilder()
            source_paper = request.source_paper or "Source Document"
            builder.build_from_citations(source_paper, request.citations)
            network_data = builder.to_dict()
            content = exporter.export_from_citation_network(
                network_data, request.export_format.value
            )

        return GraphExportResponse(
            content=content,
            format=request.export_format.value,
            graph_type=request.graph_type.value,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Graph export failed: {str(e)}"
        )


@router.post("/dashboard", response_class=HTMLResponse)
async def generate_dashboard(request: DashboardRequest) -> str:
    """
    Generate an interactive HTML dashboard.

    - **citations**: List of citation objects
    - **dashboard_type**: Type of dashboard (citation, knowledge, theme)
    - **title**: Dashboard title
    """
    from academic_research_toolkit.visualization.dashboard import DashboardGenerator

    try:
        generator = DashboardGenerator(title=request.title or "Academic Research Dashboard")

        if request.dashboard_type == DashboardType.CITATION:
            from academic_research_toolkit.visualization.citation_network import (
                CitationNetworkBuilder,
            )

            builder = CitationNetworkBuilder()
            source_paper = request.source_paper or "Source Document"
            builder.build_from_citations(source_paper, request.citations)
            network_data = builder.to_dict()
            generator.build_citation_network_dashboard(network_data)

        elif request.dashboard_type == DashboardType.KNOWLEDGE:
            from academic_research_toolkit.visualization.knowledge_graph import (
                KnowledgeGraphBuilder,
            )

            builder = KnowledgeGraphBuilder()
            builder.build_from_citations(request.citations)
            graph_data = builder.to_dict()
            generator.build_knowledge_graph_dashboard(graph_data)

        elif request.dashboard_type == DashboardType.THEME:
            if request.theme_data:
                generator.build_theme_dashboard(request.theme_data)
            else:
                generator.build_theme_dashboard({"dominant_themes": []})

        return generator.generate_html()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Dashboard generation failed: {str(e)}"
        )


@router.post("/network/metrics")
async def get_network_metrics(request: GraphRequest) -> Dict:
    """
    Get detailed metrics for a citation network.

    - **citations**: List of citation objects
    - **source_paper**: Source paper title
    """
    from academic_research_toolkit.visualization.citation_network import (
        CitationNetworkBuilder,
    )

    try:
        builder = CitationNetworkBuilder()
        source_paper = request.source_paper or "Source Document"
        builder.build_from_citations(source_paper, request.citations)

        metrics = builder.calculate_metrics()
        most_cited = builder.get_most_cited(10)
        author_network = builder.get_author_collaboration_network()

        return {
            "metrics": metrics,
            "most_cited": [
                {
                    "title": n.title,
                    "authors": n.authors,
                    "year": n.year,
                    "citations_in": n.citations_in,
                }
                for n in most_cited
            ],
            "author_collaboration": author_network,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Metrics calculation failed: {str(e)}"
        )
