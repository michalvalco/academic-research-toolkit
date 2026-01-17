"""
Academic Research Toolkit - Unified Command Line Interface

Provides a single entry point for all toolkit functionality.

Usage:
    research-toolkit <command> [options]

Commands:
    pdf      Extract text and metadata from PDFs
    cite     Extract citations from markdown files
    theme    Analyze themes in academic texts
    affil    Extract author affiliations from PDFs
    biblio   Generate formatted bibliographies
    process  Run full pipeline on a directory
"""

import argparse
import sys
from pathlib import Path

from academic_research_toolkit import __version__
from academic_research_toolkit.utils.exceptions import ToolkitError, InvalidInputError


def cmd_pdf(args):
    """Handle PDF processing command."""
    from academic_research_toolkit.pdf_processor import PDFProcessor
    from academic_research_toolkit.utils.validation import validate_output_dir

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    output_dir = validate_output_dir(args.output)

    processor = PDFProcessor()

    if input_path.is_file():
        result = processor.process_pdf(input_path, output_dir)
        if result.get("success"):
            print(f"Processed: {input_path.name}")
            print(f"  Output: {result.get('output_path')}")
            print(f"  Text length: {result.get('text_length')} characters")
            return 0
        else:
            print(f"Failed: {result.get('error')}")
            return 1
    else:
        processor.input_dir = input_path
        processor.output_dir = output_dir
        stats = processor.process_directory()

        print(f"\nPDF Processing Complete")
        print(f"  Processed: {stats['processed']}/{stats['total']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Output: {output_dir}")

        return 0 if stats["failed"] == 0 else 1


def cmd_cite(args):
    """Handle citation extraction command."""
    from academic_research_toolkit.citation_extractor import CitationExtractor
    from academic_research_toolkit.utils.validation import validate_output_dir

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    output_dir = validate_output_dir(args.output)

    extractor = CitationExtractor()

    if input_path.is_file():
        citations = extractor.extract_from_file(input_path)
        paths = extractor.save_citations(citations, output_dir, input_path.name)

        print(f"\nCitation Extraction Complete")
        print(f"  Found: {len(citations)} citations")
        print(f"  JSON: {paths['json_path']}")
        print(f"  Report: {paths['md_path']}")

        stats = extractor.get_stats()
        if stats["by_type"]:
            print(f"\n  By type:")
            for ctype, count in sorted(stats["by_type"].items()):
                print(f"    {ctype}: {count}")

        return 0
    else:
        # Process all markdown files in directory
        md_files = list(input_path.glob("*.md"))
        if not md_files:
            print(f"No markdown files found in: {input_path}")
            return 1

        total_citations = 0
        for md_file in md_files:
            citations = extractor.extract_from_file(md_file)
            extractor.save_citations(citations, output_dir, md_file.name)
            total_citations += len(citations)

        print(f"\nProcessed {len(md_files)} files")
        print(f"Total citations: {total_citations}")
        return 0


def cmd_theme(args):
    """Handle theme analysis command."""
    from academic_research_toolkit.theme_analyzer import ThemeAnalyzer
    from academic_research_toolkit.utils.validation import validate_output_dir

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    output_dir = validate_output_dir(args.output)

    analyzer = ThemeAnalyzer()

    if input_path.is_file():
        analyzer.analyze_file(input_path)
    else:
        analyzer.analyze_directory(input_path)

    paths = analyzer.save_analysis(output_dir)

    insights = analyzer.generate_insights()
    stats = insights["corpus_statistics"]

    print(f"\nTheme Analysis Complete")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Unique terms: {stats['unique_terms']}")
    print(f"  Total occurrences: {stats['total_terms']}")
    print(f"\n  Report: {paths['report_path']}")

    if insights["dominant_themes"]:
        print(f"\n  Top themes:")
        for theme in insights["dominant_themes"][:5]:
            print(f"    {theme['term']}: {theme['frequency']} occurrences")

    return 0


