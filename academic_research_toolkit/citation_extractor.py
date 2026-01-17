"""
Citation Extractor for Academic Research

Identifies and extracts structured citation data from academic texts.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from academic_research_toolkit.utils.exceptions import CitationExtractionError


@dataclass
class Citation:
    """Structured citation data."""

    raw_text: str
    citation_type: str  # 'book', 'article', 'archival', 'interview', etc.
    authors: List[str]
    year: Optional[str]
    title: Optional[str]
    publisher: Optional[str]
    location: Optional[str]
    source: Optional[str]  # journal, archive, etc.
    url: Optional[str]
    notes: Optional[str]
    confidence: float  # 0.0 to 1.0


class CitationExtractor:
    """Extract and parse citations from academic texts."""

    def __init__(self):
        """Initialize citation extractor with regex patterns."""
        self.patterns = {
            "book": self._compile_book_patterns(),
            "article": self._compile_article_patterns(),
            "interview": self._compile_interview_patterns(),
            "archival": self._compile_archival_patterns(),
            "online": self._compile_online_patterns(),
        }

        self.stats = {
            "total_lines": 0,
            "citations_found": 0,
            "by_type": {},
        }

    def _compile_book_patterns(self) -> List[re.Pattern]:
        """Regex patterns for book citations."""
        return [
            re.compile(
                r"^-?\s*([A-ZČŠŽÁÉÍÓÚÝŇĎŤĽ][^\d\.]+?)\.\s*"
                r"(\d{4})\.\s*"
                r"([^\.]+?)\.\s*"
                r"([^:]+):\s*"
                r"([^\.]+)\.",
                re.MULTILINE | re.UNICODE,
            ),
        ]

    def _compile_article_patterns(self) -> List[re.Pattern]:
        """Regex patterns for journal articles."""
        return [
            re.compile(
                r"^-?\s*([A-ZČŠŽÁÉÍÓÚÝŇĎŤĽ][^\d\.]+?)\.\s*"
                r'(\d{4})\.\s*"([^"]+)"\.\s*'
                r"([^\d]+?)\s+(\d+)\s*"
                r"(?:\((\d+)\))?\s*:\s*(\d+-\d+)",
                re.MULTILINE | re.UNICODE,
            ),
        ]

    def _compile_interview_patterns(self) -> List[re.Pattern]:
        """Regex patterns for interviews."""
        return [
            re.compile(
                r"^-?\s*([A-ZČŠŽÁÉÍÓÚÝŇĎŤĽ][^\d\.]+?)\.\s*"
                r"(\d{4})\.\s*"
                r"(?:Interview|Rozhovor)\s+"
                r"(?:by|s)\s+"
                r"([^\.]+?)\.\s*"
                r"([^,]+),\s*"
                r"([^\.]+)\.",
                re.MULTILINE | re.UNICODE | re.IGNORECASE,
            ),
        ]

    def _compile_archival_patterns(self) -> List[re.Pattern]:
        """Regex patterns for archival documents."""
        return [
            re.compile(
                r"^-?\s*([Aa]rchív|[Ll]ibrary)[^\.]+\.\s*" r"(\d{4}(?:-\d{4})?)",
                re.MULTILINE | re.UNICODE,
            ),
        ]

    def _compile_online_patterns(self) -> List[re.Pattern]:
        """Regex patterns for online sources."""
        return [
            re.compile(r"(https?://[^\s]+)", re.UNICODE),
        ]

    def extract_from_file(self, filepath: Path) -> List[Citation]:
        """
        Extract citations from a markdown file.

        Args:
            filepath: Path to markdown file

        Returns:
            List of Citation objects
        """
        filepath = Path(filepath)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise CitationExtractionError(
                f"Failed to read file: {filepath}",
                source_file=str(filepath),
                details=str(e),
            )

        return self.extract_from_text(content)

    def extract_from_text(self, content: str) -> List[Citation]:
        """
        Extract citations from text content.

        Args:
            content: Text content to analyze

        Returns:
            List of Citation objects
        """
        content = self._skip_metadata(content)

        citations = []
        lines = content.split("\n")
        self.stats["total_lines"] = len(lines)

        current_section = None

        for line in lines:
            if line.startswith("#"):
                current_section = line.strip()
                continue

            if not line.strip():
                continue

            citation = self._parse_line(line, current_section)
            if citation:
                citations.append(citation)
                self.stats["citations_found"] += 1

                ctype = citation.citation_type
                self.stats["by_type"][ctype] = self.stats["by_type"].get(ctype, 0) + 1

        return citations

    def _skip_metadata(self, content: str) -> str:
        """Skip the metadata section at the beginning."""
        parts = content.split("## Extracted Text", 1)
        if len(parts) == 2:
            return parts[1]
        return content

    def _parse_line(self, line: str, section: Optional[str]) -> Optional[Citation]:
        """Try to parse a line as a citation."""
        if len(line) < 20:
            return None

        for citation_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    return self._build_citation(line, citation_type, match, section)

        if line.strip().startswith("-") and len(line) > 30:
            return Citation(
                raw_text=line.strip(),
                citation_type="unclassified",
                authors=[],
                year=self._extract_year(line),
                title=None,
                publisher=None,
                location=None,
                source=None,
                url=self._extract_url(line),
                notes=section,
                confidence=0.3,
            )

        return None

    def _build_citation(
        self, line: str, ctype: str, match: re.Match, section: Optional[str]
    ) -> Optional[Citation]:
        """Build a Citation object from regex match."""
        if ctype == "book":
            return Citation(
                raw_text=line.strip(),
                citation_type="book",
                authors=self._parse_authors(match.group(1)),
                year=match.group(2),
                title=match.group(3).strip(),
                location=match.group(4).strip(),
                publisher=match.group(5).strip(),
                source=None,
                url=None,
                notes=section,
                confidence=0.9,
            )

        elif ctype == "article":
            return Citation(
                raw_text=line.strip(),
                citation_type="article",
                authors=self._parse_authors(match.group(1)),
                year=match.group(2),
                title=match.group(3).strip(),
                source=match.group(4).strip(),
                publisher=None,
                location=None,
                url=None,
                notes=f"{section} | Vol {match.group(5)} ({match.group(6)}): {match.group(7)}" if section else f"Vol {match.group(5)} ({match.group(6)}): {match.group(7)}",
                confidence=0.9,
            )

        elif ctype == "interview":
            return Citation(
                raw_text=line.strip(),
                citation_type="interview",
                authors=self._parse_authors(match.group(1)),
                year=match.group(2),
                title=f"Interview with {match.group(1)}",
                location=match.group(4).strip(),
                publisher=None,
                source=f"Interviewed by {match.group(3)}",
                url=None,
                notes=f"{section} | {match.group(5)}" if section else match.group(5),
                confidence=0.85,
            )

        elif ctype == "archival":
            return Citation(
                raw_text=line.strip(),
                citation_type="archival",
                authors=[],
                year=match.group(2),
                title=None,
                location=None,
                publisher=None,
                source=line.strip(),
                url=None,
                notes=section,
                confidence=0.7,
            )

        elif ctype == "online":
            return Citation(
                raw_text=line.strip(),
                citation_type="online",
                authors=[],
                year=self._extract_year(line),
                title=None,
                location=None,
                publisher=None,
                source=None,
                url=match.group(1),
                notes=section,
                confidence=0.8,
            )

        return None

    def _parse_authors(self, author_string: str) -> List[str]:
        """Parse author names from string."""
        authors = re.split(r"\s+(?:and|a)\s+|,\s*(?:and|a)\s+", author_string)
        return [a.strip() for a in authors if a.strip()]

    def _extract_year(self, text: str) -> Optional[str]:
        """Try to extract a year from text."""
        match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
        return match.group(1) if match else None

    def _extract_url(self, text: str) -> Optional[str]:
        """Try to extract a URL from text."""
        match = re.search(r"https?://[^\s]+", text)
        return match.group(0) if match else None

    def save_citations(
        self, citations: List[Citation], output_dir: Path, source_filename: str
    ) -> Dict[str, str]:
        """
        Save extracted citations in multiple formats.

        Args:
            citations: List of Citation objects
            output_dir: Output directory
            source_filename: Original source filename

        Returns:
            Dictionary with output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = Path(source_filename).stem

        json_path = output_dir / f"{base_name}_citations.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in citations], f, indent=2, ensure_ascii=False)

        md_path = output_dir / f"{base_name}_citations.md"
        self._generate_markdown_report(citations, md_path, source_filename)

        stats_path = output_dir / f"{base_name}_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

        return {
            "json_path": str(json_path),
            "md_path": str(md_path),
            "stats_path": str(stats_path),
        }

    def _generate_markdown_report(
        self, citations: List[Citation], output_path: Path, source_filename: str
    ):
        """Generate a markdown report of citations."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Citation Analysis: {source_filename}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Citations Found:** {len(citations)}\n\n")

            f.write("## Citations by Type\n\n")
            for ctype, count in sorted(self.stats["by_type"].items()):
                f.write(f"- **{ctype.title()}:** {count}\n")
            f.write("\n")

            by_type = {}
            for citation in citations:
                ctype = citation.citation_type
                if ctype not in by_type:
                    by_type[ctype] = []
                by_type[ctype].append(citation)

            for ctype in sorted(by_type.keys()):
                f.write(f"## {ctype.title()} Citations\n\n")

                for citation in by_type[ctype]:
                    f.write(f"### {citation.title or 'Untitled'}\n\n")

                    if citation.authors:
                        f.write(f"**Authors:** {', '.join(citation.authors)}\n\n")

                    if citation.year:
                        f.write(f"**Year:** {citation.year}\n\n")

                    if citation.url:
                        f.write(f"**URL:** {citation.url}\n\n")

                    f.write(f"**Confidence:** {citation.confidence:.0%}\n\n")
                    f.write(f"**Raw Text:**\n```\n{citation.raw_text}\n```\n\n")
                    f.write("---\n\n")

    def get_stats(self) -> Dict:
        """Get extraction statistics."""
        return self.stats.copy()


def main():
    """CLI entry point for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract structured citation data from academic texts"
    )
    parser.add_argument("--input", "-i", required=True, help="Markdown file to process")
    parser.add_argument("--output", "-o", required=True, help="Directory for output files")

    args = parser.parse_args()

    extractor = CitationExtractor()
    citations = extractor.extract_from_file(Path(args.input))
    extractor.save_citations(citations, Path(args.output), Path(args.input).name)

    print(f"\nFound {len(citations)} citations")


if __name__ == "__main__":
    main()
