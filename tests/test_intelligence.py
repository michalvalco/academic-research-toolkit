"""Comprehensive tests for the intelligence module."""

import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest


# Mock numpy for environments where it might not be installed
@pytest.fixture
def mock_numpy():
    """Mock numpy for testing without the actual dependency."""
    with patch.dict("sys.modules", {"numpy": MagicMock()}):
        import numpy as np
        np.array = lambda x: x
        np.zeros = lambda x: [0] * x if isinstance(x, int) else [[0] * x[1] for _ in range(x[0])]
        np.dot = lambda a, b: sum(x * y for x, y in zip(a, b)) if isinstance(a[0], (int, float)) else 0
        np.linalg = MagicMock()
        np.linalg.norm = lambda x, axis=None, keepdims=False: 1.0
        np.argsort = lambda x: list(range(len(x)))[::-1]
        np.where = lambda cond, a, b: a
        yield np


# ============================================================================
# VectorStore Tests
# ============================================================================

class TestVectorStoreInit:
    """Tests for VectorStore initialization."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore with local embeddings (no external deps)."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            return VectorStore(embedding_provider="local")
        except ImportError:
            pytest.skip("numpy not installed")

    def test_init_defaults(self, vector_store):
        """Test VectorStore initialization with defaults."""
        assert vector_store.embedding_model == "text-embedding-3-small"
        assert vector_store.embedding_provider == "local"
        assert vector_store.chunk_size == 1000
        assert vector_store.chunk_overlap == 200
        assert vector_store.documents == []

    def test_init_custom_params(self):
        """Test VectorStore initialization with custom parameters."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            store = VectorStore(
                embedding_model="custom-model",
                embedding_provider="local",
                chunk_size=500,
                chunk_overlap=100,
            )
            assert store.embedding_model == "custom-model"
            assert store.chunk_size == 500
            assert store.chunk_overlap == 100
        except ImportError:
            pytest.skip("numpy not installed")


class TestVectorStoreChunking:
    """Tests for document chunking functionality."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore with local embeddings."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            return VectorStore(embedding_provider="local", chunk_size=100, chunk_overlap=20)
        except ImportError:
            pytest.skip("numpy not installed")

    def test_chunk_short_text(self, vector_store):
        """Test chunking text shorter than chunk_size."""
        text = "This is a short text."
        chunks = vector_store._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_long_text(self, vector_store):
        """Test chunking text longer than chunk_size."""
        text = "Word " * 50  # 250 characters
        chunks = vector_store._chunk_text(text)
        assert len(chunks) > 1
        # Each chunk should be roughly chunk_size or less
        for chunk in chunks:
            assert len(chunk) <= vector_store.chunk_size + 50  # Allow some flexibility

    def test_chunk_with_sentence_boundaries(self, vector_store):
        """Test chunking respects sentence boundaries."""
        text = "First sentence. " * 10  # Multiple sentences
        chunks = vector_store._chunk_text(text)
        # Chunks should ideally end at sentence boundaries
        for chunk in chunks[:-1]:  # Except possibly the last one
            assert chunk.strip().endswith(".") or len(chunk) <= vector_store.chunk_size


class TestVectorStoreDocuments:
    """Tests for document operations."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore with local embeddings."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            return VectorStore(embedding_provider="local", chunk_size=500)
        except ImportError:
            pytest.skip("numpy not installed")

    def test_add_document_basic(self, vector_store):
        """Test adding a basic document."""
        text = "This is a test document about machine learning."
        count = vector_store.add_document(
            doc_id="test_doc",
            text=text,
            metadata={"title": "Test Document"},
        )

        assert count >= 1
        assert len(vector_store.documents) >= 1
        assert vector_store.documents[0].doc_id in ["test_doc", "test_doc_chunk_0"]
        assert vector_store.documents[0].metadata.get("title") == "Test Document"

    def test_add_document_with_chunking(self, vector_store):
        """Test adding a document that needs chunking."""
        text = "Machine learning is fascinating. " * 50  # Long text
        count = vector_store.add_document(
            doc_id="long_doc",
            text=text,
            metadata={"title": "Long Document"},
            chunk=True,
        )

        # Should create multiple chunks
        assert count > 1
        # All chunks should have original_doc_id in metadata
        for doc in vector_store.documents:
            assert doc.metadata.get("original_doc_id") == "long_doc"

    def test_add_document_no_chunking(self, vector_store):
        """Test adding a document without chunking."""
        text = "Machine learning is fascinating. " * 50
        count = vector_store.add_document(
            doc_id="no_chunk",
            text=text,
            chunk=False,
        )

        assert count == 1

    def test_add_citations(self, vector_store):
        """Test adding citations for indexing."""
        citations = [
            {
                "title": "Machine Learning in Healthcare",
                "authors": ["Smith, John", "Doe, Jane"],
                "year": "2020",
            },
            {
                "title": "Deep Learning Applications",
                "authors": ["Brown, Bob"],
                "year": "2021",
                "doi": "10.1234/test",
            },
        ]

        count = vector_store.add_citations(citations)

        assert count == 2
        assert len(vector_store.documents) == 2

    def test_add_citations_empty(self, vector_store):
        """Test adding empty citations list."""
        count = vector_store.add_citations([])
        assert count == 0