def cmd_affil(args):
    """Handle affiliation extraction command."""
    from academic_research_toolkit.affiliation_extractor import AffiliationExtractor
    from academic_research_toolkit.utils.validation import validate_output_dir

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    output_dir = validate_output_dir(args.output)

    extractor = AffiliationExtractor()

    if input_path.is_file():
        result = extractor.process_pdf(input_path, output_dir)
        if result.get("success"):
            print(f"\nAffiliation Extraction Complete")
            print(f"  Authors found: {result.get('count')}")
            if result.get("json_path"):
                print(f"  Output: {result.get('json_path')}")
            return 0
        else:
            print(f"Failed: {result.get('error')}")
            return 1
    else:
        extractor.input_dir = input_path
        extractor.output_dir = output_dir
        stats = extractor.process_all()

        print(f"\nAffiliation Extraction Complete")
        print(f"  Processed: {stats['processed']}/{stats['total']}")
        print(f"  Authors found: {stats['authors_found']}")
        print(f"  Failed: {stats['failed']}")

        return 0 if stats["failed"] == 0 else 1


def cmd_biblio(args):
    """Handle bibliography generation command."""
    from academic_research_toolkit.bibliography_generator import BibliographyGenerator

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    if input_path.suffix.lower() != ".json":
        print(f"Error: Input must be a JSON file with citation data")
        return 1

    try:
        generator = BibliographyGenerator(format_style=args.format)
    except InvalidInputError as e:
        print(f"Error: {e}")
        return 1

    bibliography = generator.generate_from_file(input_path)

    if not bibliography:
        print("No citations found in input file")
        return 1

    output_path = generator.save_bibliography(bibliography, Path(args.output))

    print(f"\nBibliography Generated")
    print(f"  Format: {args.format.upper()}")
    print(f"  Output: {output_path}")

    return 0


