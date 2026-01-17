"""Tests for the visualization module."""

import json

import pytest

from academic_research_toolkit.visualization.knowledge_graph import (
    KnowledgeGraphBuilder,
)
from academic_research_toolkit.visualization.citation_network import (
    CitationNetworkBuilder,
    PaperNode,
)
from academic_research_toolkit.visualization.exporters import GraphExporter


@pytest.fixture
def sample_citations():
    """Sample citations for testing."""
    return [
        {
            "title": "Machine Learning Fundamentals",
            "authors": ["Smith, John", "Doe, Jane"],
            "year": "2020",
            "citation_type": "book",
        },
        {
            "title": "Deep Learning Applications",
            "authors": ["Johnson, Bob"],
            "year": "2021",
            "citation_type": "article",
        },
        {
            "title": "Neural Networks for NLP",
            "authors": ["Smith, John"],
            "year": "2019",
            "citation_type": "article",
        },
    ]


@pytest.fixture
def sample_theme_data():
    """Sample theme data for testing."""
    return {
        "dominant_themes": [
            {"term": "machine learning", "frequency": 50},
            {"term": "neural networks", "frequency": 35},
            {"term": "deep learning", "frequency": 28},
        ],
        "corpus_statistics": {
            "total_documents": 5,
            "unique_terms": 100,
            "total_terms": 500,
        },
    }


class TestKnowledgeGraphBuilder:
    """Tests for KnowledgeGraphBuilder."""

    def test_init(self):
        """Test builder initialization."""
        builder = KnowledgeGraphBuilder()
        assert len(builder.entities) == 0
        assert len(builder.relationships) == 0

    def test_add_paper(self):
        """Test adding a paper."""
        builder = KnowledgeGraphBuilder()
        paper = builder.add_paper(
            title="Test Paper",
            authors=["Smith, John"],
            year="2020",
        )

        assert paper.entity_type == "paper"
        assert paper.label == "Test Paper"
        assert len(builder.entities) >= 1  # Paper + author

    def test_add_paper_with_authors(self):
        """Test that authors are added as entities."""
        builder = KnowledgeGraphBuilder()
        builder.add_paper(
            title="Test Paper",
            authors=["Smith, John", "Doe, Jane"],
            year="2020",
        )

        # Should have paper + 2 authors
        entity_types = [e.entity_type for e in builder.entities.values()]
        assert entity_types.count("author") == 2
        assert entity_types.count("paper") == 1

    def test_add_citation(self):
        """Test adding a citation relationship."""
        builder = KnowledgeGraphBuilder()
        rel = builder.add_citation(
            citing_paper="Paper A",
            cited_paper="Paper B",
            cited_authors=["Smith"],
            cited_year="2020",
        )

        assert rel.relationship_type == "cites"

    def test_add_affiliation(self):
        """Test adding an affiliation."""
        builder = KnowledgeGraphBuilder()
        rel = builder.add_affiliation("Smith, John", "MIT")

        assert rel.relationship_type == "affiliated_with"
        entity_types = [e.entity_type for e in builder.entities.values()]
        assert "author" in entity_types
        assert "institution" in entity_types

    def test_extract_concepts(self):
        """Test concept extraction from text."""
        builder = KnowledgeGraphBuilder()
        text = "This paper discusses machine learning and neural networks."
        concepts = builder.extract_concepts(text)

        assert "machine learning" in concepts
        assert "neural network" in concepts or "neural networks" in concepts

    def test_build_from_citations(self, sample_citations):
        """Test building graph from citations."""
        builder = KnowledgeGraphBuilder()
        builder.build_from_citations(sample_citations)

        stats = builder.get_statistics()
        assert stats["total_entities"] > 0
        assert stats["entities_by_type"]["paper"] == 3

    def test_to_dict(self, sample_citations):
        """Test converting graph to dictionary."""
        builder = KnowledgeGraphBuilder()
        builder.build_from_citations(sample_citations)

        graph_dict = builder.to_dict()

        assert "entities" in graph_dict
        assert "relationships" in graph_dict
        assert "statistics" in graph_dict

    def test_get_neighbors(self):
        """Test getting neighboring entities."""
        builder = KnowledgeGraphBuilder()
        paper = builder.add_paper("Test", authors=["Smith"])

        neighbors = builder.get_neighbors(paper.id)
        assert len(neighbors) > 0  # Should have author neighbor

    def test_clear(self):
        """Test clearing the graph."""
        builder = KnowledgeGraphBuilder()
        builder.add_paper("Test", authors=["Smith"])

        assert len(builder.entities) > 0

        builder.clear()
        assert len(builder.entities) == 0
        assert len(builder.relationships) == 0

    def test_build_from_themes(self):
        """Test building knowledge graph from theme analysis data."""
        builder = KnowledgeGraphBuilder()
        theme_data = {
            "dominant_themes": [
                {"term": "machine learning", "frequency": 10},
                {"term": "deep learning", "frequency": 8},
            ],
            "cooccurrences": {
                "machine learning": {"deep learning": 5},
            },
        }

        builder.build_from_themes(theme_data)

        # Should have concept entities
        concept_count = sum(
            1 for e in builder.entities.values() if e.entity_type == "concept"
        )
        assert concept_count >= 2

    def test_build_from_themes_empty(self):
        """Test building from themes with empty/malformed data."""
        builder = KnowledgeGraphBuilder()

        # Empty data
        builder.build_from_themes({})
        assert len(builder.entities) == 0

        # Missing keys
        builder.build_from_themes({"dominant_themes": []})
        assert len(builder.entities) == 0

    def test_build_from_affiliations(self):
        """Test building knowledge graph from author affiliation data."""
        builder = KnowledgeGraphBuilder()
        authors = [
            {"name": "John Smith", "institution": "MIT"},
            {"name": "Jane Doe", "affiliation": "Stanford University"},
            {"name": "Bob Wilson"},  # No affiliation
        ]

        builder.build_from_affiliations(authors)

        # Should have author and institution entities
        author_count = sum(
            1 for e in builder.entities.values() if e.entity_type == "author"
        )
        institution_count = sum(
            1 for e in builder.entities.values() if e.entity_type == "institution"
        )

        assert author_count >= 2  # Two authors with affiliations
        assert institution_count >= 2  # MIT and Stanford


