"""Input validation utilities for Academic Research Toolkit."""

import os
from pathlib import Path
from typing import Union

from academic_research_toolkit.utils.exceptions import InvalidInputError


SUPPORTED_CITATION_FORMATS = ["apa", "mla", "chicago"]


def validate_pdf_path(path: Union[str, Path]) -> Path:
    """
    Validate that a path points to an existing PDF file.

    Args:
        path: Path to validate

    Returns:
        Validated Path object

    Raises:
        InvalidInputError: If path is invalid or not a PDF
    """
    path = Path(path)

    if not path.exists():
        raise InvalidInputError(
            f"File not found: {path}",
            input_path=str(path),
            expected="existing file",
        )

    if not path.is_file():
        raise InvalidInputError(
            f"Not a file: {path}",
            input_path=str(path),
            expected="file, not directory",
        )

    if path.suffix.lower() != ".pdf":
        raise InvalidInputError(
            f"Not a PDF file: {path}",
            input_path=str(path),
            expected=".pdf extension",
        )

    return path


def validate_pdf_directory(path: Union[str, Path]) -> Path:
    """
    Validate that a path points to a directory containing PDFs.

    Args:
        path: Directory path to validate

    Returns:
        Validated Path object

    Raises:
        InvalidInputError: If path is invalid or contains no PDFs
    """
    path = Path(path)

    if not path.exists():
        raise InvalidInputError(
            f"Directory not found: {path}",
            input_path=str(path),
            expected="existing directory",
        )

    if not path.is_dir():
        raise InvalidInputError(
            f"Not a directory: {path}",
            input_path=str(path),
            expected="directory, not file",
        )

    pdf_files = list(path.glob("*.pdf"))
    if not pdf_files:
        raise InvalidInputError(
            f"No PDF files found in: {path}",
            input_path=str(path),
            expected="directory containing .pdf files",
        )

    return path


def validate_markdown_path(path: Union[str, Path]) -> Path:
    """
    Validate that a path points to an existing markdown file.

    Args:
        path: Path to validate

    Returns:
        Validated Path object

    Raises:
        InvalidInputError: If path is invalid or not a markdown file
    """
    path = Path(path)

    if not path.exists():
        raise InvalidInputError(
            f"File not found: {path}",
            input_path=str(path),
            expected="existing file",
        )

    if not path.is_file():
        raise InvalidInputError(
            f"Not a file: {path}",
            input_path=str(path),
            expected="file, not directory",
        )

    if path.suffix.lower() != ".md":
        raise InvalidInputError(
            f"Not a markdown file: {path}",
            input_path=str(path),
            expected=".md extension",
        )

    return path


def validate_json_path(path: Union[str, Path]) -> Path:
    """
    Validate that a path points to an existing JSON file.

    Args:
        path: Path to validate

    Returns:
        Validated Path object

    Raises:
        InvalidInputError: If path is invalid or not a JSON file
    """
    path = Path(path)

    if not path.exists():
        raise InvalidInputError(
            f"File not found: {path}",
            input_path=str(path),
            expected="existing file",
        )

    if not path.is_file():
        raise InvalidInputError(
            f"Not a file: {path}",
            input_path=str(path),
            expected="file, not directory",
        )

    if path.suffix.lower() != ".json":
        raise InvalidInputError(
            f"Not a JSON file: {path}",
            input_path=str(path),
            expected=".json extension",
        )

    return path


def validate_output_dir(path: Union[str, Path], create: bool = True) -> Path:
    """
    Validate that a path is a writable directory.

    Args:
        path: Directory path to validate
        create: If True, create the directory if it doesn't exist

    Returns:
        Validated Path object

    Raises:
        InvalidInputError: If path is invalid or not writable
    """
    path = Path(path)

    if path.exists():
        if not path.is_dir():
            raise InvalidInputError(
                f"Not a directory: {path}",
                input_path=str(path),
                expected="directory, not file",
            )

        if not os.access(path, os.W_OK):
            raise InvalidInputError(
                f"Directory not writable: {path}",
                input_path=str(path),
                expected="writable directory",
            )
    else:
        if create:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise InvalidInputError(
                    f"Cannot create directory: {path}",
                    input_path=str(path),
                    expected="creatable directory path",
                )
        else:
            raise InvalidInputError(
                f"Directory not found: {path}",
                input_path=str(path),
                expected="existing directory",
            )

    return path


def validate_citation_format(format_style: str) -> str:
    """
    Validate citation format style.

    Args:
        format_style: Citation format to validate

    Returns:
        Validated format string (lowercase)

    Raises:
        InvalidInputError: If format is not supported
    """
    format_lower = format_style.lower()

    if format_lower not in SUPPORTED_CITATION_FORMATS:
        raise InvalidInputError(
            f"Unsupported citation format: {format_style}",
            expected=f"one of: {', '.join(SUPPORTED_CITATION_FORMATS)}",
        )

    return format_lower


def validate_input_path(path: Union[str, Path]) -> Path:
    """
    Validate that a path exists (file or directory).

    Args:
        path: Path to validate

    Returns:
        Validated Path object

    Raises:
        InvalidInputError: If path doesn't exist
    """
    path = Path(path)

    if not path.exists():
        raise InvalidInputError(
            f"Path not found: {path}",
            input_path=str(path),
            expected="existing file or directory",
        )

    return path
