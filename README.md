# Academic Research Toolkit

**A suite of Python tools for processing, analyzing, and extracting insights from academic research papers.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

The Academic Research Toolkit is a collection of standalone Python scripts and MCP (Model Context Protocol) servers designed to automate common research workflows. Extract text from PDFs, parse citations, identify themes, and analyze author affiliations—all with a focus on academic use cases.

**Status:** Phase 3 Complete - Production Ready  
**Architecture:** Dual-architecture (Standalone CLI + MCP Servers)

## Features

### 🔄 Dual Architecture

Each tool exists in two forms:

- **Standalone CLI** - Direct command-line usage for one-off tasks
- **MCP Server** - Programmatic access for agent orchestration

### 📄 Core Tools

#### 1. PDF Processor

Extracts text and metadata from academic PDFs into structured markdown.

```bash
python pdf_processor.py --input ./pdfs --output ./results
```

**Features:**

- Batch processing of PDF directories
- Metadata extraction (title, author, date, page count)
- Clean text extraction with formatting preservation
- Outputs: Markdown + JSON metadata

#### 2. Citation Extractor

Identifies and parses citations from academic texts using regex patterns.

```bash
python citation_extractor.py --input ./extracted --output ./citations
```

**Features:**

- Multi-format support (books, articles, chapters, online sources)
- English & Slovak language support
- Structured JSON output with citation metadata
- AI-powered fallback for complex formats (via `citation_extractor_ai.py`)

#### 3. Theme Analyzer

Analyzes themes, concepts, and term co-occurrences across research corpus.

```bash
python theme_analyzer.py --input ./extracted --output ./themes
```

**Features:**

- Keyword frequency analysis
- Term co-occurrence mapping
- Context extraction for key terms
- Cross-document theme identification
- Research gap detection

#### 4. Affiliation Extractor

Extracts author names and institutional affiliations from PDFs.

```bash
python affiliation_extractor.py --input ./pdfs --output ./authors
```

**Features:**

- Heuristic-based extraction (no API costs)
- Parses affiliations into: department, institution, location
- Email extraction and matching
- Multi-language support (English, Slovak)

### 🤖 Batch Processing Agent

The **Research Library Agent** orchestrates all tools to process entire PDF libraries:

```bash
python mcp_servers/research_library_agent.py --input ./pdfs --output ./results
```

**What it does:**

1. Extracts text from all PDFs (free)
2. Extracts citations using Claude API (paid)
3. Analyzes themes across corpus (free)
4. Generates comprehensive briefing (paid)

