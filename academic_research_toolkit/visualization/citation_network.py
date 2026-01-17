"""Citation Network Builder for academic research.

Builds and analyzes citation networks showing how papers reference each other.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class PaperNode:
    """Represents a paper in the citation network."""

    id: str
    title: str
    authors: List[str] = field(default_factory=list)
    year: Optional[str] = None
    doi: Optional[str] = None
    citations_in: int = 0  # Number of times this paper is cited
    citations_out: int = 0  # Number of papers this paper cites
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationEdge:
    """Represents a citation relationship between papers."""

    source_id: str  # Citing paper
    target_id: str  # Cited paper
    context: Optional[str] = None  # Citation context/quote
    properties: Dict[str, Any] = field(default_factory=dict)


class CitationNetworkBuilder:
    """Builds citation networks from academic papers.

    Creates a directed graph where nodes are papers and edges
    represent citation relationships (citing -> cited).
    """

    def __init__(self):
        """Initialize the citation network builder."""
        self.nodes: Dict[str, PaperNode] = {}
        self.edges: List[CitationEdge] = []
        self._node_counter = 0

    def _generate_id(self) -> str:
        """Generate a unique node ID."""
        self._node_counter += 1
        return f"paper_{self._node_counter}"

    def _normalize_title(self, title: str) -> str:
        """Normalize a title for consistent identification."""
        return title.lower().strip()

    def _get_or_create_node(
        self,
        title: str,
        authors: Optional[List[str]] = None,
        year: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> PaperNode:
        """Get existing node or create a new one."""
        normalized_title = self._normalize_title(title)

        if normalized_title not in self.nodes:
            node = PaperNode(
                id=self._generate_id(),
                title=title,
                authors=authors or [],
                year=year,
                doi=doi,
            )
            self.nodes[normalized_title] = node

        return self.nodes[normalized_title]

    def add_paper(
        self,
        title: str,
        authors: Optional[List[str]] = None,
        year: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> PaperNode:
        """
        Add a paper to the network.

        Args:
            title: Paper title
            authors: List of author names
            year: Publication year
            doi: Digital Object Identifier

        Returns:
            The paper node
        """
        return self._get_or_create_node(title, authors, year, doi)

    def add_citation(
        self,
        citing_title: str,
        cited_title: str,
        cited_authors: Optional[List[str]] = None,
        cited_year: Optional[str] = None,
        context: Optional[str] = None,
    ) -> CitationEdge:
        """
        Add a citation relationship.

        Args:
            citing_title: Title of the paper that cites
            cited_title: Title of the cited paper
            cited_authors: Authors of the cited paper
            cited_year: Year of the cited paper
            context: Citation context or quote

        Returns:
            The citation edge
        """
        citing_node = self._get_or_create_node(citing_title)
        cited_node = self._get_or_create_node(
            cited_title, cited_authors, cited_year
        )

        # Update citation counts
        citing_node.citations_out += 1
        cited_node.citations_in += 1

        # Check for duplicate edges
        for edge in self.edges:
            if edge.source_id == citing_node.id and edge.target_id == cited_node.id:
                return edge

        edge = CitationEdge(
            source_id=citing_node.id,
            target_id=cited_node.id,
            context=context,
        )
        self.edges.append(edge)
        return edge

    def build_from_citations(
        self, source_paper: str, citations: List[Dict]
    ) -> "CitationNetworkBuilder":
        """
        Build network from a source paper and its citations.

        Args:
            source_paper: Title of the source paper
            citations: List of citation data from CitationExtractor

        Returns:
            Self for method chaining
        """
        source_node = self.add_paper(source_paper)

        for citation in citations:
            cited_title = citation.get("title") or citation.get("raw_text", "Unknown")
            cited_authors = citation.get("authors", [])
            cited_year = citation.get("year")

            if isinstance(cited_authors, str):
                cited_authors = [cited_authors]

            self.add_citation(
                citing_title=source_paper,
                cited_title=cited_title,
                cited_authors=cited_authors,
                cited_year=cited_year,
            )

        return self

    def build_from_multiple_papers(
        self, papers_citations: Dict[str, List[Dict]]
    ) -> "CitationNetworkBuilder":
        """
        Build network from multiple papers and their citations.

        Args:
            papers_citations: Dict mapping paper titles to their citation lists

        Returns:
            Self for method chaining
        """
        for paper_title, citations in papers_citations.items():
            self.build_from_citations(paper_title, citations)

        return self

    def get_most_cited(self, n: int = 10) -> List[PaperNode]:
        """
        Get the most cited papers in the network.

        Args:
            n: Number of papers to return

        Returns:
            List of most cited paper nodes
        """
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda x: x.citations_in,
            reverse=True,
        )
        return sorted_nodes[:n]

    def get_citing_papers(self, paper_title: str) -> List[PaperNode]:
        """
        Get all papers that cite a given paper.

        Args:
            paper_title: Title of the cited paper

        Returns:
            List of citing paper nodes
        """
        normalized = self._normalize_title(paper_title)
        if normalized not in self.nodes:
            return []

        target_node = self.nodes[normalized]
        citing = []

        for edge in self.edges:
            if edge.target_id == target_node.id:
                for node in self.nodes.values():
                    if node.id == edge.source_id:
                        citing.append(node)
                        break

        return citing

    def get_cited_papers(self, paper_title: str) -> List[PaperNode]:
        """
        Get all papers cited by a given paper.

        Args:
            paper_title: Title of the citing paper

        Returns:
            List of cited paper nodes
        """
        normalized = self._normalize_title(paper_title)
        if normalized not in self.nodes:
            return []

        source_node = self.nodes[normalized]
        cited = []

        for edge in self.edges:
            if edge.source_id == source_node.id:
                for node in self.nodes.values():
                    if node.id == edge.target_id:
                        cited.append(node)
                        break

        return cited

    def get_citation_chain(
        self, paper_title: str, depth: int = 2
    ) -> Dict[str, List[str]]:
        """
        Get the citation chain (papers that cite papers that cite...).

        Args:
            paper_title: Starting paper title
            depth: How many levels to traverse

        Returns:
            Dictionary mapping depth level to paper titles
        """
        normalized = self._normalize_title(paper_title)
        if normalized not in self.nodes:
            return {}

        chain: Dict[str, List[str]] = {f"level_0": [paper_title]}
        visited: Set[str] = {normalized}

        current_level = [self.nodes[normalized]]

        for level in range(1, depth + 1):
            next_level = []
            level_titles = []

            for node in current_level:
                # Get papers citing this one
                for edge in self.edges:
                    if edge.target_id == node.id:
                        for n in self.nodes.values():
                            if n.id == edge.source_id:
                                norm_title = self._normalize_title(n.title)
                                if norm_title not in visited:
                                    visited.add(norm_title)
                                    next_level.append(n)
                                    level_titles.append(n.title)
                                break

            if level_titles:
                chain[f"level_{level}"] = level_titles
            current_level = next_level

        return chain

    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate network metrics.

        Returns:
            Dictionary with network metrics
        """
        if not self.nodes:
            return {
                "node_count": 0,
                "edge_count": 0,
                "density": 0,
                "avg_citations_in": 0,
                "avg_citations_out": 0,
            }

        node_count = len(self.nodes)
        edge_count = len(self.edges)
        max_edges = node_count * (node_count - 1)
        density = edge_count / max_edges if max_edges > 0 else 0

        total_in = sum(n.citations_in for n in self.nodes.values())
        total_out = sum(n.citations_out for n in self.nodes.values())

        # Find papers by year
        papers_by_year: Dict[str, int] = defaultdict(int)
        for node in self.nodes.values():
            if node.year:
                papers_by_year[node.year] += 1

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": round(density, 4),
            "avg_citations_in": round(total_in / node_count, 2),
            "avg_citations_out": round(total_out / node_count, 2),
            "max_citations_in": max(n.citations_in for n in self.nodes.values()),
            "max_citations_out": max(n.citations_out for n in self.nodes.values()),
            "papers_by_year": dict(sorted(papers_by_year.items())),
        }

    def get_author_collaboration_network(self) -> Dict[str, Any]:
        """
        Extract author collaboration network from the citation network.

        Returns:
            Dictionary with collaboration network data
        """
        collaborations: Dict[str, Set[str]] = defaultdict(set)
        author_papers: Dict[str, int] = defaultdict(int)

        for node in self.nodes.values():
            if len(node.authors) > 1:
                # Add collaborations between co-authors
                for i, author1 in enumerate(node.authors):
                    author_papers[author1] += 1
                    for author2 in node.authors[i + 1 :]:
                        collaborations[author1].add(author2)
                        collaborations[author2].add(author1)
            elif node.authors:
                author_papers[node.authors[0]] += 1

        # Convert to serializable format
        collab_list = []
        seen = set()
        for author, coauthors in collaborations.items():
            for coauthor in coauthors:
                pair = tuple(sorted([author, coauthor]))
                if pair not in seen:
                    seen.add(pair)
                    collab_list.append({"author1": pair[0], "author2": pair[1]})

        return {
            "authors": [
                {"name": name, "papers": count}
                for name, count in sorted(
                    author_papers.items(), key=lambda x: x[1], reverse=True
                )
            ],
            "collaborations": collab_list,
            "total_authors": len(author_papers),
            "total_collaborations": len(collab_list),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the citation network to a dictionary format.

        Returns:
            Dictionary representation of the network
        """
        return {
            "nodes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "authors": n.authors,
                    "year": n.year,
                    "doi": n.doi,
                    "citations_in": n.citations_in,
                    "citations_out": n.citations_out,
                    "properties": n.properties,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "context": e.context,
                    "properties": e.properties,
                }
                for e in self.edges
            ],
            "metrics": self.calculate_metrics(),
        }

    def clear(self) -> None:
        """Clear all nodes and edges."""
        self.nodes.clear()
        self.edges.clear()
        self._node_counter = 0