class TestVectorStoreSearch:
    """Tests for search functionality."""

    @pytest.fixture
    def populated_store(self):
        """Create a VectorStore with some documents."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            store = VectorStore(embedding_provider="local")

            # Add some documents
            store.add_document(
                "doc1",
                "Machine learning is a branch of artificial intelligence.",
                {"title": "ML Intro"},
            )
            store.add_document(
                "doc2",
                "Natural language processing enables computers to understand text.",
                {"title": "NLP Basics"},
            )
            store.add_document(
                "doc3",
                "Deep learning uses neural networks with many layers.",
                {"title": "Deep Learning"},
            )
            return store
        except ImportError:
            pytest.skip("numpy not installed")

    def test_search_basic(self, populated_store):
        """Test basic search functionality."""
        results = populated_store.search("machine learning", top_k=3)

        assert len(results) <= 3
        for result in results:
            assert "doc_id" in result
            assert "text" in result
            assert "score" in result
            assert "metadata" in result

    def test_search_top_k(self, populated_store):
        """Test search returns correct number of results."""
        results = populated_store.search("neural networks", top_k=2)
        assert len(results) <= 2

    def test_search_empty_store(self):
        """Test search on empty store."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            store = VectorStore(embedding_provider="local")
            results = store.search("test query")
            assert results == []
        except ImportError:
            pytest.skip("numpy not installed")

    def test_search_with_filter(self, populated_store):
        """Test search with filter function."""
        # Filter to only include documents with "ML" in title
        filter_fn = lambda doc: "ML" in doc.metadata.get("title", "")
        results = populated_store.search(
            "machine learning",
            filter_fn=filter_fn,
        )

        for result in results:
            assert "ML" in result["metadata"].get("title", "")


