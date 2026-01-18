"""
Intelligence module for AI-powered research assistance.

Provides vector search, intelligent Q&A, and research gap detection.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from academic_research_toolkit.intelligence.vector_store import VectorStore
    from academic_research_toolkit.intelligence.assistant import ResearchAssistant
    from academic_research_toolkit.intelligence.gap_detector import GapDetector


def __getattr__(name):
    """Lazy import for optional dependencies."""
    if name == "VectorStore":
        from academic_research_toolkit.intelligence.vector_store import VectorStore
        return VectorStore
    elif name == "ResearchAssistant":
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        return ResearchAssistant
    elif name == "GapDetector":
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "VectorStore",
    "ResearchAssistant",
    "GapDetector",
]