class TestCitationNetworkBuilder:
    """Tests for CitationNetworkBuilder."""

    def test_init(self):
        """Test builder initialization."""
        builder = CitationNetworkBuilder()
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0

    def test_add_paper(self):
        """Test adding a paper."""
        builder = CitationNetworkBuilder()
        node = builder.add_paper(
            title="Test Paper",
            authors=["Smith, John"],
            year="2020",
        )

        assert isinstance(node, PaperNode)
        assert node.title == "Test Paper"
        assert "Smith, John" in node.authors

    def test_add_citation(self):
        """Test adding a citation."""
        builder = CitationNetworkBuilder()
        builder.add_citation(
            citing_title="Paper A",
            cited_title="Paper B",
            cited_authors=["Smith"],
            cited_year="2020",
        )

        assert len(builder.edges) == 1
        # Cited paper should have citation_in incremented
        cited = builder.nodes[builder._normalize_title("Paper B")]
        assert cited.citations_in == 1

    def test_build_from_citations(self, sample_citations):
        """Test building network from citations."""
        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source Paper", sample_citations)

        assert len(builder.nodes) == 4  # Source + 3 cited
        assert len(builder.edges) == 3

    def test_get_most_cited(self, sample_citations):
        """Test getting most cited papers."""
        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source Paper", sample_citations)

        most_cited = builder.get_most_cited(5)
        assert len(most_cited) <= 5

    def test_calculate_metrics(self, sample_citations):
        """Test calculating network metrics."""
        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source Paper", sample_citations)

        metrics = builder.calculate_metrics()

        assert "node_count" in metrics
        assert "edge_count" in metrics
        assert "density" in metrics
        assert metrics["node_count"] == 4
        assert metrics["edge_count"] == 3

    def test_to_dict(self, sample_citations):
        """Test converting network to dictionary."""
        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source Paper", sample_citations)

        network_dict = builder.to_dict()

        assert "nodes" in network_dict
        assert "edges" in network_dict
        assert "metrics" in network_dict

    def test_get_citing_papers(self):
        """Test getting papers that cite a given paper."""
        builder = CitationNetworkBuilder()
        builder.add_citation("Paper A", "Paper B")
        builder.add_citation("Paper C", "Paper B")

        citing = builder.get_citing_papers("Paper B")
        assert len(citing) == 2

    def test_get_cited_papers(self):
        """Test getting papers cited by a given paper."""
        builder = CitationNetworkBuilder()
        builder.add_citation("Paper A", "Paper B")
        builder.add_citation("Paper A", "Paper C")

        cited = builder.get_cited_papers("Paper A")
        assert len(cited) == 2

    def test_author_collaboration_network(self):
        """Test extracting author collaboration network."""
        builder = CitationNetworkBuilder()
        builder.add_paper("Paper 1", authors=["Smith", "Jones"])
        builder.add_paper("Paper 2", authors=["Smith", "Brown"])

        collab = builder.get_author_collaboration_network()

        assert collab["total_authors"] == 3
        assert collab["total_collaborations"] >= 1

    def test_build_from_multiple_papers(self, sample_citations):
        """Test building network from multiple papers and their citations."""
        builder = CitationNetworkBuilder()
        papers_citations = {
            "Paper A": sample_citations[:2],
            "Paper B": sample_citations[1:],
        }

        builder.build_from_multiple_papers(papers_citations)

        # Should have multiple source papers and cited papers
        assert len(builder.nodes) > 2
        assert len(builder.edges) > 0

    def test_get_citation_chain(self):
        """Test getting citation chain traversal."""
        builder = CitationNetworkBuilder()
        # Create a chain: A cites B, B cites C
        builder.add_citation("Paper A", "Paper B")
        builder.add_citation("Paper B", "Paper C")
        builder.add_citation("Paper D", "Paper B")  # Another paper cites B

        chain = builder.get_citation_chain("Paper B", depth=2)

        # Should have the starting paper at level 0
        assert "level_0" in chain
        assert "Paper B" in chain["level_0"]

    def test_get_citation_chain_empty(self):
        """Test citation chain for non-existent paper."""
        builder = CitationNetworkBuilder()
        builder.add_citation("Paper A", "Paper B")

        chain = builder.get_citation_chain("Non-existent Paper")
        assert chain == {}