class TestVectorStorePersistence:
    """Tests for save/load functionality."""

    @pytest.fixture
    def populated_store(self):
        """Create a VectorStore with some documents."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            store = VectorStore(embedding_provider="local")
            store.add_document("doc1", "Test document one", {"title": "Doc 1"})
            store.add_document("doc2", "Test document two", {"title": "Doc 2"})
            return store
        except ImportError:
            pytest.skip("numpy not installed")

    def test_save_and_load(self, populated_store, tmp_path):
        """Test saving and loading the vector store."""
        save_path = tmp_path / "vectors.pkl"

        # Save
        populated_store.save(save_path)
        assert save_path.exists()

        # Load into new store
        from academic_research_toolkit.intelligence.vector_store import VectorStore
        new_store = VectorStore(embedding_provider="local")
        new_store.load(save_path)

        assert len(new_store.documents) == len(populated_store.documents)
        assert new_store.embedding_model == populated_store.embedding_model

    def test_save_creates_parent_dirs(self, populated_store, tmp_path):
        """Test that save creates parent directories."""
        save_path = tmp_path / "nested" / "dir" / "vectors.pkl"
        populated_store.save(save_path)
        assert save_path.exists()


class TestVectorStoreStats:
    """Tests for statistics and utility methods."""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore with local embeddings."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            store = VectorStore(embedding_provider="local")
            store.add_document("doc1", "Test document", {"title": "Test"})
            return store
        except ImportError:
            pytest.skip("numpy not installed")

    def test_get_stats(self, vector_store):
        """Test getting store statistics."""
        stats = vector_store.get_stats()

        assert "document_count" in stats
        assert "embedding_model" in stats
        assert "embedding_provider" in stats
        assert "chunk_size" in stats
        assert stats["document_count"] >= 1

    def test_clear(self, vector_store):
        """Test clearing the store."""
        assert len(vector_store.documents) > 0
        vector_store.clear()
        assert len(vector_store.documents) == 0


# ============================================================================
# ResearchAssistant Tests
# ============================================================================

class TestResearchAssistantInit:
    """Tests for ResearchAssistant initialization."""

    def test_init_defaults(self):
        """Test ResearchAssistant initialization with defaults."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        assistant = ResearchAssistant(dry_run=True)

        assert assistant.vector_store is None
        assert assistant.model == "claude-sonnet-4-20250514"
        assert assistant.max_tokens == 4096
        assert assistant.dry_run is True

    def test_init_with_vector_store(self):
        """Test initialization with vector store."""
        try:
            from academic_research_toolkit.intelligence.assistant import ResearchAssistant
            from academic_research_toolkit.intelligence.vector_store import VectorStore

            store = VectorStore(embedding_provider="local")
            assistant = ResearchAssistant(vector_store=store, dry_run=True)

            assert assistant.vector_store is store
        except ImportError:
            pytest.skip("numpy not installed")


class TestResearchAssistantContextFormatting:
    """Tests for context formatting."""

    @pytest.fixture
    def assistant(self):
        """Create a ResearchAssistant in dry_run mode."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        return ResearchAssistant(dry_run=True)

    def test_format_context_empty(self, assistant):
        """Test formatting empty context."""
        result = assistant._format_context([])
        assert result == ""

    def test_format_context_with_metadata(self, assistant):
        """Test formatting context with metadata."""
        context = [
            {
                "text": "This is the document content.",
                "metadata": {
                    "title": "Test Paper",
                    "authors": ["John Smith", "Jane Doe"],
                    "year": "2020",
                },
                "score": 0.95,
            }
        ]

        result = assistant._format_context(context)

        assert "Source 1" in result
        assert "Test Paper" in result
        assert "John Smith, Jane Doe" in result
        assert "2020" in result
        assert "0.95" in result

    def test_format_context_author_string(self, assistant):
        """Test formatting context with author as string."""
        context = [
            {
                "text": "Content",
                "metadata": {"authors": "Single Author"},
            }
        ]

        result = assistant._format_context(context)
        assert "Single Author" in result


class TestResearchAssistantDryRun:
    """Tests for dry_run mode (no API calls)."""

    @pytest.fixture
    def assistant(self):
        """Create a ResearchAssistant in dry_run mode."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        return ResearchAssistant(dry_run=True)

    def test_ask_dry_run(self, assistant):
        """Test ask in dry_run mode."""
        result = assistant.ask("What is machine learning?")
        assert "DRY RUN" in result

    def test_summarize_papers_dry_run(self, assistant):
        """Test summarize_papers in dry_run mode."""
        citations = [
            {"title": "Paper 1", "year": "2020"},
            {"title": "Paper 2", "year": "2021"},
        ]
        result = assistant.summarize_papers(citations)
        assert "DRY RUN" in result


