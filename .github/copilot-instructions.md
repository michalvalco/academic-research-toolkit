# GitHub Copilot Custom Instructions - Research Tools Suite

## Project Context

This is an academic research processing toolkit that extracts, analyzes, and synthesizes information from academic PDFs. The tools are being developed for:
- Personal research workflow automation
- Academic course content development  
- Future SaaS productization for scholars

**Current Phase:** Phase 3 complete - MCP servers operational, batch processing agent functional, ready for API-powered full automation.

## Architecture Overview

This project uses a **dual-architecture pattern**: standalone Python scripts AND MCP servers exposing the same functionality.

### Root-Level Scripts (Direct CLI Usage)
- `pdf_processor.py` - Extract text/metadata from PDFs → markdown files
- `citation_extractor.py` - Regex-based citation parsing (no API needed)
- `theme_analyzer.py` - Identify themes, concepts, co-occurrences across corpus

**Usage:** `python pdf_processor.py --input ./pdfs --output ./results`

### MCP Servers (`mcp_servers/` directory)
MCP versions of the same tools for programmatic/agent access:
- `pdf_processor_mcp.py` - Same functionality, exposed via `@mcp.tool()` decorators
- `citation_extractor_mcp.py` - MCP-wrapped citation extraction
- `theme_analyzer_mcp.py` - MCP-wrapped theme analysis with batch processing

**Additional Agent Components:**
- `citation_extractor_ai.py` - AI-powered citation extraction using Claude API (for complex formats)
- `research_library_agent.py` - **Primary batch processor** orchestrating all tools on entire PDF directories
- `research_agent.py` - Demonstration/template for agent workflows

### Key Architectural Principle
Each tool exists in TWO forms:
1. **Standalone CLI** (root `*.py`) - For direct human use, testing, one-off processing
2. **MCP Server** (`mcp_servers/*_mcp.py`) - For agent orchestration and programmatic access

When modifying functionality, update BOTH versions to maintain parity.

## Domain Expertise

The developer has deep expertise in:
- AI Ethics (especially Christian Personalism approaches)
- Theology and philosophy (Neo-Aristotelianism, narrative theory)
- Industry 4.0 and technology ethics
- Academic research methodology
- Content creation and affiliate marketing

## Technical Stack

**Primary Languages:**
- Python 3.9+ (main development language)
- Markdown (documentation and output format)

**Key Libraries:**
- `pdfplumber` - PDF text extraction (primary method)
- `pypdf` / `PyPDF2` - PDF metadata extraction
- `anthropic` - Claude API integration for AI-powered analysis
- `fastmcp` - MCP server framework for Agent SDK
- Standard library: `re`, `json`, `pathlib`, `argparse`, `dataclasses`, `Counter` (from collections)

**Development Environment:**
- Claude Desktop as primary development interface
- Windows system (`c:\Users\valco\...`) with Linux container (`/home/claude`, `/mnt/project`)
- PowerShell (`pwsh.exe`) is default shell - use PowerShell syntax for terminal commands
- Cross-platform paths: use `pathlib.Path` for compatibility

## Critical Workflows

### Running the Batch Processor (Primary Use Case)
```bash
# Process entire directory of PDFs with full AI analysis
python mcp_servers/research_library_agent.py --input ./pdfs --output ./results

# Requires: ANTHROPIC_API_KEY environment variable set
# Cost: ~$0.01-0.03 per paper for citations, ~$0.05 for final synthesis
```

**What it does:**
1. Extracts text from all PDFs (free, no API)
2. Extracts citations using Claude API (paid)
3. Analyzes themes across corpus (free)
4. Generates comprehensive briefing (paid)

Outputs 4 directories: `1_extracted_text/`, `2_citations/`, `3_themes/`, `4_briefings/`

### Testing Individual Tools
```bash
# Test PDF extraction
python pdf_processor.py --input ./test_pdfs --output ./test_output

# Test theme analysis (on already-extracted markdown)
python theme_analyzer.py --input ./test_output --output ./themes

# Check MCP server functionality
python mcp_servers/pdf_processor_mcp.py
# Then manually invoke with MCP client or agent
```

### Setting Up API Access
```bash
# PowerShell syntax (Windows default shell)
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# For persistent setup, add to PowerShell profile:
# notepad $PROFILE
# Add: $env:ANTHROPIC_API_KEY = "sk-ant-..."
```

Get API key: https://console.anthropic.com/ (requires account with credits)

## Code Style Preferences

### General Philosophy
- **Pragmatic over perfect** - Working code beats elegant abstraction
- **Iterative development** - Build small, test often, improve continuously  
- **Real data from the start** - Test with actual academic PDFs, not toy examples
- **Modular design** - Components should be reusable across projects