class TestGraphExporter:
    """Tests for GraphExporter."""

    @pytest.fixture
    def sample_nodes(self):
        return [
            {"id": "1", "label": "Node 1", "type": "paper"},
            {"id": "2", "label": "Node 2", "type": "author"},
            {"id": "3", "label": "Node 3", "type": "concept"},
        ]

    @pytest.fixture
    def sample_edges(self):
        return [
            {"source": "1", "target": "2", "type": "authored_by"},
            {"source": "1", "target": "3", "type": "discusses"},
        ]

    def test_export_json(self, sample_nodes, sample_edges, tmp_path):
        """Test JSON export."""
        exporter = GraphExporter()
        output = tmp_path / "test.json"

        result = exporter.export_json(sample_nodes, sample_edges, output)

        assert output.exists()
        data = json.loads(result)
        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) == 3
        assert len(data["links"]) == 2

    def test_export_graphml(self, sample_nodes, sample_edges, tmp_path):
        """Test GraphML export."""
        exporter = GraphExporter()
        output = tmp_path / "test.graphml"

        result = exporter.export_graphml(sample_nodes, sample_edges, output)

        assert output.exists()
        assert "<graphml" in result
        assert "<node" in result
        assert "<edge" in result

    def test_export_gexf(self, sample_nodes, sample_edges, tmp_path):
        """Test GEXF export."""
        exporter = GraphExporter()
        output = tmp_path / "test.gexf"

        result = exporter.export_gexf(sample_nodes, sample_edges, output)

        assert output.exists()
        assert "<gexf" in result
        assert "<node" in result
        assert "<edge" in result

    def test_export_dot(self, sample_nodes, sample_edges, tmp_path):
        """Test DOT export."""
        exporter = GraphExporter()
        output = tmp_path / "test.dot"

        result = exporter.export_dot(sample_nodes, sample_edges, output)

        assert output.exists()
        assert "digraph" in result
        assert "->" in result

    def test_export_cytoscape(self, sample_nodes, sample_edges, tmp_path):
        """Test Cytoscape JSON export."""
        exporter = GraphExporter()
        output = tmp_path / "test_cytoscape.json"

        result = exporter.export_cytoscape_json(sample_nodes, sample_edges, output)

        assert output.exists()
        data = json.loads(result)
        assert "nodes" in data
        assert "edges" in data

    def test_export_from_knowledge_graph(self, sample_citations, tmp_path):
        """Test exporting from knowledge graph data."""
        from academic_research_toolkit.visualization.knowledge_graph import (
            KnowledgeGraphBuilder,
        )

        builder = KnowledgeGraphBuilder()
        builder.build_from_citations(sample_citations)
        graph_data = builder.to_dict()

        exporter = GraphExporter()
        output = tmp_path / "kg.json"

        result = exporter.export_from_knowledge_graph(graph_data, "json", output)

        assert output.exists()
        data = json.loads(result)
        assert "nodes" in data

    def test_export_from_citation_network(self, sample_citations, tmp_path):
        """Test exporting from citation network data."""
        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source", sample_citations)
        network_data = builder.to_dict()

        exporter = GraphExporter()
        output = tmp_path / "cn.json"

        result = exporter.export_from_citation_network(network_data, "json", output)

        assert output.exists()
        data = json.loads(result)
        assert "nodes" in data

    def test_invalid_format(self, sample_nodes, sample_edges):
        """Test that invalid format raises error."""
        exporter = GraphExporter()

        with pytest.raises(ValueError):
            exporter._export_by_format(sample_nodes, sample_edges, "invalid")