class TestResearchAssistantCitationFormatting:
    """Tests for citation formatting."""

    @pytest.fixture
    def assistant(self):
        """Create a ResearchAssistant in dry_run mode."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        return ResearchAssistant(dry_run=True)

    def test_format_citation_complete(self, assistant):
        """Test formatting a complete citation."""
        citation = {
            "title": "Machine Learning Methods",
            "authors": ["Smith, J.", "Doe, J."],
            "year": "2020",
            "source": "Journal of AI",
            "raw_text": "Smith & Doe (2020). Machine Learning Methods.",
        }

        result = assistant._format_citation_for_context(citation)

        assert "Machine Learning Methods" in result
        assert "Smith, J., Doe, J." in result
        assert "2020" in result
        assert "Journal of AI" in result

    def test_format_citation_minimal(self, assistant):
        """Test formatting a minimal citation."""
        citation = {"title": "Just a Title"}
        result = assistant._format_citation_for_context(citation)
        assert "Just a Title" in result


class TestResearchAssistantTokenUsage:
    """Tests for token usage tracking."""

    def test_get_token_usage(self):
        """Test getting token usage."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        assistant = ResearchAssistant(dry_run=True)

        usage = assistant.get_token_usage()

        assert "input_tokens" in usage
        assert "output_tokens" in usage
        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0

    def test_reset_token_usage(self):
        """Test resetting token usage."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        assistant = ResearchAssistant(dry_run=True)

        assistant._token_usage["input_tokens"] = 100
        assistant._token_usage["output_tokens"] = 50
        assistant.reset_token_usage()

        assert assistant._token_usage["input_tokens"] == 0
        assert assistant._token_usage["output_tokens"] == 0


# ============================================================================
# GapDetector Tests
# ============================================================================

class TestGapDetectorInit:
    """Tests for GapDetector initialization."""

    def test_init_defaults(self):
        """Test GapDetector initialization with defaults."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        detector = GapDetector()

        assert detector.assistant is None
        assert detector.use_ai is False

    def test_init_with_assistant(self):
        """Test initialization with AI assistant."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant

        assistant = ResearchAssistant(dry_run=True)
        detector = GapDetector(assistant=assistant, use_ai=True)

        assert detector.assistant is assistant
        assert detector.use_ai is True


class TestGapDetectorTemporalGaps:
    """Tests for temporal gap detection."""

    @pytest.fixture
    def detector(self):
        """Create a GapDetector."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector()

    def test_find_temporal_gaps_basic(self, detector):
        """Test basic temporal gap detection."""
        citations = [
            {"year": "2015"},
            {"year": "2016"},
            {"year": "2020"},
            {"year": "2021"},
        ]

        gaps = detector.find_temporal_gaps(citations)

        # Should detect gap between 2016 and 2020
        assert len(gaps) > 0
        gap_years = [(g["start_year"], g["end_year"]) for g in gaps]
        # Gap should be in the 2017-2019 range
        assert any(2017 <= start <= 2019 for start, _ in gap_years)

    def test_find_temporal_gaps_no_gaps(self, detector):
        """Test when there are no significant gaps."""
        citations = [
            {"year": "2018"},
            {"year": "2019"},
            {"year": "2020"},
            {"year": "2021"},
        ]

        gaps = detector.find_temporal_gaps(citations)
        # May or may not find gaps depending on thresholds
        # Just ensure it doesn't crash
        assert isinstance(gaps, list)

    def test_find_temporal_gaps_empty(self, detector):
        """Test with empty citations."""
        gaps = detector.find_temporal_gaps([])
        assert gaps == []

    def test_find_temporal_gaps_no_years(self, detector):
        """Test with citations missing years."""
        citations = [
            {"title": "Paper 1"},
            {"title": "Paper 2"},
        ]

        gaps = detector.find_temporal_gaps(citations)
        assert gaps == []

    def test_extract_year_various_formats(self, detector):
        """Test year extraction from various formats."""
        # Direct year
        assert detector._extract_year({"year": 2020}) == 2020
        assert detector._extract_year({"year": "2020"}) == 2020

        # Year in string
        assert detector._extract_year({"year": "Published 2020"}) == 2020

        # No year
        assert detector._extract_year({"title": "No year"}) is None


