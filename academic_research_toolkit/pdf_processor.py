"""
PDF Processor for Academic Research

Extracts text and metadata from academic PDFs, outputting structured markdown files.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pdfplumber
from pypdf import PdfReader

from academic_research_toolkit.utils.exceptions import PDFProcessingError, OutputWriteError
from academic_research_toolkit.utils.validation import validate_output_dir


class PDFProcessor:
    """Extract text and metadata from academic PDFs."""

    def __init__(self, input_dir: str = None, output_dir: str = None):
        """
        Initialize PDF processor.

        Args:
            input_dir: Directory containing PDF files (optional for single-file processing)
            output_dir: Directory for output files (optional for programmatic use)
        """
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None

        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "processed": 0,
            "failed": 0,
            "total": 0,
        }

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """
        Extract metadata from PDF using pypdf.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with metadata fields
        """
        metadata = {
            "filename": pdf_path.name,
            "title": None,
            "author": None,
            "subject": None,
            "creator": None,
            "producer": None,
            "creation_date": None,
            "page_count": None,
        }

        try:
            reader = PdfReader(str(pdf_path))
            info = reader.metadata

            if info:
                metadata["title"] = info.get("/Title", None)
                metadata["author"] = info.get("/Author", None)
                metadata["subject"] = info.get("/Subject", None)
                metadata["creator"] = info.get("/Creator", None)
                metadata["producer"] = info.get("/Producer", None)

                creation_date = info.get("/CreationDate", None)
                if creation_date:
                    metadata["creation_date"] = str(creation_date)

            metadata["page_count"] = len(reader.pages)

        except Exception as e:
            # Log warning but don't fail - metadata is optional
            pass

        return metadata

    def extract_text(self, pdf_path: Path) -> Tuple[str, Dict[int, str]]:
        """
        Extract text from PDF using pdfplumber.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (full_text, page_texts_dict)

        Raises:
            PDFProcessingError: If PDF cannot be opened or read
        """
        full_text = []
        page_texts = {}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            full_text.append(text)
                            page_texts[page_num] = text
                    except Exception:
                        continue

        except Exception as e:
            raise PDFProcessingError(
                "Failed to open PDF",
                pdf_path=str(pdf_path),
                details=str(e),
            )

        return "\n\n".join(full_text), page_texts

    def clean_text(self, text: str) -> str:
        """
        Basic text cleaning.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = text.replace("\x0c", "")
        return text.strip()

    def generate_markdown(self, pdf_path: Path, metadata: Dict, text: str) -> str:
        """
        Generate markdown output with metadata and extracted text.

        Args:
            pdf_path: Source PDF path
            metadata: Extracted metadata
            text: Extracted and cleaned text

        Returns:
            Formatted markdown string
        """
        md_parts = []

        md_parts.append(f"# {metadata.get('title') or pdf_path.stem}\n")

        md_parts.append("## Document Metadata\n")
        md_parts.append(f"- **Filename:** {metadata['filename']}")

        if metadata.get("author"):
            md_parts.append(f"- **Author:** {metadata['author']}")

        if metadata.get("subject"):
            md_parts.append(f"- **Subject:** {metadata['subject']}")

        if metadata.get("creation_date"):
            md_parts.append(f"- **Date:** {metadata['creation_date']}")

        if metadata.get("page_count"):
            md_parts.append(f"- **Pages:** {metadata['page_count']}")

        md_parts.append(f"- **Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        md_parts.append("## Extracted Text\n")
        md_parts.append(text)

        return "\n".join(md_parts)

    def process_pdf(self, pdf_path: Path, output_dir: Path = None) -> Dict:
        """
        Process a single PDF file.

        Args:
            pdf_path: Path to PDF file
            output_dir: Override output directory

        Returns:
            Result dictionary with success status and paths
        """
        pdf_path = Path(pdf_path)
        out_dir = output_dir or self.output_dir

        try:
            metadata = self.extract_metadata(pdf_path)
            full_text, page_texts = self.extract_text(pdf_path)

            if not full_text:
                return {
                    "success": False,
                    "error": "No text extracted from PDF",
                    "pdf_path": str(pdf_path),
                }

            full_text = self.clean_text(full_text)
            markdown = self.generate_markdown(pdf_path, metadata, full_text)

            result = {
                "success": True,
                "pdf_path": str(pdf_path),
                "metadata": metadata,
                "text_length": len(full_text),
                "markdown": markdown,
            }

            if out_dir:
                out_dir = Path(out_dir)
                out_dir.mkdir(parents=True, exist_ok=True)

                output_filename = pdf_path.stem + ".md"
                output_path = out_dir / output_filename

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown)

                json_filename = pdf_path.stem + "_metadata.json"
                json_path = out_dir / json_filename

                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)

                result["output_path"] = str(output_path)
                result["json_path"] = str(json_path)

            return result

        except PDFProcessingError:
            raise
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pdf_path": str(pdf_path),
            }

    def process_directory(self, input_dir: Path = None, output_dir: Path = None) -> Dict:
        """
        Process all PDFs in a directory.

        Args:
            input_dir: Override input directory
            output_dir: Override output directory

        Returns:
            Statistics dictionary
        """
        in_dir = Path(input_dir) if input_dir else self.input_dir
        out_dir = Path(output_dir) if output_dir else self.output_dir

        if not in_dir:
            raise PDFProcessingError("No input directory specified")

        pdf_files = list(in_dir.glob("*.pdf"))
        self.stats["total"] = len(pdf_files)

        if not pdf_files:
            return self.stats

        for pdf_path in pdf_files:
            result = self.process_pdf(pdf_path, out_dir)

            if result.get("success"):
                self.stats["processed"] += 1
            else:
                self.stats["failed"] += 1

        return self.stats


def main():
    """CLI entry point for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract text and metadata from academic PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m academic_research_toolkit.pdf_processor --input ./papers --output ./extracted
        """,
    )

    parser.add_argument("--input", "-i", required=True, help="Directory containing PDF files")
    parser.add_argument("--output", "-o", required=True, help="Directory for output files")

    args = parser.parse_args()

    processor = PDFProcessor(args.input, args.output)
    stats = processor.process_directory()

    print(f"\nProcessed: {stats['processed']}/{stats['total']}")
    print(f"Failed: {stats['failed']}")


if __name__ == "__main__":
    main()
