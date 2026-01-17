"""RIS exporter for citations."""

import json
from pathlib import Path
from typing import Dict, List, Optional


class RISExporter:
    """Export citations to RIS format for reference managers."""

    # RIS type codes
    TYPE_MAP = {
        "book": "BOOK",
        "article": "JOUR",
        "journal": "JOUR",
        "interview": "PCOMM",  # Personal communication
        "online": "ELEC",  # Electronic citation
        "archival": "UNPB",  # Unpublished work
        "unclassified": "GEN",  # Generic
    }

    # RIS tag definitions
    # TY - Type of reference (must be first)
    # AU - Author
    # TI - Title
    # PY - Publication year
    # PB - Publisher
    # CY - City (place of publication)
    # JO/JF - Journal name
    # VL - Volume
    # IS - Issue
    # SP - Start page
    # EP - End page
    # UR - URL
    # DO - DOI
    # N1 - Notes
    # ER - End of reference (must be last)

    def __init__(self):
        """Initialize the RIS exporter."""
        pass

    def export(self, citations: List[Dict]) -> str:
        """
        Convert citations to RIS entries.

        Args:
            citations: List of citation dictionaries.

        Returns:
            RIS formatted string with all entries.
        """
        entries = []

        for citation in citations:
            entry = self._format_entry(citation)
            if entry:
                entries.append(entry)

        return "\n".join(entries)

    def save(self, citations: List[Dict], output_path: Path) -> str:
        """
        Save citations to .ris file.

        Args:
            citations: List of citation dictionaries.
            output_path: Path to output .ris file.

        Returns:
            Path to the saved file as string.
        """
        output_path = Path(output_path)
        ris_content = self.export(citations)

        output_path.write_text(ris_content, encoding="utf-8")
        return str(output_path)

    def _format_entry(self, citation: Dict) -> Optional[str]:
        """Format a single citation as a RIS entry."""
        lines = []

        # Type must be first
        citation_type = citation.get("citation_type", "unclassified")
        ris_type = self.TYPE_MAP.get(citation_type, "GEN")
        lines.append(f"TY  - {ris_type}")

        # Authors (multiple AU lines for multiple authors)
        authors = citation.get("authors", [])
        if authors:
            if isinstance(authors, list):
                for author in authors:
                    formatted_author = self._format_author(author)
                    lines.append(f"AU  - {formatted_author}")
            else:
                formatted_author = self._format_author(str(authors))
                lines.append(f"AU  - {formatted_author}")

        # Title
        title = citation.get("title")
        if title:
            clean_title = title.strip().strip('"').strip("'")
            lines.append(f"TI  - {clean_title}")

        # Year
        year = citation.get("year")
        if year:
            lines.append(f"PY  - {str(year).strip()}")

        # Publisher
        publisher = citation.get("publisher")
        if publisher:
            lines.append(f"PB  - {publisher}")

        # Location/City
        location = citation.get("location")
        if location:
            lines.append(f"CY  - {location}")

        # Journal/Source (for articles)
        source = citation.get("source")
        if source:
            lines.append(f"JO  - {source}")

        # Volume
        volume = citation.get("volume")
        if volume:
            lines.append(f"VL  - {volume}")

        # Issue
        issue = citation.get("issue")
        if issue:
            lines.append(f"IS  - {issue}")

        # Pages
        pages = citation.get("pages")
        if pages:
            # Try to parse start and end pages
            sp, ep = self._parse_pages(pages)
            if sp:
                lines.append(f"SP  - {sp}")
            if ep:
                lines.append(f"EP  - {ep}")

        # URL
        url = citation.get("url")
        if url:
            lines.append(f"UR  - {url}")

        # DOI
        doi = citation.get("doi")
        if doi:
            lines.append(f"DO  - {doi}")

        # Notes
        notes = citation.get("notes")
        if notes:
            lines.append(f"N1  - {notes}")

        # Raw text as abstract/note if no other notes
        if not notes and citation.get("raw_text"):
            lines.append(f"N1  - {citation['raw_text']}")

        # End of reference (must be last)
        lines.append("ER  - ")

        return "\n".join(lines)

    def _format_author(self, author: str) -> str:
        """
        Format author name for RIS.

        RIS expects: Last, First Middle
        """
        author = author.strip()
        if not author:
            return "Unknown"

        # Already in "Last, First" format
        if "," in author:
            return author

        # Convert "First Last" to "Last, First"
        parts = author.split()
        if len(parts) >= 2:
            last_name = parts[-1]
            first_parts = " ".join(parts[:-1])
            return f"{last_name}, {first_parts}"

        return author

    def _parse_pages(self, pages: str) -> tuple:
        """
        Parse page range into start and end pages.

        Args:
            pages: Page string like "100-120" or "100"

        Returns:
            Tuple of (start_page, end_page) or (start_page, None)
        """
        pages = str(pages).strip()

        # Try to split on common delimiters
        for delimiter in ["-", "–", "—", "to"]:
            if delimiter in pages:
                parts = pages.split(delimiter)
                if len(parts) >= 2:
                    return (parts[0].strip(), parts[1].strip())

        # Single page
        return (pages, None)

    def load_citations(self, citations_path: Path) -> List[Dict]:
        """
        Load citations from a JSON file.

        Args:
            citations_path: Path to JSON file containing citations.

        Returns:
            List of citation dictionaries.
        """
        citations_path = Path(citations_path)
        with citations_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both list format and dict format with 'citations' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "citations" in data:
            return data["citations"]
        else:
            return []