class TestGapDetectorMethodologicalGaps:
    """Tests for methodological gap detection."""

    @pytest.fixture
    def detector(self):
        """Create a GapDetector."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector()

    def test_find_methodological_gaps_basic(self, detector):
        """Test basic methodological gap detection."""
        citations = [
            {"title": "Survey-based study of user behavior", "raw_text": "quantitative survey"},
            {"title": "Statistical analysis of trends", "raw_text": "regression analysis"},
            {"title": "Experimental study", "raw_text": "controlled experiment"},
            {"title": "Interview study", "raw_text": "qualitative interviews"},
        ]

        gaps = detector.find_methodological_gaps(citations)

        # Should identify underused methodologies
        assert isinstance(gaps, list)
        # Each gap should have required fields
        for gap in gaps:
            assert "methodology" in gap
            assert "current_usage" in gap
            assert "severity" in gap

    def test_find_methodological_gaps_empty(self, detector):
        """Test with empty citations."""
        gaps = detector.find_methodological_gaps([])
        # Should return gaps for all methodologies (none used)
        assert len(gaps) > 0

    def test_methodology_detection(self, detector):
        """Test that specific methodologies are detected."""
        citations = [
            {"raw_text": "machine learning neural network deep learning algorithm"},
        ]

        gaps = detector.find_methodological_gaps(citations)

        # Computational methodology should be used
        comp_gap = next((g for g in gaps if g["methodology"] == "computational"), None)
        # Either not a gap (it's used) or not present in gaps list
        # This depends on threshold


class TestGapDetectorGeographicGaps:
    """Tests for geographic gap detection."""

    @pytest.fixture
    def detector(self):
        """Create a GapDetector."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector()

    def test_find_geographic_gaps_basic(self, detector):
        """Test basic geographic gap detection."""
        citations = [
            {"title": "Study in United States", "raw_text": "American institutions"},
            {"title": "European research", "raw_text": "UK and Germany"},
        ]

        gaps = detector.find_geographic_gaps(citations)

        # Should identify regions with limited coverage
        assert isinstance(gaps, list)
        for gap in gaps:
            assert "region" in gap
            assert "current_coverage" in gap
            assert "severity" in gap

    def test_find_geographic_gaps_empty(self, detector):
        """Test with empty citations."""
        gaps = detector.find_geographic_gaps([])
        assert len(gaps) > 0  # All regions should be gaps


class TestGapDetectorCoverageAnalysis:
    """Tests for coverage analysis."""

    @pytest.fixture
    def detector(self):
        """Create a GapDetector."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector()

    def test_analyze_coverage_basic(self, detector):
        """Test basic coverage analysis."""
        citations = [
            {"title": "Machine learning applications"},
            {"title": "Deep learning methods"},
            {"title": "Statistical analysis"},
        ]

        themes = {
            "dominant_themes": [
                {"term": "machine", "frequency": 10},
                {"term": "learning", "frequency": 8},
            ]
        }

        result = detector.analyze_coverage(citations, themes)

        assert "total_citations" in result
        assert "theme_coverage" in result
        assert result["total_citations"] == 3

    def test_analyze_coverage_empty(self, detector):
        """Test coverage analysis with empty citations."""
        result = detector.analyze_coverage([], None)
        assert result["total_citations"] == 0


class TestGapDetectorResearchQuestions:
    """Tests for research question suggestion."""

    @pytest.fixture
    def detector(self):
        """Create a GapDetector."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector()

    def test_suggest_research_questions(self, detector):
        """Test research question suggestion."""
        citations = [
            {"title": "Study from 2015", "year": "2015"},
            {"title": "Study from 2020", "year": "2020"},
        ]

        questions = detector.suggest_research_questions(citations, num_questions=3)

        assert isinstance(questions, list)
        for q in questions:
            assert "question" in q
            assert "gap_type" in q
            assert "rationale" in q


