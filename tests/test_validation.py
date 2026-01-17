"""Tests for validation utilities."""

import pytest
from pathlib import Path

from academic_research_toolkit.utils.validation import (
    validate_pdf_path,
    validate_output_dir,
    validate_citation_format,
    validate_markdown_path,
    validate_input_path,
    SUPPORTED_CITATION_FORMATS,
)
from academic_research_toolkit.utils.exceptions import InvalidInputError


class TestValidatePdfPath:
    """Tests for validate_pdf_path."""

    def test_nonexistent_file(self, temp_dir):
        """Test validation of nonexistent file."""
        with pytest.raises(InvalidInputError) as exc_info:
            validate_pdf_path(temp_dir / "nonexistent.pdf")
        assert "not found" in str(exc_info.value).lower()

    def test_directory_instead_of_file(self, temp_dir):
        """Test validation when path is a directory."""
        with pytest.raises(InvalidInputError) as exc_info:
            validate_pdf_path(temp_dir)
        assert "not a file" in str(exc_info.value).lower()

    def test_wrong_extension(self, temp_dir):
        """Test validation of non-PDF file."""
        txt_file = temp_dir / "file.txt"
        txt_file.write_text("content")

        with pytest.raises(InvalidInputError) as exc_info:
            validate_pdf_path(txt_file)
        assert "not a pdf" in str(exc_info.value).lower()

    def test_valid_pdf(self, temp_dir):
        """Test validation of valid PDF path."""
        pdf_file = temp_dir / "file.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")  # Minimal PDF header

        result = validate_pdf_path(pdf_file)
        assert result == pdf_file


class TestValidateOutputDir:
    """Tests for validate_output_dir."""

    def test_existing_directory(self, temp_dir):
        """Test validation of existing directory."""
        result = validate_output_dir(temp_dir)
        assert result == temp_dir

    def test_create_new_directory(self, temp_dir):
        """Test creation of new directory."""
        new_dir = temp_dir / "new_subdir"
        assert not new_dir.exists()

        result = validate_output_dir(new_dir, create=True)
        assert result == new_dir
        assert new_dir.exists()

    def test_file_instead_of_directory(self, temp_dir):
        """Test validation when path is a file."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        with pytest.raises(InvalidInputError) as exc_info:
            validate_output_dir(file_path)
        assert "not a directory" in str(exc_info.value).lower()

    def test_nonexistent_without_create(self, temp_dir):
        """Test nonexistent directory without create flag."""
        new_dir = temp_dir / "nonexistent"

        with pytest.raises(InvalidInputError) as exc_info:
            validate_output_dir(new_dir, create=False)
        assert "not found" in str(exc_info.value).lower()


class TestValidateCitationFormat:
    """Tests for validate_citation_format."""

    def test_valid_formats(self):
        """Test validation of all supported formats."""
        for fmt in SUPPORTED_CITATION_FORMATS:
            result = validate_citation_format(fmt)
            assert result == fmt.lower()

    def test_case_insensitive(self):
        """Test case-insensitive format validation."""
        assert validate_citation_format("APA") == "apa"
        assert validate_citation_format("MLA") == "mla"
        assert validate_citation_format("Chicago") == "chicago"

    def test_invalid_format(self):
        """Test validation of unsupported format."""
        with pytest.raises(InvalidInputError) as exc_info:
            validate_citation_format("harvard")
        assert "unsupported" in str(exc_info.value).lower()


class TestValidateMarkdownPath:
    """Tests for validate_markdown_path."""

    def test_nonexistent_file(self, temp_dir):
        """Test validation of nonexistent file."""
        with pytest.raises(InvalidInputError):
            validate_markdown_path(temp_dir / "nonexistent.md")

    def test_wrong_extension(self, temp_dir):
        """Test validation of non-markdown file."""
        txt_file = temp_dir / "file.txt"
        txt_file.write_text("content")

        with pytest.raises(InvalidInputError) as exc_info:
            validate_markdown_path(txt_file)
        assert "not a markdown" in str(exc_info.value).lower()

    def test_valid_markdown(self, temp_dir):
        """Test validation of valid markdown path."""
        md_file = temp_dir / "file.md"
        md_file.write_text("# Heading")

        result = validate_markdown_path(md_file)
        assert result == md_file


class TestValidateInputPath:
    """Tests for validate_input_path."""

    def test_existing_file(self, temp_dir):
        """Test validation of existing file."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        result = validate_input_path(file_path)
        assert result == file_path

    def test_existing_directory(self, temp_dir):
        """Test validation of existing directory."""
        result = validate_input_path(temp_dir)
        assert result == temp_dir

    def test_nonexistent_path(self, temp_dir):
        """Test validation of nonexistent path."""
        with pytest.raises(InvalidInputError):
            validate_input_path(temp_dir / "nonexistent")
