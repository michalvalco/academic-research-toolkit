"""
Bibliography Generator for Academic Research

Generates formatted bibliographies from extracted citation data.
Supports APA, MLA, and Chicago citation formats.
"""

import json
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from academic_research_toolkit.utils.exceptions import InvalidInputError
from academic_research_toolkit.utils.validation import validate_citation_format


class BibliographyGenerator:
    """Generate formatted bibliographies from citation data."""

    SUPPORTED_FORMATS = ["apa", "mla", "chicago"]

    def __init__(self, format_style: str = "apa"):
        """
        Initialize bibliography generator.

        Args:
            format_style: Citation format ('apa', 'mla', 'chicago')

        Raises:
            InvalidInputError: If format is not supported
        """
        self.format_style = validate_citation_format(format_style)

    def generate_from_file(self, citations_file: Path) -> str:
        """
        Generate bibliography from a citations JSON file.

        Args:
            citations_file: Path to citations JSON file

        Returns:
            Formatted bibliography as string
        """
        citations_file = Path(citations_file)

        with open(citations_file, "r", encoding="utf-8") as f:
            citations = json.load(f)

        if not citations:
            return ""

        return self.generate_bibliography(citations)

    def generate_bibliography(self, citations: List[Dict]) -> str:
        """
        Generate formatted bibliography from citation dictionaries.

        Args:
            citations: List of citation dictionaries

        Returns:
            Formatted bibliography as string
        """
        sorted_citations = self._sort_citations(citations)

        formatted_entries = []
        for citation in sorted_citations:
            entry = self._format_citation(citation)
            if entry:
                formatted_entries.append(entry)

        if self.format_style == "chicago":
            numbered_entries = [
                f"{i+1}. {entry}"
                for i, entry in enumerate(formatted_entries)
            ]
            bibliography = "\n\n".join(numbered_entries)
        else:
            bibliography = "\n\n".join(formatted_entries)

        return bibliography

    def _sort_citations(self, citations: List[Dict]) -> List[Dict]:
        """Sort citations alphabetically by author last name."""
        def get_sort_key(citation: Dict) -> str:
            authors = citation.get("authors", [])

            if not authors:
                title = citation.get("title", citation.get("raw_text", ""))
                return self._normalize_for_sorting(title)

            first_author = authors[0]
            last_name = self._extract_last_name(first_author)

            return self._normalize_for_sorting(last_name)

        return sorted(citations, key=get_sort_key)

    def _extract_last_name(self, author: str) -> str:
        """Extract last name from author string."""
        author = author.strip()

        if "," in author:
            parts = author.split(",")
            return parts[0].strip()

        parts = author.split()
        if parts:
            return parts[-1]

        return author

    def _normalize_for_sorting(self, text: str) -> str:
        """Normalize text for alphabetical sorting."""
        text = text.strip()
        for article in ["The ", "A ", "An ", "Der ", "Die ", "Das ", "Le ", "La ", "Les "]:
            if text.startswith(article):
                text = text[len(article):]
                break

        normalized = unicodedata.normalize("NFD", text)
        return normalized.lower()

    def _format_citation(self, citation: Dict) -> Optional[str]:
        """Format a single citation according to the selected style."""
        citation_type = citation.get("citation_type", "unclassified")

        if self.format_style == "apa":
            return self._format_apa(citation, citation_type)
        elif self.format_style == "mla":
            return self._format_mla(citation, citation_type)
        else:
            return self._format_chicago(citation, citation_type)

    def _format_apa(self, citation: Dict, ctype: str) -> Optional[str]:
        """Format citation in APA style."""
        if ctype == "book":
            return self._format_apa_book(citation)
        elif ctype == "article":
            return self._format_apa_article(citation)
        elif ctype == "online":
            return self._format_apa_online(citation)
        elif ctype == "interview":
            return self._format_apa_interview(citation)
        else:
            return citation.get("raw_text", "")

    def _format_apa_book(self, citation: Dict) -> str:
        """Format book citation in APA style."""
        parts = []

        authors = citation.get("authors", [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)

        year = citation.get("year")
        if year:
            parts.append(f"({year}).")

        title = citation.get("title")
        if title:
            parts.append(f"{title}.")

        publisher = citation.get("publisher")
        location = citation.get("location")

        if location and publisher:
            parts.append(f"{location}: {publisher}.")
        elif publisher:
            parts.append(f"{publisher}.")

        return " ".join(parts)

    def _format_apa_article(self, citation: Dict) -> str:
        """Format article citation in APA style."""
        parts = []

        authors = citation.get("authors", [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)

        year = citation.get("year")
        if year:
            parts.append(f"({year}).")

        title = citation.get("title")
        if title:
            parts.append(f"{title}.")

        source = citation.get("source")
        if source:
            notes = citation.get("notes", "")
            parts.append(f"{source}, {notes}.")

        return " ".join(parts)

    def _format_apa_online(self, citation: Dict) -> str:
        """Format online source in APA style."""
        parts = []

        authors = citation.get("authors", [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)

        year = citation.get("year")
        if year:
            parts.append(f"({year}).")

        title = citation.get("title")
        if title:
            parts.append(f"{title}.")

        url = citation.get("url")
        if url:
            parts.append(f"Retrieved from {url}")

        return " ".join(parts) if parts else citation.get("raw_text", "")

    def _format_apa_interview(self, citation: Dict) -> str:
        """Format interview citation in APA style."""
        parts = []

        authors = citation.get("authors", [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)

        year = citation.get("year")
        if year:
            parts.append(f"({year}).")

        source = citation.get("source")
        if source:
            parts.append(f"{source}.")

        return " ".join(parts)

    def _format_apa_authors(self, authors: List[str]) -> str:
        """Format author names in APA style."""
        if not authors:
            return ""

        formatted = []
        for author in authors[:7]:
            formatted.append(self._format_apa_single_author(author))

        if len(authors) > 7:
            formatted = formatted[:6]
            formatted.append("...")
            formatted.append(self._format_apa_single_author(authors[-1]))

        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]}, & {formatted[1]}"
        else:
            return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"

    def _format_apa_single_author(self, author: str) -> str:
        """Format single author name in APA style."""
        author = author.strip()

        if "," in author:
            parts = author.split(",", 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            parts = author.split()
            if len(parts) >= 2:
                first_name = " ".join(parts[:-1])
                last_name = parts[-1]
            else:
                return author

        initials = self._get_initials(first_name)
        return f"{last_name}, {initials}"

    def _get_initials(self, name: str) -> str:
        """Get initials from a name."""
        parts = name.split()
        initials = [f"{p[0].upper()}." for p in parts if p]
        return " ".join(initials)

    def _format_mla(self, citation: Dict, ctype: str) -> Optional[str]:
        """Format citation in MLA style."""
        parts = []

        authors = citation.get("authors", [])
        if authors:
            first_author = authors[0]
            if "," in first_author:
                parts.append(first_author)
            else:
                name_parts = first_author.split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}")
                else:
                    parts.append(first_author)

            if len(authors) > 1:
                parts[-1] += f", and {authors[1]}"

        title = citation.get("title")
        if title:
            if ctype == "book":
                parts.append(f"{title}.")
            else:
                parts.append(f'"{title}."')

        publisher = citation.get("publisher")
        source = citation.get("source")
        year = citation.get("year")

        if ctype == "book" and publisher:
            parts.append(f"{publisher},")
        elif source:
            parts.append(f"{source},")

        if year:
            parts.append(f"{year}.")

        return " ".join(parts) if parts else citation.get("raw_text", "")

    def _format_chicago(self, citation: Dict, ctype: str) -> Optional[str]:
        """Format citation in Chicago style (notes-bibliography)."""
        parts = []

        authors = citation.get("authors", [])
        if authors:
            parts.append(", ".join(authors))

        title = citation.get("title")
        if title:
            parts.append(f"{title}")

        publisher = citation.get("publisher")
        location = citation.get("location")
        year = citation.get("year")

        pub_info = []
        if location:
            pub_info.append(location)
        if publisher:
            pub_info.append(publisher)
        if year:
            pub_info.append(year)

        if pub_info:
            parts.append(f"({', '.join(pub_info)})")

        return ", ".join(parts) if parts else citation.get("raw_text", "")

    def save_bibliography(self, bibliography: str, output_path: Path) -> str:
        """
        Save bibliography to file.

        Args:
            bibliography: Formatted bibliography string
            output_path: Output file path

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Bibliography ({self.format_style.upper()} Format)\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(bibliography)
            f.write("\n")

        return str(output_path)


def main():
    """CLI entry point for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate formatted bibliographies from citation data"
    )
    parser.add_argument("--input", "-i", required=True, help="JSON file with citations")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument(
        "--format", "-f",
        default="apa",
        choices=["apa", "mla", "chicago"],
        help="Citation format (default: apa)",
    )

    args = parser.parse_args()

    generator = BibliographyGenerator(format_style=args.format)
    bibliography = generator.generate_from_file(Path(args.input))

    if bibliography:
        generator.save_bibliography(bibliography, Path(args.output))
        print(f"\nGenerated {args.format.upper()} bibliography")
    else:
        print("\nNo citations found")


if __name__ == "__main__":
    main()
