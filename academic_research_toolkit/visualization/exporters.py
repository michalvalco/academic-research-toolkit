"""Graph exporters for various formats.

Exports knowledge graphs and citation networks to GraphML, JSON, and other formats.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.dom import minidom


class GraphExporter:
    """Exports graph data to various formats.

    Supports GraphML, JSON, GEXF, and DOT formats for graph visualization
    tools like Gephi, Cytoscape, and GraphViz.
    """

    def export_graphml(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export graph to GraphML format.

        GraphML is widely supported by tools like Gephi, Cytoscape, yEd.

        Args:
            nodes: List of node dictionaries with 'id', 'label', optionally 'type'
            edges: List of edge dictionaries with 'source', 'target'
            output_path: Optional path to save the file

        Returns:
            GraphML XML string
        """
        # Create root element
        graphml = ET.Element("graphml")
        graphml.set("xmlns", "http://graphml.graphdrawing.org/xmlns")
        graphml.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        graphml.set(
            "xsi:schemaLocation",
            "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd",
        )

        # Define node attributes
        key_label = ET.SubElement(graphml, "key")
        key_label.set("id", "label")
        key_label.set("for", "node")
        key_label.set("attr.name", "label")
        key_label.set("attr.type", "string")

        key_type = ET.SubElement(graphml, "key")
        key_type.set("id", "type")
        key_type.set("for", "node")
        key_type.set("attr.name", "type")
        key_type.set("attr.type", "string")

        # Define edge attributes
        key_weight = ET.SubElement(graphml, "key")
        key_weight.set("id", "weight")
        key_weight.set("for", "edge")
        key_weight.set("attr.name", "weight")
        key_weight.set("attr.type", "double")
        default = ET.SubElement(key_weight, "default")
        default.text = "1.0"

        key_rel_type = ET.SubElement(graphml, "key")
        key_rel_type.set("id", "relationship_type")
        key_rel_type.set("for", "edge")
        key_rel_type.set("attr.name", "relationship_type")
        key_rel_type.set("attr.type", "string")

        # Create graph element
        graph = ET.SubElement(graphml, "graph")
        graph.set("id", "G")
        graph.set("edgedefault", "directed")

        # Add nodes
        for node in nodes:
            node_elem = ET.SubElement(graph, "node")
            node_elem.set("id", str(node.get("id", "")))

            label_data = ET.SubElement(node_elem, "data")
            label_data.set("key", "label")
            label_data.text = str(node.get("label", node.get("id", "")))

            if "type" in node:
                type_data = ET.SubElement(node_elem, "data")
                type_data.set("key", "type")
                type_data.text = str(node["type"])

        # Add edges
        for i, edge in enumerate(edges):
            edge_elem = ET.SubElement(graph, "edge")
            edge_elem.set("id", f"e{i}")
            edge_elem.set("source", str(edge.get("source", "")))
            edge_elem.set("target", str(edge.get("target", "")))

            if "weight" in edge:
                weight_data = ET.SubElement(edge_elem, "data")
                weight_data.set("key", "weight")
                weight_data.text = str(edge["weight"])

            if "type" in edge:
                type_data = ET.SubElement(edge_elem, "data")
                type_data.set("key", "relationship_type")
                type_data.text = str(edge["type"])

        # Pretty print
        xml_string = ET.tostring(graphml, encoding="unicode")
        try:
            parsed = minidom.parseString(xml_string)
            xml_string = parsed.toprettyxml(indent="  ")
        except Exception:
            # Pretty-printing is optional; if it fails, use the unformatted XML
            pass

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(xml_string, encoding="utf-8")

        return xml_string

    def export_json(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        output_path: Optional[Path] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Export graph to JSON format.

        Uses a format compatible with D3.js and similar visualization libraries.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            output_path: Optional path to save the file
            metadata: Optional metadata to include

        Returns:
            JSON string
        """
        graph_data = {
            "nodes": nodes,
            "links": [
                {
                    "source": e.get("source"),
                    "target": e.get("target"),
                    "type": e.get("type"),
                    "weight": e.get("weight", 1.0),
                }
                for e in edges
            ],
        }

        if metadata:
            graph_data["metadata"] = metadata

        json_string = json.dumps(graph_data, indent=2, ensure_ascii=False)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(json_string, encoding="utf-8")

        return json_string

    def export_gexf(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export graph to GEXF format.

        GEXF (Graph Exchange XML Format) is the native format for Gephi.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            output_path: Optional path to save the file

        Returns:
            GEXF XML string
        """
        # Create root element
        gexf = ET.Element("gexf")
        gexf.set("xmlns", "http://www.gexf.net/1.2draft")
        gexf.set("version", "1.2")

        # Create graph element
        graph = ET.SubElement(gexf, "graph")
        graph.set("defaultedgetype", "directed")

        # Define node attributes
        attributes = ET.SubElement(graph, "attributes")
        attributes.set("class", "node")
        attr_label = ET.SubElement(attributes, "attribute")
        attr_label.set("id", "0")
        attr_label.set("title", "type")
        attr_label.set("type", "string")

        # Add nodes
        nodes_elem = ET.SubElement(graph, "nodes")
        for node in nodes:
            node_elem = ET.SubElement(nodes_elem, "node")
            node_elem.set("id", str(node.get("id", "")))
            node_elem.set("label", str(node.get("label", node.get("id", ""))))

            if "type" in node:
                attvalues = ET.SubElement(node_elem, "attvalues")
                attvalue = ET.SubElement(attvalues, "attvalue")
                attvalue.set("for", "0")
                attvalue.set("value", str(node["type"]))

        # Add edges
        edges_elem = ET.SubElement(graph, "edges")
        for i, edge in enumerate(edges):
            edge_elem = ET.SubElement(edges_elem, "edge")
            edge_elem.set("id", str(i))
            edge_elem.set("source", str(edge.get("source", "")))
            edge_elem.set("target", str(edge.get("target", "")))
            if "weight" in edge:
                edge_elem.set("weight", str(edge["weight"]))

        # Pretty print
        xml_string = ET.tostring(gexf, encoding="unicode")
        try:
            parsed = minidom.parseString(xml_string)
            xml_string = parsed.toprettyxml(indent="  ")
        except Exception:
            # Pretty-printing is optional; if it fails, use the unformatted XML
            pass

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(xml_string, encoding="utf-8")

        return xml_string

    def export_dot(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        output_path: Optional[Path] = None,
        graph_name: str = "G",
    ) -> str:
        """
        Export graph to DOT format.

        DOT format is used by GraphViz for graph visualization.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            output_path: Optional path to save the file
            graph_name: Name for the graph

        Returns:
            DOT format string
        """
        lines = [f"digraph {graph_name} {{"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        lines.append("")

        # Node type colors
        type_colors = {
            "paper": "lightblue",
            "author": "lightgreen",
            "concept": "lightyellow",
            "institution": "lavender",
        }

        # Add nodes
        for node in nodes:
            node_id = str(node.get("id", "")).replace('"', '\\"')
            label = str(node.get("label", node_id)).replace('"', '\\"')
            node_type = node.get("type", "default")
            color = type_colors.get(node_type, "white")

            lines.append(f'  "{node_id}" [label="{label}" fillcolor="{color}" style=filled];')

        lines.append("")

        # Add edges
        for edge in edges:
            source = str(edge.get("source", "")).replace('"', '\\"')
            target = str(edge.get("target", "")).replace('"', '\\"')
            edge_type = edge.get("type", "")

            if edge_type:
                lines.append(f'  "{source}" -> "{target}" [label="{edge_type}"];')
            else:
                lines.append(f'  "{source}" -> "{target}";')

        lines.append("}")

        dot_string = "\n".join(lines)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(dot_string, encoding="utf-8")

        return dot_string

    def export_cytoscape_json(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export graph to Cytoscape.js JSON format.

        This format is used by Cytoscape.js for web-based graph visualization.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
            output_path: Optional path to save the file

        Returns:
            JSON string in Cytoscape.js format
        """
        elements = {"nodes": [], "edges": []}

        for node in nodes:
            elements["nodes"].append(
                {
                    "data": {
                        "id": str(node.get("id", "")),
                        "label": str(node.get("label", node.get("id", ""))),
                        "type": node.get("type", "default"),
                    }
                }
            )

        for i, edge in enumerate(edges):
            elements["edges"].append(
                {
                    "data": {
                        "id": f"e{i}",
                        "source": str(edge.get("source", "")),
                        "target": str(edge.get("target", "")),
                        "type": edge.get("type", ""),
                        "weight": edge.get("weight", 1.0),
                    }
                }
            )

        json_string = json.dumps(elements, indent=2, ensure_ascii=False)

        if output_path:
            output_path = Path(output_path)
            output_path.write_text(json_string, encoding="utf-8")

        return json_string

    def export_from_knowledge_graph(
        self,
        knowledge_graph_data: Dict[str, Any],
        format: str,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export a knowledge graph to the specified format.

        Args:
            knowledge_graph_data: Output from KnowledgeGraphBuilder.to_dict()
            format: Export format ('graphml', 'json', 'gexf', 'dot', 'cytoscape')
            output_path: Optional path to save the file

        Returns:
            Exported string in the specified format
        """
        entities = knowledge_graph_data.get("entities", [])
        relationships = knowledge_graph_data.get("relationships", [])

        nodes = [
            {"id": e["id"], "label": e["label"], "type": e["type"]} for e in entities
        ]
        edges = [
            {
                "source": r["source"],
                "target": r["target"],
                "type": r["type"],
                "weight": r.get("weight", 1.0),
            }
            for r in relationships
        ]

        return self._export_by_format(nodes, edges, format, output_path)

    def export_from_citation_network(
        self,
        citation_network_data: Dict[str, Any],
        format: str,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Export a citation network to the specified format.

        Args:
            citation_network_data: Output from CitationNetworkBuilder.to_dict()
            format: Export format ('graphml', 'json', 'gexf', 'dot', 'cytoscape')
            output_path: Optional path to save the file

        Returns:
            Exported string in the specified format
        """
        network_nodes = citation_network_data.get("nodes", [])
        network_edges = citation_network_data.get("edges", [])

        nodes = [
            {
                "id": n["id"],
                "label": n["title"],
                "type": "paper",
                "year": n.get("year"),
                "citations_in": n.get("citations_in", 0),
            }
            for n in network_nodes
        ]
        edges = [
            {"source": e["source"], "target": e["target"], "type": "cites"}
            for e in network_edges
        ]

        return self._export_by_format(nodes, edges, format, output_path)

    def _export_by_format(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        format: str,
        output_path: Optional[Path] = None,
    ) -> str:
        """Export to the specified format."""
        format = format.lower()

        if format == "graphml":
            return self.export_graphml(nodes, edges, output_path)
        elif format == "json":
            return self.export_json(nodes, edges, output_path)
        elif format == "gexf":
            return self.export_gexf(nodes, edges, output_path)
        elif format == "dot":
            return self.export_dot(nodes, edges, output_path)
        elif format == "cytoscape":
            return self.export_cytoscape_json(nodes, edges, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
