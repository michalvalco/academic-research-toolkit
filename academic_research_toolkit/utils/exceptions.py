"""Custom exceptions for Academic Research Toolkit."""


class ToolkitError(Exception):
    """Base exception for all toolkit errors."""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class PDFProcessingError(ToolkitError):
    """Error during PDF processing operations."""

    def __init__(self, message: str, pdf_path: str = None, details: str = None):
        self.pdf_path = pdf_path
        super().__init__(message, details)

    def __str__(self) -> str:
        base = super().__str__()
        if self.pdf_path:
            return f"{base} (file: {self.pdf_path})"
        return base


class CitationExtractionError(ToolkitError):
    """Error during citation extraction."""

    def __init__(self, message: str, source_file: str = None, details: str = None):
        self.source_file = source_file
        super().__init__(message, details)


class InvalidInputError(ToolkitError):
    """Error for invalid input files or parameters."""

    def __init__(self, message: str, input_path: str = None, expected: str = None):
        self.input_path = input_path
        self.expected = expected
        details = f"expected {expected}" if expected else None
        super().__init__(message, details)


class OutputWriteError(ToolkitError):
    """Error writing output files."""

    def __init__(self, message: str, output_path: str = None, details: str = None):
        self.output_path = output_path
        super().__init__(message, details)
