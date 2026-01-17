"""Dashboard Generator for academic research visualization.

Creates interactive HTML dashboards for exploring research data.
Uses Plotly for visualizations with fallback to basic HTML if not available.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import plotly, provide fallback if not available
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Try to import networkx for graph layouts
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class DashboardGenerator:
    """Generates interactive HTML dashboards for research visualization.

    Creates visual representations of knowledge graphs, citation networks,
    and theme analyses using Plotly or basic HTML fallback.
    """

    # Color schemes
    ENTITY_COLORS = {
        "paper": "#3498db",  # Blue
        "author": "#2ecc71",  # Green
        "concept": "#e74c3c",  # Red
        "institution": "#9b59b6",  # Purple
    }

    RELATIONSHIP_COLORS = {
        "cites": "#95a5a6",  # Gray
        "authored_by": "#2ecc71",  # Green
        "affiliated_with": "#9b59b6",  # Purple
        "discusses": "#e74c3c",  # Red
        "related_to": "#f39c12",  # Orange
    }

    def __init__(self, title: str = "Academic Research Dashboard"):
        """
        Initialize the dashboard generator.

        Args:
            title: Dashboard title
        """
        self.title = title
        self.figures: List[Dict[str, Any]] = []

    def _check_plotly(self) -> bool:
        """Check if Plotly is available."""
        if not PLOTLY_AVAILABLE:
            return False
        return True

    def create_network_graph(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        title: str = "Network Graph",
        node_color_field: str = "type",
        node_size_field: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create an interactive network graph visualization.

        Args:
            nodes: List of node dictionaries with 'id', 'label', optionally 'type'
            edges: List of edge dictionaries with 'source', 'target'
            title: Graph title
            node_color_field: Field to use for node coloring
            node_size_field: Field to use for node sizing

        Returns:
            Plotly figure object or None if Plotly not available
        """
        if not self._check_plotly():
            return None

        # Calculate node positions
        positions = self._calculate_layout(nodes, edges)

        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")
            if source_id in positions and target_id in positions:
                x0, y0 = positions[source_id]
                x1, y1 = positions[target_id]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines",
        )

        # Create node traces grouped by type
        node_traces = []
        nodes_by_type: Dict[str, List[Dict]] = {}

        for node in nodes:
            node_type = node.get(node_color_field, "default")
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)

        for node_type, type_nodes in nodes_by_type.items():
            node_x = []
            node_y = []
            node_text = []
            node_sizes = []

            for node in type_nodes:
                node_id = node.get("id")
                if node_id in positions:
                    x, y = positions[node_id]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(node.get("label", node_id))

                    if node_size_field and node_size_field in node:
                        size = min(30, 10 + node[node_size_field])
                    else:
                        size = 15
                    node_sizes.append(size)

            color = self.ENTITY_COLORS.get(node_type, "#95a5a6")

            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                hoverinfo="text",
                text=node_text,
                textposition="top center",
                name=node_type.capitalize(),
                marker=dict(
                    showscale=False,
                    color=color,
                    size=node_sizes,
                    line_width=2,
                ),
            )
            node_traces.append(node_trace)

        fig = go.Figure(
            data=[edge_trace] + node_traces,
            layout=go.Layout(
                title=title,
                titlefont_size=16,
                showlegend=True,
                hovermode="closest",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="white",
            ),
        )

        self.figures.append({"type": "network", "title": title, "figure": fig})
        return fig

    def create_bar_chart(
        self,
        data: List[Dict],
        x_field: str,
        y_field: str,
        title: str = "Bar Chart",
        color: str = "#3498db",
        orientation: str = "v",
    ) -> Optional[Any]:
        """
        Create a bar chart visualization.

        Args:
            data: List of data dictionaries
            x_field: Field for x-axis values
            y_field: Field for y-axis values
            title: Chart title
            color: Bar color
            orientation: 'v' for vertical, 'h' for horizontal

        Returns:
            Plotly figure object or None
        """
        if not self._check_plotly():
            return None

        x_values = [d.get(x_field, "") for d in data]
        y_values = [d.get(y_field, 0) for d in data]

        if orientation == "h":
            fig = go.Figure(
                data=[go.Bar(y=x_values, x=y_values, orientation="h", marker_color=color)]
            )
        else:
            fig = go.Figure(
                data=[go.Bar(x=x_values, y=y_values, marker_color=color)]
            )

        fig.update_layout(
            title=title,
            xaxis_title=x_field.replace("_", " ").title(),
            yaxis_title=y_field.replace("_", " ").title(),
            plot_bgcolor="white",
        )

        self.figures.append({"type": "bar", "title": title, "figure": fig})
        return fig

    def create_pie_chart(
        self, data: Dict[str, int], title: str = "Distribution"
    ) -> Optional[Any]:
        """
        Create a pie chart visualization.

        Args:
            data: Dictionary mapping labels to values
            title: Chart title

        Returns:
            Plotly figure object or None
        """
        if not self._check_plotly():
            return None

        labels = list(data.keys())
        values = list(data.values())

        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.update_layout(title=title)

        self.figures.append({"type": "pie", "title": title, "figure": fig})
        return fig

    def create_timeline(
        self, data: Dict[str, int], title: str = "Timeline"
    ) -> Optional[Any]:
        """
        Create a timeline visualization.

        Args:
            data: Dictionary mapping years to counts
            title: Chart title

        Returns:
            Plotly figure object or None
        """
        if not self._check_plotly():
            return None

        sorted_data = sorted(data.items(), key=lambda x: x[0])
        years = [d[0] for d in sorted_data]
        counts = [d[1] for d in sorted_data]

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=years,
                    y=counts,
                    mode="lines+markers",
                    line=dict(color="#3498db", width=2),
                    marker=dict(size=8),
                )
            ]
        )

        fig.update_layout(
            title=title,
            xaxis_title="Year",
            yaxis_title="Count",
            plot_bgcolor="white",
        )

        self.figures.append({"type": "timeline", "title": title, "figure": fig})
        return fig

    def create_heatmap(
        self,
        matrix: List[List[float]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "Heatmap",
    ) -> Optional[Any]:
        """
        Create a heatmap visualization.

        Args:
            matrix: 2D matrix of values
            x_labels: Labels for x-axis
            y_labels: Labels for y-axis
            title: Chart title

        Returns:
            Plotly figure object or None
        """
        if not self._check_plotly():
            return None

        fig = go.Figure(
            data=go.Heatmap(z=matrix, x=x_labels, y=y_labels, colorscale="Blues")
        )

        fig.update_layout(title=title)

        self.figures.append({"type": "heatmap", "title": title, "figure": fig})
        return fig

    def _calculate_layout(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calculate node positions for graph layout.

        Uses NetworkX if available, otherwise falls back to circular layout.
        """
        positions = {}

        if NETWORKX_AVAILABLE and nodes:
            # Create NetworkX graph for layout calculation
            G = nx.DiGraph()
            for node in nodes:
                G.add_node(node.get("id"))
            for edge in edges:
                G.add_edge(edge.get("source"), edge.get("target"))

            # Use spring layout
            try:
                pos = nx.spring_layout(G, k=2, iterations=50)
                positions = {node_id: (float(x), float(y)) for node_id, (x, y) in pos.items()}
            except Exception:
                pass

        # Fallback to circular layout
        if not positions and nodes:
            n = len(nodes)
            for i, node in enumerate(nodes):
                angle = 2 * math.pi * i / n
                x = math.cos(angle)
                y = math.sin(angle)
                positions[node.get("id")] = (x, y)

        return positions

    def build_knowledge_graph_dashboard(
        self, knowledge_graph_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Build a complete dashboard from knowledge graph data.

        Args:
            knowledge_graph_data: Output from KnowledgeGraphBuilder.to_dict()

        Returns:
            Combined figure or None
        """
        if not self._check_plotly():
            return None

        entities = knowledge_graph_data.get("entities", [])
        relationships = knowledge_graph_data.get("relationships", [])
        statistics = knowledge_graph_data.get("statistics", {})

        # Create network graph
        nodes = [
            {"id": e["id"], "label": e["label"], "type": e["type"]} for e in entities
        ]
        edges = [{"source": r["source"], "target": r["target"]} for r in relationships]

        self.create_network_graph(nodes, edges, title="Knowledge Graph")

        # Create entity distribution chart
        entity_dist = statistics.get("entities_by_type", {})
        if entity_dist:
            self.create_pie_chart(entity_dist, title="Entity Distribution")

        # Create relationship distribution chart
        rel_dist = statistics.get("relationships_by_type", {})
        if rel_dist:
            self.create_pie_chart(rel_dist, title="Relationship Distribution")

        return self.figures

    def build_citation_network_dashboard(
        self, citation_network_data: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Build a complete dashboard from citation network data.

        Args:
            citation_network_data: Output from CitationNetworkBuilder.to_dict()

        Returns:
            Combined figure or None
        """
        if not self._check_plotly():
            return None

        nodes = citation_network_data.get("nodes", [])
        edges = citation_network_data.get("edges", [])
        metrics = citation_network_data.get("metrics", {})

        # Create network graph
        graph_nodes = [
            {
                "id": n["id"],
                "label": n["title"][:30] + "..." if len(n.get("title", "")) > 30 else n.get("title", ""),
                "type": "paper",
                "citations_in": n.get("citations_in", 0),
            }
            for n in nodes
        ]
        graph_edges = [{"source": e["source"], "target": e["target"]} for e in edges]

        self.create_network_graph(
            graph_nodes,
            graph_edges,
            title="Citation Network",
            node_size_field="citations_in",
        )

        # Create top cited papers chart
        sorted_nodes = sorted(nodes, key=lambda x: x.get("citations_in", 0), reverse=True)
        top_cited = sorted_nodes[:10]
        if top_cited:
            chart_data = [
                {"title": n["title"][:40], "citations": n.get("citations_in", 0)}
                for n in top_cited
            ]
            self.create_bar_chart(
                chart_data,
                "title",
                "citations",
                title="Most Cited Papers",
                orientation="h",
            )

        # Create timeline if year data available
        papers_by_year = metrics.get("papers_by_year", {})
        if papers_by_year:
            self.create_timeline(papers_by_year, title="Papers by Year")

        return self.figures

    def build_theme_dashboard(self, theme_data: Dict[str, Any]) -> Optional[Any]:
        """
        Build a dashboard from theme analysis data.

        Args:
            theme_data: Output from ThemeAnalyzer.generate_insights()

        Returns:
            Combined figure or None
        """
        if not self._check_plotly():
            return None

        # Create top themes chart
        dominant_themes = theme_data.get("dominant_themes", [])[:20]
        if dominant_themes:
            chart_data = [
                {"term": t["term"], "frequency": t["frequency"]} for t in dominant_themes
            ]
            self.create_bar_chart(
                chart_data,
                "term",
                "frequency",
                title="Dominant Themes",
                orientation="h",
            )

        return self.figures

    def generate_html(self, output_path: Optional[Path] = None) -> str:
        """
        Generate a complete HTML dashboard.

        Args:
            output_path: Optional path to save HTML file

        Returns:
            HTML string
        """
        if PLOTLY_AVAILABLE and self.figures:
            return self._generate_plotly_html(output_path)
        else:
            return self._generate_fallback_html(output_path)

    def _generate_plotly_html(self, output_path: Optional[Path] = None) -> str:
        """Generate HTML using Plotly figures."""
        from plotly.io import to_html

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.title}</title>",
            '<meta charset="utf-8">',
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            "h1 { color: #2c3e50; text-align: center; }",
            ".chart-container { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            ".chart-title { color: #34495e; margin-bottom: 10px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{self.title}</h1>",
        ]

        for fig_data in self.figures:
            fig = fig_data.get("figure")
            title = fig_data.get("title", "Chart")
            if fig:
                fig_html = to_html(fig, include_plotlyjs="cdn", full_html=False)
                html_parts.append(f'<div class="chart-container">')
                html_parts.append(fig_html)
                html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])
        html_content = "\n".join(html_parts)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(html_content, encoding="utf-8")

        return html_content

    def _generate_fallback_html(self, output_path: Optional[Path] = None) -> str:
        """Generate basic HTML without Plotly."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.title}</title>",
            '<meta charset="utf-8">',
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #2c3e50; }",
            ".note { color: #7f8c8d; padding: 20px; background: #ecf0f1; border-radius: 4px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{self.title}</h1>",
            '<div class="note">',
            "<p>Interactive visualizations require Plotly. Install with:</p>",
            "<code>pip install plotly</code>",
            "</div>",
            "</body>",
            "</html>",
        ]

        html_content = "\n".join(html_parts)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(html_content, encoding="utf-8")

        return html_content

    def clear(self) -> None:
        """Clear all figures."""
        self.figures.clear()
