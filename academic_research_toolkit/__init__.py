"""
Academic Research Toolkit

A modular Python toolkit for processing, analyzing, and synthesizing academic PDF documents.
"""

__version__ = "1.0.0"
__author__ = "Academic Research Toolkit Contributors"


def __getattr__(name):
    """Lazy import for optional dependencies."""
    if name == "PDFProcessor":
        from academic_research_toolkit.pdf_processor import PDFProcessor
        return PDFProcessor
    elif name == "CitationExtractor":
        from academic_research_toolkit.citation_extractor import CitationExtractor
        return CitationExtractor
    elif name == "Citation":
        from academic_research_toolkit.citation_extractor import Citation
        return Citation
    elif name == "ThemeAnalyzer":
        from academic_research_toolkit.theme_analyzer import ThemeAnalyzer
        return ThemeAnalyzer
    elif name == "AffiliationExtractor":
        from academic_research_toolkit.affiliation_extractor import AffiliationExtractor
        return AffiliationExtractor
    elif name == "Author":
        from academic_research_toolkit.affiliation_extractor import Author
        return Author
    elif name == "BibliographyGenerator":
        from academic_research_toolkit.bibliography_generator import BibliographyGenerator
        return BibliographyGenerator
    elif name == "BibTeXExporter":
        from academic_research_toolkit.exporters.bibtex import BibTeXExporter
        return BibTeXExporter
    elif name == "RISExporter":
        from academic_research_toolkit.exporters.ris import RISExporter
        return RISExporter
    elif name == "CrossRefEnricher":
        from academic_research_toolkit.enrichment.crossref import CrossRefEnricher
        return CrossRefEnricher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PDFProcessor",
    "CitationExtractor",
    "Citation",
    "ThemeAnalyzer",
    "AffiliationExtractor",
    "Author",
    "BibliographyGenerator",
    "BibTeXExporter",
    "RISExporter",
    "CrossRefEnricher",
    "__version__",
]