**Outputs:** 4 structured directories (`1_extracted_text/`, `2_citations/`, `3_themes/`, `4_briefings/`)

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/michalvalco/academic-research-toolkit.git
cd academic-research-toolkit
```

2. Create a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:

```bash
pip install pdfplumber pypdf anthropic fastmcp
```

### Optional: API Setup (for AI-powered features)

For citation extraction and synthesis using Claude API:

```bash
# Set environment variable
export ANTHROPIC_API_KEY='sk-ant-your-key-here'  # Linux/Mac
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"  # PowerShell
```

Get your API key at: <https://console.anthropic.com/>

## Quick Start

### Process a Single PDF

```bash
python pdf_processor.py --input ./sample.pdf --output ./output
```

### Extract Citations from Processed Text

```bash
python citation_extractor.py --input ./output --output ./citations
```

### Analyze Themes Across Multiple Papers

```bash
python theme_analyzer.py --input ./output --output ./themes
```

### Extract Author Affiliations

```bash
python affiliation_extractor.py --input ./pdfs --output ./authors
```

### Process Entire Research Library (with API)

```bash
python mcp_servers/research_library_agent.py --input ./pdfs --output ./complete_analysis
```

## Directory Structure

```text
academic-research-toolkit/
├── pdf_processor.py              # Extract text from PDFs
├── citation_extractor.py         # Parse citations (regex)
├── theme_analyzer.py             # Analyze themes and concepts
├── affiliation_extractor.py      # Extract author affiliations
├── mcp_servers/                  # MCP server versions
│   ├── pdf_processor_mcp.py
│   ├── citation_extractor_mcp.py
│   ├── citation_extractor_ai.py  # AI-powered citation extraction
│   ├── theme_analyzer_mcp.py
│   ├── affiliation_extractor_mcp.py
│   ├── research_library_agent.py # Batch processor orchestrator
│   └── research_agent.py         # Demo agent workflow
├── .github/
│   └── copilot-instructions.md   # AI agent development guide
└── README.md
```

## MCP Server Usage

Start an MCP server:

```bash
python mcp_servers/pdf_processor_mcp.py
```

Then call via MCP client or agent. Each MCP server exposes tools like:

- `process_pdf(pdf_path, output_dir)` - Process single file
- `process_pdf_directory(input_dir, output_dir)` - Batch processing

## Use Cases

**Academic Researchers:**

- Process large PDF libraries quickly
- Extract and organize citations automatically
- Identify research themes and gaps
- Track author networks

**PhD Students:**

- Literature review automation
- Citation management
- Theme mapping for dissertation chapters
- Author affiliation tracking

**Research Institutions:**

- Corpus analysis across departments
- Institutional publication tracking
- Research trend identification
- Collaboration network analysis

## Cost Breakdown

**Free Components (No API):**

- ✅ PDF text extraction
- ✅ Citation extraction (regex)
- ✅ Theme analysis
- ✅ Affiliation extraction

**AI Components (Claude API):**

- 💰 AI-powered citation extraction: ~$0.01-0.03 per paper
- 💰 Research briefing synthesis: ~$0.05 one-time
- **Total for 50 papers:** ~$0.55-1.55

## Language Support

- **English** - Full support
- **Slovak** - Academic keywords and special characters (á, č, ď, é, í, ľ, ň, ó, ô, ŕ, š, ť, ú, ý, ž)

## Documentation

- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) - Comprehensive development guide for AI agents
- [`AFFILIATION_EXTRACTOR_README.md`](AFFILIATION_EXTRACTOR_README.md) - Affiliation extractor details
- [`mcp_servers/agent_setup_guide.md`](mcp_servers/agent_setup_guide.md) - Batch processor setup
- [`mcp_servers/PHASE_3_STATUS.md`](mcp_servers/PHASE_3_STATUS.md) - Current development status

## Limitations

⚠️ **PDF Requirements:** Text-based PDFs only (not scanned images)  
⚠️ **Heuristic Tools:** Citation/affiliation extractors use pattern matching (~70% accuracy)  
⚠️ **Format Dependency:** Works best with standard academic paper formats  
⚠️ **Language:** Optimized for English and Slovak academic text

For complex formats or higher accuracy, use AI-powered versions with Claude API.

## Development

### Running Tests

```bash
# Test individual tools
python pdf_processor.py --input ./test_data --output ./test_output
```

### Code Style

This project follows pragmatic Python patterns:

- Type hints for function signatures
- Descriptive variable names
- `pathlib.Path` for file operations
- Graceful error handling

See [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for complete development guidelines.

## Contributing

Contributions welcome! This toolkit is designed for academic research workflows. If you have ideas for:

- New extraction patterns
- Additional languages
- Performance improvements
- New analysis tools

Please open an issue or submit a pull request.

## License

MIT License - See LICENSE file for details

## Author

**Michal Valčo**  
GitHub: [@michalvalco](https://github.com/michalvalco)

## Acknowledgments

Built with:

- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction
- [Anthropic Claude](https://www.anthropic.com/) - AI-powered analysis
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework

---

**Status:** Production Ready | **Version:** 1.0.0 | **Last Updated:** November 2025

---

## Development Roadmap

### Phase 1: Standalone Tools (Current)

Build each tool as independent Python script:

- Works with local files
- Takes command-line arguments
- Outputs to files
- Fully tested on real data

### Phase 2: MCP Server Conversion

Refactor each tool as Model Context Protocol server:

- Callable by Claude Agent SDK
- Standardized input/output
- Error handling
- Logging and monitoring

### Phase 3: Agent Integration

Build Research Assistant Agent using our MCP servers:

- Combines all tools into unified workflow
- Maintains context across operations
- Autonomous operation
- Production-ready

---

**Last Updated:** November 5, 2025
