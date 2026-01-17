"""Tests for custom exceptions."""

import pytest
from academic_research_toolkit.utils.exceptions import (
    ToolkitError,
    PDFProcessingError,
    CitationExtractionError,
    InvalidInputError,
    OutputWriteError,
)


class TestToolkitError:
    """Tests for base ToolkitError."""

    def test_basic_message(self):
        """Test error with basic message."""
        error = ToolkitError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.details is None

    def test_with_details(self):
        """Test error with details."""
        error = ToolkitError("Failed", details="File not found")
        assert str(error) == "Failed: File not found"
        assert error.details == "File not found"


class TestPDFProcessingError:
    """Tests for PDFProcessingError."""

    def test_basic_error(self):
        """Test basic PDF error."""
        error = PDFProcessingError("Could not open PDF")
        assert "Could not open PDF" in str(error)

    def test_with_pdf_path(self):
        """Test error with PDF path."""
        error = PDFProcessingError(
            "Could not open PDF",
            pdf_path="/path/to/file.pdf",
        )
        assert "file.pdf" in str(error)

    def test_with_all_fields(self):
        """Test error with all fields."""
        error = PDFProcessingError(
            "Could not open PDF",
            pdf_path="/path/to/file.pdf",
            details="Encrypted file",
        )
        assert "Could not open PDF" in str(error)
        assert "file.pdf" in str(error)


class TestInvalidInputError:
    """Tests for InvalidInputError."""

    def test_basic_error(self):
        """Test basic invalid input error."""
        error = InvalidInputError("Invalid file")
        assert "Invalid file" in str(error)

    def test_with_expected(self):
        """Test error with expected value."""
        error = InvalidInputError(
            "Invalid format",
            expected="PDF file",
        )
        assert "Invalid format" in str(error)
        assert "PDF file" in str(error)


class TestCitationExtractionError:
    """Tests for CitationExtractionError."""

    def test_basic_error(self):
        """Test basic citation error."""
        error = CitationExtractionError("Failed to parse")
        assert error.message == "Failed to parse"

    def test_with_source_file(self):
        """Test error with source file."""
        error = CitationExtractionError(
            "Failed to parse",
            source_file="paper.md",
        )
        assert error.source_file == "paper.md"


class TestOutputWriteError:
    """Tests for OutputWriteError."""

    def test_basic_error(self):
        """Test basic output error."""
        error = OutputWriteError("Cannot write file")
        assert error.message == "Cannot write file"

    def test_with_output_path(self):
        """Test error with output path."""
        error = OutputWriteError(
            "Cannot write file",
            output_path="/output/file.txt",
        )
        assert error.output_path == "/output/file.txt"