class TestDashboardGenerator:
    """Tests for DashboardGenerator."""

    def test_init(self):
        """Test generator initialization."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator

        gen = DashboardGenerator(title="Test Dashboard")
        assert gen.title == "Test Dashboard"
        assert len(gen.figures) == 0

    def test_generate_fallback_html(self):
        """Test fallback HTML generation when Plotly not available."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator

        gen = DashboardGenerator(title="Test")
        html = gen._generate_fallback_html()

        assert "<!DOCTYPE html>" in html
        assert "Test" in html

    def test_clear(self):
        """Test clearing figures."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator

        gen = DashboardGenerator()
        gen.figures.append({"test": "data"})

        gen.clear()
        assert len(gen.figures) == 0


# Conditional tests that require Plotly
class TestDashboardWithPlotly:
    """Tests for DashboardGenerator that require Plotly."""

    @pytest.fixture
    def check_plotly(self):
        """Skip if Plotly not available."""
        try:
            import plotly
            return True
        except ImportError:
            pytest.skip("Plotly not installed")

    def test_create_bar_chart(self, check_plotly):
        """Test bar chart creation."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator

        gen = DashboardGenerator()
        data = [{"name": "A", "value": 10}, {"name": "B", "value": 20}]

        fig = gen.create_bar_chart(data, "name", "value", "Test Chart")

        assert fig is not None
        assert len(gen.figures) == 1

    def test_create_pie_chart(self, check_plotly):
        """Test pie chart creation."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator

        gen = DashboardGenerator()
        data = {"A": 30, "B": 50, "C": 20}

        fig = gen.create_pie_chart(data, "Distribution")

        assert fig is not None

    def test_create_timeline(self, check_plotly):
        """Test timeline creation."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator

        gen = DashboardGenerator()
        data = {"2018": 5, "2019": 10, "2020": 15}

        fig = gen.create_timeline(data, "Papers by Year")

        assert fig is not None

    def test_build_citation_dashboard(self, check_plotly, sample_citations):
        """Test building citation network dashboard."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator
        from academic_research_toolkit.visualization.citation_network import (
            CitationNetworkBuilder,
        )

        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source", sample_citations)
        network_data = builder.to_dict()

        gen = DashboardGenerator(title="Citation Dashboard")
        gen.build_citation_network_dashboard(network_data)

        assert len(gen.figures) > 0

    def test_generate_html(self, check_plotly, sample_citations, tmp_path):
        """Test HTML generation with Plotly."""
        from academic_research_toolkit.visualization.dashboard import DashboardGenerator
        from academic_research_toolkit.visualization.citation_network import (
            CitationNetworkBuilder,
        )

        builder = CitationNetworkBuilder()
        builder.build_from_citations("Source", sample_citations)
        network_data = builder.to_dict()

        gen = DashboardGenerator()
        gen.build_citation_network_dashboard(network_data)

        output = tmp_path / "dashboard.html"
        html = gen.generate_html(output)

        assert output.exists()
        assert "<!DOCTYPE html>" in html
