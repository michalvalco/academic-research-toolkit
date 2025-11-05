# Research Tools Suite

**Status:** Active Development  
**Phase:** Building foundational components  
**Next:** Convert to MCP servers for Agent SDK integration

---

## What We're Building

A suite of document processing tools for academic research that will eventually become components of an intelligent research agent.

### Current Components

**1. PDF Processor** (In Progress)
- Extracts text from academic PDFs
- Captures metadata (title, author, date)
- Outputs structured markdown
- Handles multiple files in batch

**2. Citation Extractor** (Planned)
- Identifies citations in extracted text
- Extracts bibliographic information
- Links citations across documents

**3. Theme Analyzer** (Planned)
- Identifies key themes and concepts
- Maps conceptual relationships
- Generates research opportunity insights

---

## Project Structure

```
research-tools/
├── src/              # Source code
├── tests/            # Test files and test data
├── data/             # Sample/test documents
├── output/           # Generated results
└── README.md         # This file
```

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

## Usage (When Complete)

```bash
# Standalone mode
python src/pdf_processor.py --input ./papers --output ./extracted

# Agent mode (future)
research-agent analyze --topic "AI Ethics" --papers ./papers
```

---

## Technical Stack

- **Python 3.9+**
- **PDF Processing:** pdfplumber, PyPDF2
- **Text Analysis:** spaCy, NLTK
- **Agent Framework:** claude-agent-sdk
- **Protocol:** Model Context Protocol (MCP)

---

## Testing Strategy

Each tool is tested with actual academic papers from your research library. Success means the tool produces output you'd actually use in your work.

---

**Last Updated:** November 4, 2025