### Python Specifics
- Type hints for function signatures (but not exhaustive)
- Docstrings that explain *why*, not just *what*
- Descriptive variable names (no cryptic abbreviations)
- Comments for complex logic, none for obvious code
- Prefer `pathlib.Path` over string path manipulation
- Use `dataclasses` for structured data
- Error handling that fails gracefully with useful messages

### Code Structure Pattern
```python
"""
Module docstring explaining purpose and usage examples.
"""

import standard_library
import third_party
from local_modules import components

# Constants at top
CONSTANT_VALUE = 100

class ProcessorName:
    """What this does and when to use it."""
    
    def __init__(self, required_params):
        self.param = required_params
    
    def public_method(self) -> ReturnType:
        """User-facing method with clear return type."""
        pass
    
    def _private_helper(self):
        """Internal logic, prefixed with underscore."""
        pass

if __name__ == '__main__':
    # CLI argument parsing with argparse
    # Clear usage examples in help text
```

## Project-Specific Patterns

### Dual-Architecture Implementation Pattern
When adding a new tool, create BOTH versions:

**1. Standalone CLI version (root directory):**
```python
# tool_name.py
import argparse
from pathlib import Path

class ToolProcessor:
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self):
        # Core logic here
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tool description')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o', required=True)
    args = parser.parse_args()
    
    processor = ToolProcessor(args.input, args.output)
    processor.process()
```

**2. MCP Server version (mcp_servers/ directory):**
```python
# mcp_servers/tool_name_mcp.py
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("Tool Name")

@mcp.tool()
def process_item(input_path: str, output_dir: str = "/tmp/output") -> Dict:
    """
    Process a single item with this tool.
    
    Returns dict with: success (bool), data (any), error (str|None)
    """
    try:
        # Reuse logic from standalone version or copy
        result = do_processing(input_path, output_dir)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run()
```

### MCP Server Structure
When creating MCP servers, follow this pattern:
```python
from fastmcp import FastMCP

mcp = FastMCP("Server Name")

@mcp.tool()
def tool_name(required_param: str, optional_param: str = "default") -> Dict:
    """
    Brief description of what this tool does.
    
    Args:
        required_param: What this parameter is for
        optional_param: What this does (default behavior)
    
    Returns:
        Dictionary with structure:
        - success: bool
        - data: relevant output
        - error: error message if failed
    """
    try:
        # Implementation
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run()
```

### File Processing Pattern
```python
def process_file(filepath: Path, output_dir: Path) -> Dict:
    """Process a single file and return results."""
    
    print(f"Processing: {filepath.name}")
    
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process content
        result = do_processing(content)
        
        # Save output
        output_path = output_dir / f"{filepath.stem}_result.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"  ✓ Success: {output_path}")
        return {"success": True, "output_path": str(output_path)}
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return {"success": False, "error": str(e)}
```

### Citation Extraction Patterns
When working with citations, expect these formats:
- Books: `Author. Year. Title. Location: Publisher.`
- Articles: `Author. Year. "Title." Journal Volume(Issue): Pages.`
- Mixed languages (English and Slovak common)
- Footnotes interspersed with main text
- PDFs with formatting issues

### Academic Text Processing
- Always handle Slovak characters: á, č, ď, é, í, ľ, ň, ó, ô, ŕ, š, ť, ú, ý, ž
- Skip metadata sections in extracted markdown (look for `## Extracted Text`)
- Preserve scholarly formatting and citations
- Be case-insensitive in searches but preserve original case in output

### Agent Orchestration Pattern (See `research_library_agent.py`)
The batch processor demonstrates multi-stage workflows:
```python
class ResearchLibraryAgent:
    def run(self):
        # Phase 1: Free processing (PDF extraction)
        extracted_files = self._extract_all_pdfs(pdf_files)
        
        # Phase 2: AI processing (citations, uses API)
        citations = self._extract_all_citations(extracted_files)
        
        # Phase 3: Free analysis (themes)
        themes = self._analyze_corpus_themes(extracted_files)
        
        # Phase 4: AI synthesis (final briefing, uses API)
        briefing = self._generate_corpus_briefing(extracted_files, citations, themes)
```

**Key principles:**
- Separate free operations from API-based operations
- Show cost estimates before API calls
- Track API usage and display total cost
- Save intermediate results at each phase
- Use structured output directories (`1_extracted_text/`, `2_citations/`, etc.)

## Output Format Preferences

### Markdown Reports
```markdown
# Main Title

**Metadata:**
- Field: Value
- Generated: YYYY-MM-DD HH:MM:SS

## Section Heading

Content with proper paragraphs.

### Subsection

- Bullet points when listing items
- Not for flowing prose

**Key Terms** in bold for emphasis.

---

Clear section breaks with horizontal rules.
```