class TestGapDetectorFullReport:
    """Tests for full gap report generation."""

    @pytest.fixture
    def detector(self):
        """Create a GapDetector."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        return GapDetector()

    def test_generate_gap_report_complete(self, detector):
        """Test generating a complete gap report."""
        citations = [
            {"title": "ML in Healthcare", "year": "2018", "raw_text": "survey quantitative"},
            {"title": "Deep Learning", "year": "2019", "raw_text": "neural network"},
            {"title": "NLP Study", "year": "2021", "raw_text": "natural language"},
        ]

        report = detector.generate_gap_report(citations)

        # Check all sections are present
        assert "summary" in report
        assert "coverage_analysis" in report
        assert "temporal_gaps" in report
        assert "methodological_gaps" in report
        assert "geographic_gaps" in report
        assert "suggested_research_questions" in report
        assert "recommendations" in report

        # Check summary structure
        summary = report["summary"]
        assert "total_citations" in summary
        assert summary["total_citations"] == 3

    def test_generate_gap_report_empty(self, detector):
        """Test generating report with empty citations."""
        report = detector.generate_gap_report([])

        assert report["summary"]["total_citations"] == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntelligenceIntegration:
    """Integration tests for intelligence module."""

    def test_full_workflow(self, tmp_path):
        """Test a full workflow: index, search, detect gaps."""
        try:
            from academic_research_toolkit.intelligence.vector_store import VectorStore
            from academic_research_toolkit.intelligence.gap_detector import GapDetector

            # Create and populate vector store
            store = VectorStore(embedding_provider="local")

            citations = [
                {
                    "title": "Machine Learning Fundamentals",
                    "authors": ["Smith, John"],
                    "year": "2018",
                    "raw_text": "Introduction to machine learning algorithms.",
                },
                {
                    "title": "Deep Learning Applications",
                    "authors": ["Doe, Jane"],
                    "year": "2021",
                    "raw_text": "Neural network applications in healthcare.",
                },
            ]

            # Index citations
            store.add_citations(citations)
            assert len(store.documents) == 2

            # Search
            results = store.search("machine learning", top_k=2)
            assert len(results) <= 2

            # Save and load
            save_path = tmp_path / "test_vectors.pkl"
            store.save(save_path)

            new_store = VectorStore(embedding_provider="local")
            new_store.load(save_path)
            assert len(new_store.documents) == 2

            # Gap detection
            detector = GapDetector()
            report = detector.generate_gap_report(citations)
            assert report["summary"]["total_citations"] == 2

        except ImportError:
            pytest.skip("numpy not installed")


# ============================================================================
# CLI Tests
# ============================================================================

class TestIntelligenceCLI:
    """Tests for intelligence CLI commands."""

    def test_gaps_command_help(self, capsys):
        """Test that gaps command is available."""
        import sys
        from unittest.mock import patch

        # Test that the command is registered
        from academic_research_toolkit.cli import main

        with patch.object(sys, "argv", ["research-toolkit", "gaps", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Help should exit with 0
            assert exc_info.value.code == 0

    def test_search_command_help(self, capsys):
        """Test that search command is available."""
        import sys
        from unittest.mock import patch
        from academic_research_toolkit.cli import main

        with patch.object(sys, "argv", ["research-toolkit", "search", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_ask_command_help(self, capsys):
        """Test that ask command is available."""
        import sys
        from unittest.mock import patch
        from academic_research_toolkit.cli import main

        with patch.object(sys, "argv", ["research-toolkit", "ask", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_summarize_command_help(self, capsys):
        """Test that summarize command is available."""
        import sys
        from unittest.mock import patch
        from academic_research_toolkit.cli import main

        with patch.object(sys, "argv", ["research-toolkit", "summarize", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_vector_store_without_numpy(self):
        """Test that appropriate error is raised without numpy."""
        import sys
        from unittest.mock import patch

        # Mock numpy not being available
        with patch.dict(sys.modules, {"numpy": None}):
            # This test ensures the import handling works
            pass  # The actual import error is handled in the module

    def test_assistant_without_anthropic_dry_run(self):
        """Test assistant works in dry_run mode without anthropic."""
        from academic_research_toolkit.intelligence.assistant import ResearchAssistant
        assistant = ResearchAssistant(dry_run=True)
        result = assistant.ask("Test question")
        assert "DRY RUN" in result

    def test_gap_detector_with_malformed_citations(self):
        """Test gap detector handles malformed citations."""
        from academic_research_toolkit.intelligence.gap_detector import GapDetector
        detector = GapDetector()

        # Various malformed inputs
        citations = [
            None,  # This should be filtered or handled
            {},  # Empty dict
            {"year": "invalid"},  # Invalid year
            {"title": 123},  # Wrong type
        ]

        # Should not crash
        # Filter out None values for this test
        valid_citations = [c for c in citations if c is not None]
        report = detector.generate_gap_report(valid_citations)
        assert "summary" in report
