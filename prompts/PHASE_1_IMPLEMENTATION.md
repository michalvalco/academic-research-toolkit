# Phase 1 Implementation Prompt: Foundation Strengthening

## Objective
Transform the Academic Research Toolkit from a collection of scripts into a polished, distributable Python package ready for public release as v1.0.0.

## Context
The toolkit has 5 core tools (pdf_processor, citation_extractor, theme_analyzer, affiliation_extractor, bibliography_generator) that work but lack:
- Test coverage
- Unified entry point
- Proper packaging
- Standardized error handling

## Implementation Tasks

### Task 1: Project Structure for Packaging
Create proper Python package structure:
```
academic_research_toolkit/
├── __init__.py          # Package version and exports
├── cli.py               # Unified CLI entry point
├── pdf_processor.py     # Move/refactor from root
├── citation_extractor.py
├── theme_analyzer.py
├── affiliation_extractor.py
├── bibliography_generator.py
└── utils/
    ├── __init__.py
    └── common.py        # Shared utilities
```

### Task 2: Create pyproject.toml
Modern Python packaging with:
- Package metadata (name: academic-research-toolkit)
- Dependencies: pdfplumber, pypdf, anthropic (optional)
- Dev dependencies: pytest, pytest-cov
- Entry point: `research-toolkit` command
- Python version: >=3.9

### Task 3: Unified CLI
Create `cli.py` with subcommands using argparse:
```bash
research-toolkit pdf <input> [--output]      # PDF processing
research-toolkit cite <input> [--output]     # Citation extraction
research-toolkit theme <input> [--output]    # Theme analysis
research-toolkit affil <input> [--output]    # Affiliation extraction
research-toolkit biblio <input> [--format]   # Bibliography generation
research-toolkit process <dir> [--all]       # Full pipeline
```

### Task 4: Test Suite
Create `tests/` directory with pytest tests:
```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_pdf_processor.py
├── test_citation_extractor.py
├── test_theme_analyzer.py
├── test_affiliation_extractor.py
├── test_bibliography_generator.py
└── fixtures/
    └── sample.pdf       # Test PDF file
```

Test coverage requirements:
- Test each extractor with sample inputs
- Test error handling (missing files, invalid input)
- Test output format correctness
- Minimum 70% code coverage target

### Task 5: Standardized Error Handling
Create custom exceptions in `utils/exceptions.py`:
- `ToolkitError` (base)
- `PDFProcessingError`
- `CitationExtractionError`
- `InvalidInputError`
- `OutputWriteError`

Wrap all file operations and external calls with proper try/except.

### Task 6: Input Validation
Add validation functions in `utils/validation.py`:
- `validate_pdf_path()` - Check file exists and is PDF
- `validate_output_dir()` - Check directory is writable
- `validate_citation_format()` - Check APA/MLA/Chicago

### Task 7: Requirements Files
Create:
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies (pytest, etc.)

## Success Criteria
1. `pip install -e .` works from repo root
2. `research-toolkit --help` shows all subcommands
3. `pytest` runs and passes all tests
4. Each tool is importable: `from academic_research_toolkit import pdf_processor`

## Constraints
- Maintain backward compatibility with existing standalone scripts
- Keep MCP server versions working (they import from these modules)
- Don't break existing functionality
- Use type hints throughout

## Execution Order
1. Create package structure and move files
2. Create pyproject.toml
3. Create unified CLI
4. Add error handling utilities
5. Add validation utilities
6. Create test suite
7. Verify everything works together
