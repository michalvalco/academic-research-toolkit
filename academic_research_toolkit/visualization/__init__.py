"""Visualization module for academic research analysis.

Provides tools for generating knowledge graphs, citation networks,
and interactive dashboards from academic research data.
"""

from academic_research_toolkit.visualization.knowledge_graph import KnowledgeGraphBuilder
from academic_research_toolkit.visualization.citation_network import CitationNetworkBuilder
from academic_research_toolkit.visualization.dashboard import DashboardGenerator
from academic_research_toolkit.visualization.exporters import GraphExporter

__all__ = [
    "KnowledgeGraphBuilder",
    "CitationNetworkBuilder",
    "DashboardGenerator",
    "GraphExporter",
]