def cmd_process(args):
    """Handle full pipeline processing command."""
    from academic_research_toolkit.pdf_processor import PDFProcessor
    from academic_research_toolkit.citation_extractor import CitationExtractor
    from academic_research_toolkit.theme_analyzer import ThemeAnalyzer
    from academic_research_toolkit.affiliation_extractor import AffiliationExtractor
    from academic_research_toolkit.utils.validation import validate_output_dir

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    if not input_path.is_dir():
        print(f"Error: Input must be a directory for pipeline processing")
        return 1

    base_output = validate_output_dir(args.output)

    print(f"\n{'='*60}")
    print("ACADEMIC RESEARCH TOOLKIT - Full Pipeline")
    print(f"{'='*60}")
    print(f"Input: {input_path}")
    print(f"Output: {base_output}")

    # Step 1: PDF Processing
    print(f"\n{'─'*60}")
    print("Step 1: Extracting text from PDFs...")
    print(f"{'─'*60}")

    pdf_output = base_output / "1_extracted_text"
    processor = PDFProcessor(str(input_path), str(pdf_output))
    pdf_stats = processor.process_directory()

    print(f"  Processed: {pdf_stats['processed']}/{pdf_stats['total']} PDFs")

    if pdf_stats["processed"] == 0:
        print("No PDFs processed. Pipeline cannot continue.")
        return 1

    # Step 2: Citation Extraction
    print(f"\n{'─'*60}")
    print("Step 2: Extracting citations...")
    print(f"{'─'*60}")

    cite_output = base_output / "2_citations"
    cite_output.mkdir(parents=True, exist_ok=True)

    extractor = CitationExtractor()
    md_files = list(pdf_output.glob("*.md"))
    total_citations = 0

    for md_file in md_files:
        # Skip metadata files
        if "_metadata" in md_file.name:
            continue
        citations = extractor.extract_from_file(md_file)
        if citations:
            extractor.save_citations(citations, cite_output, md_file.name)
            total_citations += len(citations)

    print(f"  Found: {total_citations} citations")

    # Step 3: Theme Analysis
    print(f"\n{'─'*60}")
    print("Step 3: Analyzing themes...")
    print(f"{'─'*60}")

    theme_output = base_output / "3_themes"
    analyzer = ThemeAnalyzer()
    analyzer.analyze_directory(pdf_output)
    analyzer.save_analysis(theme_output)

    insights = analyzer.generate_insights()
    print(f"  Unique terms: {insights['corpus_statistics']['unique_terms']}")
    print(f"  Dominant themes: {len(insights['dominant_themes'])}")

    # Step 4: Affiliation Extraction
    print(f"\n{'─'*60}")
    print("Step 4: Extracting author affiliations...")
    print(f"{'─'*60}")

    affil_output = base_output / "4_affiliations"
    affil_extractor = AffiliationExtractor(str(input_path), str(affil_output))
    affil_stats = affil_extractor.process_all()

    print(f"  Authors found: {affil_stats['authors_found']}")

    # Summary
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"\nOutput directories:")
    print(f"  1. Extracted text: {pdf_output}")
    print(f"  2. Citations: {cite_output}")
    print(f"  3. Theme analysis: {theme_output}")
    print(f"  4. Affiliations: {affil_output}")

    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="research-toolkit",
        description="Academic Research Toolkit - Process and analyze academic PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  research-toolkit pdf -i ./papers -o ./extracted
  research-toolkit cite -i ./extracted/paper.md -o ./citations
  research-toolkit theme -i ./extracted -o ./analysis
  research-toolkit affil -i ./papers -o ./authors
  research-toolkit biblio -i ./citations/paper_citations.json -o ./bib.md -f apa
  research-toolkit process -i ./papers -o ./results
        """,
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # PDF command
    pdf_parser = subparsers.add_parser(
        "pdf",
        help="Extract text and metadata from PDFs",
    )
    pdf_parser.add_argument("--input", "-i", required=True, help="PDF file or directory")
    pdf_parser.add_argument("--output", "-o", required=True, help="Output directory")

    # Citation command
    cite_parser = subparsers.add_parser(
        "cite",
        help="Extract citations from markdown files",
    )
    cite_parser.add_argument("--input", "-i", required=True, help="Markdown file or directory")
    cite_parser.add_argument("--output", "-o", required=True, help="Output directory")

    # Theme command
    theme_parser = subparsers.add_parser(
        "theme",
        help="Analyze themes in academic texts",
    )
    theme_parser.add_argument("--input", "-i", required=True, help="Markdown file or directory")
    theme_parser.add_argument("--output", "-o", required=True, help="Output directory")

    # Affiliation command
    affil_parser = subparsers.add_parser(
        "affil",
        help="Extract author affiliations from PDFs",
    )
    affil_parser.add_argument("--input", "-i", required=True, help="PDF file or directory")
    affil_parser.add_argument("--output", "-o", required=True, help="Output directory")

    # Bibliography command
    biblio_parser = subparsers.add_parser(
        "biblio",
        help="Generate formatted bibliographies",
    )
    biblio_parser.add_argument("--input", "-i", required=True, help="Citations JSON file")
    biblio_parser.add_argument("--output", "-o", required=True, help="Output file path")
    biblio_parser.add_argument(
        "--format", "-f",
        default="apa",
        choices=["apa", "mla", "chicago"],
        help="Citation format (default: apa)",
    )

    # Process command (full pipeline)
    process_parser = subparsers.add_parser(
        "process",
        help="Run full pipeline on a PDF directory",
    )
    process_parser.add_argument("--input", "-i", required=True, help="Directory with PDFs")
    process_parser.add_argument("--output", "-o", required=True, help="Base output directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        command_handlers = {
            "pdf": cmd_pdf,
            "cite": cmd_cite,
            "theme": cmd_theme,
            "affil": cmd_affil,
            "biblio": cmd_biblio,
            "process": cmd_process,
        }

        handler = command_handlers.get(args.command)
        if handler:
            return handler(args)
        else:
            parser.print_help()
            return 1

    except ToolkitError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
