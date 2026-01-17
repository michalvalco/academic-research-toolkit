"""Knowledge Graph Builder for academic research.

Extracts entities and relationships from academic papers to build
a knowledge graph representing concepts, authors, and their connections.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""

    id: str
    label: str
    entity_type: str  # 'concept', 'author', 'institution', 'paper'
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    source_id: str
    target_id: str
    relationship_type: str  # 'cites', 'authored_by', 'affiliated_with', 'related_to'
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphBuilder:
    """Builds knowledge graphs from academic research data.

    Extracts entities (concepts, authors, institutions, papers) and
    their relationships to create a navigable knowledge structure.
    """

    # Common academic concepts to look for
    CONCEPT_PATTERNS = [
        r"\b(machine learning|deep learning|neural networks?|artificial intelligence)\b",
        r"\b(natural language processing|computer vision|reinforcement learning)\b",
        r"\b(data mining|big data|data science|analytics)\b",
        r"\b(algorithms?|models?|frameworks?|architectures?|systems?)\b",
        r"\b(classification|regression|clustering|prediction)\b",
        r"\b(optimization|training|inference|evaluation)\b",
    ]

    def __init__(self):
        """Initialize the knowledge graph builder."""
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self._entity_counter = 0
        self._concept_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.CONCEPT_PATTERNS
        ]

    def _generate_id(self, prefix: str = "entity") -> str:
        """Generate a unique entity ID."""
        self._entity_counter += 1
        return f"{prefix}_{self._entity_counter}"

    def _normalize_concept(self, concept: str) -> str:
        """Normalize a concept string for consistent identification."""
        return concept.lower().strip()

    def _get_or_create_entity(
        self, label: str, entity_type: str, properties: Optional[Dict] = None
    ) -> Entity:
        """Get existing entity or create a new one."""
        normalized_label = self._normalize_concept(label)
        entity_key = f"{entity_type}:{normalized_label}"

        if entity_key not in self.entities:
            entity = Entity(
                id=self._generate_id(entity_type),
                label=label,
                entity_type=entity_type,
                properties=properties or {},
            )
            self.entities[entity_key] = entity

        return self.entities[entity_key]

    def add_paper(
        self,
        title: str,
        authors: Optional[List[str]] = None,
        year: Optional[str] = None,
        doi: Optional[str] = None,
        abstract: Optional[str] = None,
    ) -> Entity:
        """
        Add a paper to the knowledge graph.

        Args:
            title: Paper title
            authors: List of author names
            year: Publication year
            doi: Digital Object Identifier
            abstract: Paper abstract

        Returns:
            The paper entity
        """
        properties = {"year": year, "doi": doi}
        paper_entity = self._get_or_create_entity(title, "paper", properties)

        # Add authors and author relationships
        if authors:
            for author in authors:
                author_entity = self._get_or_create_entity(author, "author")
                self._add_relationship(
                    paper_entity.id, author_entity.id, "authored_by"
                )

        # Extract concepts from title and abstract
        text = title
        if abstract:
            text += " " + abstract

        concepts = self.extract_concepts(text)
        for concept in concepts:
            concept_entity = self._get_or_create_entity(concept, "concept")
            self._add_relationship(paper_entity.id, concept_entity.id, "discusses")

        return paper_entity

    def add_citation(
        self,
        citing_paper: str,
        cited_paper: str,
        cited_authors: Optional[List[str]] = None,
        cited_year: Optional[str] = None,
    ) -> Relationship:
        """
        Add a citation relationship between papers.

        Args:
            citing_paper: Title of the paper that cites
            cited_paper: Title of the cited paper
            cited_authors: Authors of the cited paper
            cited_year: Year of the cited paper

        Returns:
            The citation relationship
        """
        citing_entity = self._get_or_create_entity(citing_paper, "paper")
        cited_entity = self._get_or_create_entity(
            cited_paper, "paper", {"year": cited_year}
        )

        # Add cited authors
        if cited_authors:
            for author in cited_authors:
                author_entity = self._get_or_create_entity(author, "author")
                self._add_relationship(
                    cited_entity.id, author_entity.id, "authored_by"
                )

        return self._add_relationship(citing_entity.id, cited_entity.id, "cites")

    def add_affiliation(self, author: str, institution: str) -> Relationship:
        """
        Add an affiliation relationship between author and institution.

        Args:
            author: Author name
            institution: Institution name

        Returns:
            The affiliation relationship
        """
        author_entity = self._get_or_create_entity(author, "author")
        institution_entity = self._get_or_create_entity(institution, "institution")

        return self._add_relationship(
            author_entity.id, institution_entity.id, "affiliated_with"
        )

    def extract_concepts(self, text: str) -> List[str]:
        """
        Extract academic concepts from text.

        Args:
            text: Text to extract concepts from

        Returns:
            List of extracted concept strings
        """
        concepts = set()

        for pattern in self._concept_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                concepts.add(match.lower())

        return list(concepts)

    def add_concept_relationship(
        self, concept1: str, concept2: str, weight: float = 1.0
    ) -> Relationship:
        """
        Add a relationship between two concepts.

        Args:
            concept1: First concept
            concept2: Second concept
            weight: Relationship weight (co-occurrence strength)

        Returns:
            The concept relationship
        """
        entity1 = self._get_or_create_entity(concept1, "concept")
        entity2 = self._get_or_create_entity(concept2, "concept")

        return self._add_relationship(
            entity1.id, entity2.id, "related_to", weight=weight
        )

    def _add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        weight: float = 1.0,
        properties: Optional[Dict] = None,
    ) -> Relationship:
        """Add a relationship to the graph."""
        # Check for existing relationship
        for rel in self.relationships:
            if (
                rel.source_id == source_id
                and rel.target_id == target_id
                and rel.relationship_type == relationship_type
            ):
                # Update weight for duplicate relationships
                rel.weight += weight
                return rel

        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            weight=weight,
            properties=properties or {},
        )
        self.relationships.append(relationship)
        return relationship

    def build_from_citations(self, citations: List[Dict]) -> "KnowledgeGraphBuilder":
        """
        Build knowledge graph from a list of citation dictionaries.

        Args:
            citations: List of citation data from CitationExtractor

        Returns:
            Self for method chaining
        """
        for citation in citations:
            title = citation.get("title") or citation.get("raw_text", "Unknown")
            authors = citation.get("authors", [])
            year = citation.get("year")

            self.add_paper(
                title=title,
                authors=authors if isinstance(authors, list) else [authors],
                year=year,
            )

        return self

    def build_from_themes(self, theme_data: Dict) -> "KnowledgeGraphBuilder":
        """
        Build knowledge graph from theme analysis data.

        Args:
            theme_data: Theme analysis results from ThemeAnalyzer

        Returns:
            Self for method chaining
        """
        # Add dominant themes as concepts
        for theme in theme_data.get("dominant_themes", []):
            term = theme.get("term", "")
            if term:
                self._get_or_create_entity(
                    term, "concept", {"frequency": theme.get("frequency", 0)}
                )

        # Add cooccurrence relationships
        cooccurrences = theme_data.get("cooccurrences", {})
        for concept1, related in cooccurrences.items():
            if isinstance(related, dict):
                for concept2, weight in related.items():
                    if concept1 != concept2:
                        self.add_concept_relationship(concept1, concept2, weight)

        return self

    def build_from_affiliations(self, authors: List[Dict]) -> "KnowledgeGraphBuilder":
        """
        Build knowledge graph from author affiliation data.

        Args:
            authors: List of author data from AffiliationExtractor

        Returns:
            Self for method chaining
        """
        for author_data in authors:
            author_name = author_data.get("name", "Unknown")
            institution = author_data.get("institution") or author_data.get(
                "affiliation"
            )

            if institution:
                self.add_affiliation(author_name, institution)

        return self

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.

        Returns:
            Dictionary with graph statistics
        """
        entity_counts = defaultdict(int)
        for entity in self.entities.values():
            entity_counts[entity.entity_type] += 1

        relationship_counts = defaultdict(int)
        for rel in self.relationships:
            relationship_counts[rel.relationship_type] += 1

        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entities_by_type": dict(entity_counts),
            "relationships_by_type": dict(relationship_counts),
        }

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by its ID."""
        for entity in self.entities.values():
            if entity.id == entity_id:
                return entity
        return None

    def get_neighbors(self, entity_id: str) -> List[Tuple[Entity, Relationship]]:
        """
        Get all neighboring entities and their relationships.

        Args:
            entity_id: The entity to find neighbors for

        Returns:
            List of (entity, relationship) tuples
        """
        neighbors = []

        for rel in self.relationships:
            if rel.source_id == entity_id:
                target = self.get_entity_by_id(rel.target_id)
                if target:
                    neighbors.append((target, rel))
            elif rel.target_id == entity_id:
                source = self.get_entity_by_id(rel.source_id)
                if source:
                    neighbors.append((source, rel))

        return neighbors

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the knowledge graph to a dictionary format.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "entities": [
                {
                    "id": e.id,
                    "label": e.label,
                    "type": e.entity_type,
                    "properties": e.properties,
                }
                for e in self.entities.values()
            ],
            "relationships": [
                {
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.relationship_type,
                    "weight": r.weight,
                    "properties": r.properties,
                }
                for r in self.relationships
            ],
            "statistics": self.get_statistics(),
        }

    def clear(self) -> None:
        """Clear all entities and relationships."""
        self.entities.clear()
        self.relationships.clear()
        self._entity_counter = 0
