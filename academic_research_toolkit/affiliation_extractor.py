"""
Author Affiliation Extractor for Academic Research

Extracts author names and institutional affiliations from academic PDFs.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import pdfplumber

from academic_research_toolkit.utils.exceptions import PDFProcessingError


@dataclass
class Author:
    """Structured author information."""

    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    confidence: float = 0.0


class AffiliationExtractor:
    """Extract author affiliations from academic PDFs."""

    def __init__(self, input_dir: str = None, output_dir: str = None):
        """
        Initialize affiliation extractor.

        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory for output files
        """
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "processed": 0,
            "failed": 0,
            "total": 0,
            "authors_found": 0,
        }

        self.titles = r"(?:Dr\.|Prof\.|Professor|Ph\.D\.|M\.A\.|B\.A\.|Rev\.|Fr\.)"

        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )

        self.affiliation_keywords = [
            "university", "univerzita", "college", "institute", "institut",
            "faculty", "fakulta", "department", "katedra", "school", "škola",
            "academy", "akadémia", "center", "centre", "centrum",
        ]

    def extract_first_page_text(self, pdf_path: Path) -> str:
        """Extract text from first page where author info typically appears."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > 0:
                    return pdf.pages[0].extract_text() or ""
        except Exception as e:
            raise PDFProcessingError(
                "Could not extract text",
                pdf_path=str(pdf_path),
                details=str(e),
            )
        return ""

    def extract_emails(self, text: str) -> List[str]:
        """Extract all email addresses from text."""
        return self.email_pattern.findall(text)

    def extract_author_blocks(self, text: str) -> List[str]:
        """Split text into potential author blocks."""
        section_markers = [
            "abstract", "introduction", "úvod", "keywords", "kľúčové slová",
            "contents", "obsah", r"\d+\.\s+[A-Z]",
        ]

        pattern = "|".join(section_markers)
        parts = re.split(pattern, text, flags=re.IGNORECASE, maxsplit=1)

        author_section = parts[0] if parts else text

        lines = author_section.split("\n")

        lines = [
            line.strip()
            for line in lines
            if len(line.strip()) > 3 and not re.match(r"^\d+$", line.strip())
        ]

        return lines

    def is_affiliation_line(self, line: str) -> bool:
        """Check if line contains affiliation information."""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.affiliation_keywords)

    def is_author_name(self, line: str) -> bool:
        """Heuristic to detect if line is likely an author name."""
        cleaned = re.sub(self.titles, "", line, flags=re.IGNORECASE).strip()

        if len(cleaned) < 3 or len(cleaned) > 60:
            return False

        words = cleaned.split()
        if len(words) < 1 or len(words) > 5:
            return False

        capital_pattern = r"^[A-ZÁČĎÉÍĽŇÓÔŔŠŤÚÝŽ]"
        capitals = sum(1 for w in words if re.match(capital_pattern, w))

        if capitals < len(words) / 2:
            return False

        if self.is_affiliation_line(line):
            return False

        if "," in line:
            parts = line.split(",")
            if len(parts) == 2:
                last_part = parts[-1].strip()
                if len(last_part) <= 3 or len(last_part.split()) == 1:
                    return False

        return True

    def parse_affiliation(self, text: str) -> Dict[str, Optional[str]]:
        """Parse affiliation text into components."""
        result = {
            "full": text,
            "department": None,
            "institution": None,
            "location": None,
        }

        dept_match = re.search(
            r"(department|katedra|faculty|fakulta)\s+of\s+([^,\n]+)",
            text, re.IGNORECASE,
        )
        if dept_match:
            result["department"] = dept_match.group(0).strip()

        for keyword in ["university", "univerzita", "institute", "institut", "college"]:
            if keyword in text.lower():
                parts = re.split(r"[,\n]", text)
                for part in parts:
                    if keyword in part.lower():
                        result["institution"] = part.strip()
                        break
                break

        parts = text.split(",")
        if len(parts) >= 2:
            potential_location = parts[-1].strip()
            if len(potential_location.split()) <= 3:
                result["location"] = potential_location

        return result

    def extract_authors_from_text(self, text: str) -> List[Author]:
        """Extract authors and affiliations from PDF text."""
        authors = []
        emails = self.extract_emails(text)
        lines = self.extract_author_blocks(text)

        current_authors = []
        current_affiliation = []

        for line in lines:
            if not line:
                continue

            if self.is_author_name(line):
                if current_authors and current_affiliation:
                    affiliation_text = " ".join(current_affiliation)
                    parsed = self.parse_affiliation(affiliation_text)

                    for author_name in current_authors:
                        authors.append(Author(
                            name=author_name,
                            affiliation=parsed["full"],
                            department=parsed["department"],
                            institution=parsed["institution"],
                            location=parsed["location"],
                            confidence=0.7,
                        ))

                    current_authors = []
                    current_affiliation = []

                current_authors.append(line.strip())

            elif self.is_affiliation_line(line):
                current_affiliation.append(line.strip())

        if current_authors and current_affiliation:
            affiliation_text = " ".join(current_affiliation)
            parsed = self.parse_affiliation(affiliation_text)

            for author_name in current_authors:
                authors.append(Author(
                    name=author_name,
                    affiliation=parsed["full"],
                    department=parsed["department"],
                    institution=parsed["institution"],
                    location=parsed["location"],
                    confidence=0.7,
                ))

        if emails and authors:
            for i, email in enumerate(emails):
                if i < len(authors):
                    authors[i].email = email

        return authors

    def process_pdf(self, pdf_path: Path, output_dir: Path = None) -> Dict:
        """Process a single PDF and extract author affiliations."""
        pdf_path = Path(pdf_path)
        out_dir = output_dir or self.output_dir

        try:
            text = self.extract_first_page_text(pdf_path)

            if not text:
                return {
                    "success": False,
                    "error": "No text extracted from first page",
                    "pdf_path": str(pdf_path),
                }

            authors = self.extract_authors_from_text(text)

            output_data = {
                "source": pdf_path.name,
                "processed": datetime.now().isoformat(),
                "authors": [asdict(author) for author in authors],
                "count": len(authors),
            }

            result = {
                "success": True,
                "pdf_path": str(pdf_path),
                "authors": authors,
                "count": len(authors),
            }

            if out_dir:
                out_dir = Path(out_dir)
                out_dir.mkdir(parents=True, exist_ok=True)

                json_filename = pdf_path.stem + "_authors.json"
                json_path = out_dir / json_filename

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)

                md_filename = pdf_path.stem + "_authors.md"
                md_path = out_dir / md_filename

                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(self._generate_markdown_report(output_data, authors))

                result["json_path"] = str(json_path)
                result["md_path"] = str(md_path)

            self.stats["authors_found"] += len(authors)
            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pdf_path": str(pdf_path),
            }

    def _generate_markdown_report(self, data: Dict, authors: List[Author]) -> str:
        """Generate markdown report of extracted authors."""
        lines = [
            f"# Author Affiliations: {data['source']}\n",
            f"**Processed:** {data['processed']}  ",
            f"**Authors Found:** {data['count']}\n",
            "---\n",
        ]

        if not authors:
            lines.append("*No authors detected in this document.*\n")
        else:
            for i, author in enumerate(authors, 1):
                lines.append(f"\n## {i}. {author.name}\n")

                if author.email:
                    lines.append(f"**Email:** {author.email}  \n")

                if author.institution:
                    lines.append(f"**Institution:** {author.institution}  \n")

                if author.department:
                    lines.append(f"**Department:** {author.department}  \n")

                if author.location:
                    lines.append(f"**Location:** {author.location}  \n")

                if author.affiliation:
                    lines.append(f"\n**Full Affiliation:**  \n{author.affiliation}\n")

                lines.append(f"\n*Confidence: {author.confidence:.1%}*\n")

        return "\n".join(lines)

    def process_all(self) -> Dict:
        """Process all PDFs in input directory."""
        if not self.input_dir:
            raise PDFProcessingError("No input directory specified")

        pdf_files = list(self.input_dir.glob("*.pdf"))
        self.stats["total"] = len(pdf_files)

        for pdf_path in pdf_files:
            result = self.process_pdf(pdf_path)

            if result.get("success"):
                self.stats["processed"] += 1
            else:
                self.stats["failed"] += 1

        return self.stats


def main():
    """CLI entry point for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract author affiliations from academic PDFs"
    )
    parser.add_argument("--input", "-i", required=True, help="Directory containing PDFs")
    parser.add_argument("--output", "-o", required=True, help="Directory for output files")

    args = parser.parse_args()

    extractor = AffiliationExtractor(args.input, args.output)
    stats = extractor.process_all()

    print(f"\nProcessed: {stats['processed']}/{stats['total']}")
    print(f"Authors found: {stats['authors_found']}")


if __name__ == "__main__":
    main()