### JSON Output
```json
{
  "metadata": {
    "source": "filename.pdf",
    "processed": "2025-11-05T10:30:00",
    "version": "1.0"
  },
  "results": {
    "structured_data": [],
    "statistics": {}
  },
  "success": true,
  "error": null
}
```

### Console Output
```python
print("=" * 70)
print("TOOL NAME")
print("=" * 70)
print()
print(f"Processing: {filename}")
print(f"  → Action being performed...")
print(f"  ✓ Success! Details here")
print(f"  ✗ Failed: Error message")
print()
print("📊 Summary:")
print(f"  Total: {count}")
print(f"  ✓ Successful: {success}")
print(f"  ✗ Failed: {failed}")
```

## Testing Approach

- Test with REAL academic PDFs from the start
- Include error cases (corrupted PDFs, missing metadata)
- Validate on mixed-language documents (English + Slovak)
- Check output readability and usability
- Ensure tools can be run multiple times safely (idempotent when possible)

## Documentation Standards

### Code Comments
```python
# Purpose: Extract citations from academic text
# Challenge: Footnotes mixed with main text, multiple citation styles
# Approach: Use regex patterns for known formats, AI for ambiguous cases

# This handles Slovak authors where names may have special characters
authors = re.split(r'\s+(?:and|a)\s+', author_string)  # 'a' is Slovak 'and'
```

### README Structure
Each tool should have:
1. What it does (one sentence)
2. Why it exists (the problem it solves)
3. Usage example (actual command)
4. Input requirements
5. Output format
6. Known limitations

## API Usage Guidelines

### Claude API Calls
- Use temperature=0 for factual extraction
- Provide clear, structured prompts
- Always estimate cost before API calls
- Show cost to user after each operation
- Handle rate limits gracefully
- Cache responses when appropriate

### Error Messages
Make them actionable:
```python
# Bad
raise Exception("Failed")

# Good  
raise Exception(
    f"Failed to extract text from {pdf_path}. "
    "Check if PDF is text-based (not scanned image). "
    "Try: pdfplumber.open('file.pdf').pages[0].extract_text()"
)
```

## Development Workflow

1. **Start Simple:** Single file, basic functionality
2. **Add Batch:** Process directories
3. **Error Handling:** Graceful failures
4. **Output Formats:** Multiple useful formats (JSON, markdown, etc.)
5. **MCP Conversion:** Wrap as MCP server for agent use
6. **Documentation:** Usage guide with real examples
7. **Testing:** Validate on actual research corpus

## Common Patterns to Suggest

### Argument Parser Template
```python
parser = argparse.ArgumentParser(
    description='Brief description',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  script.py --input ./data --output ./results
  script.py -i ~/pdfs -o ~/analysis
    """
)
parser.add_argument('--input', '-i', required=True, help='Input path')
parser.add_argument('--output', '-o', required=True, help='Output path')
```

### Progress Indicators
```python
for i, item in enumerate(items, 1):
    print(f"[{i}/{len(items)}] Processing: {item.name}...")
    # Do work
    print(f"    ✓ Complete")
```

### Safe File Writing
```python
output_path = output_dir / filename
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

## What NOT to Suggest

- ❌ Django/Flask web frameworks (not needed yet)
- ❌ Complex ORM or database systems (files are fine)
- ❌ Excessive abstraction (factories, abstract base classes, etc.)
- ❌ Over-engineered solutions (YAGNI principle)
- ❌ Generic tutorials (use actual project context)
- ❌ Corporate jargon in documentation

## Key Principles

1. **Build for actual use** - This isn't a coding exercise, it's building production tools
2. **Fail gracefully** - Show useful error messages, don't just crash
3. **Make it obvious** - Code should be self-explanatory; avoid cleverness
4. **Test with real data** - Academic PDFs, actual citations, real use cases
5. **Document for future self** - Assume you'll forget how this works in 6 months

## Current Project Status

**Completed:**
- ✅ Standalone PDF processor
- ✅ Citation extractor (regex-based)
- ✅ Theme analyzer
- ✅ All three converted to MCP servers
- ✅ Research Library Batch Processor (processes entire PDF directories)
- ✅ AI-powered citation extraction for complex formats

**Ready for Use:**
- `research_library_agent.py` - Fully functional batch processor
  - Requires `ANTHROPIC_API_KEY` environment variable
  - Processes entire corpus in single command
  - Outputs to 4 structured directories

**Next Steps:**
- Testing on 50+ paper corpus
- Cost optimization (caching, deduplication)
- Documentation for non-technical users
- Productization planning

## Questions to Ask Before Coding

1. Is this solving the actual problem or adding complexity?
2. Can this be tested with real data immediately?
3. Will the error message help me fix the issue?
4. Can I run this again tomorrow without remembering all the details?
5. Is this the simplest thing that could possibly work?

---

**Remember:** The goal isn't perfect code. The goal is functional tools that solve real problems in academic research processing.
