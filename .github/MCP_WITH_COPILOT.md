# Configuring MCP Servers with GitHub Copilot

## Overview

You've built three MCP servers:
1. `pdf_processor_mcp.py` - Extracts text from PDFs
2. `citation_extractor_mcp.py` - Identifies citations
3. `theme_analyzer_mcp.py` - Analyzes themes

This guide shows how to make Copilot aware of them and help you build on top of them.

## What Are MCP Servers?

**Model Context Protocol (MCP) servers** are tools that AI agents can call to perform specific tasks. Think of them as APIs that your Research Assistant Agent uses to process academic papers.

Your MCP servers convert your standalone Python scripts into callable services that an AI agent orchestrates.

## Making Copilot Aware of Your MCP Servers

### 1. Keep MCP Files Open

When working on agent code that uses these servers, open them in VS Code:

```
Open Files:
├── pdf_processor_mcp.py
├── citation_extractor_mcp.py  
├── theme_analyzer_mcp.py
└── research_agent.py (your new file)
```

Copilot learns from open files, so it will understand your MCP tool signatures.

### 2. Reference MCP Patterns in Prompts

When asking Copilot for help:

**Good:**
```
Create code that calls our PDF Processor MCP server to extract text 
from all PDFs in a directory. Use the process_pdf_directory tool.
```

**Better:**
```
Create code that calls our PDF Processor MCP server following this pattern:
[paste example MCP call from existing code]
```

**Best:**
```
Looking at pdf_processor_mcp.py, create code that:
1. Calls process_pdf_directory on input folder
2. Checks results for success/failure
3. Passes extracted markdown files to citation extractor
4. Returns combined results
```

### 3. Document MCP Tool Signatures

Add this section to your custom instructions if you want Copilot to always know about your tools:

```markdown
## Available MCP Servers

### PDF Processor (`pdf_processor_mcp.py`)

**Tools:**
- `process_pdf(pdf_path: str, output_dir: str) -> Dict`
  - Returns: `{success: bool, markdown_path: str, json_path: str, stats: dict}`
  
- `process_pdf_directory(input_dir: str, output_dir: str) -> Dict`
  - Returns: `{success: bool, processed: list, failed: list, stats: dict}`

### Citation Extractor (`citation_extractor_mcp.py`)

**Tools:**
- `extract_citations(markdown_file: str, output_dir: str) -> Dict`
  - Returns: `{success: bool, citations: list, stats: dict, json_path: str}`
  
- `extract_citations_batch(input_dir: str, output_dir: str) -> Dict`
  - Returns: `{success: bool, processed: list, failed: list, stats: dict}`

### Theme Analyzer (`theme_analyzer_mcp.py`)

**Tools:**
- `analyze_themes(markdown_file: str, output_dir: str) -> Dict`
  - Returns: `{success: bool, insights: dict, json_path: str}`
  
- `analyze_themes_batch(input_dir: str, output_dir: str) -> Dict`
  - Returns: `{success: bool, processed: list, combined_insights: dict}`
```

## Using Copilot to Build Agent Code

### Example Workflow

**You want to:** Create an agent that processes PDFs and extracts citations.

**Step 1:** Open your MCP server files
```
├── pdf_processor_mcp.py (opened)
├── citation_extractor_mcp.py (opened)
└── new_agent.py (creating)
```

**Step 2:** In `new_agent.py`, write a comment:
```python
# Create a research agent that:
# 1. Processes all PDFs in input directory using PDF Processor MCP
# 2. Extracts citations from each processed file using Citation Extractor MCP
# 3. Returns summary of all citations found
# Use the process_pdf_directory and extract_citations_batch tools
```

**Step 3:** Press Enter and watch Copilot suggest the implementation

**Step 4:** Review, test, iterate

### Ask Copilot Chat

Open Copilot Chat and try:

```
I have three MCP servers for academic research:
- pdf_processor_mcp.py (extracts text from PDFs)
- citation_extractor_mcp.py (finds citations)  
- theme_analyzer_mcp.py (analyzes themes)

Create a workflow that uses all three to generate a research briefing:
1. Process PDFs
2. Extract citations
3. Analyze themes
4. Combine results into markdown report

Use the batch processing tools from each server.
```

## Common MCP Patterns

### Calling Single MCP Tool
```python
# Import the MCP server's functions directly
from pdf_processor_mcp import process_pdf

result = process_pdf(
    pdf_path='/path/to/paper.pdf',
    output_dir='/tmp/extracted'
)

if result['success']:
    print(f"✓ Extracted to: {result['markdown_path']}")
else:
    print(f"✗ Error: {result['error']}")
```

### Chaining MCP Tools
```python
# Step 1: Process PDF
pdf_result = process_pdf(pdf_path, '/tmp/work')

if pdf_result['success']:
    # Step 2: Extract citations from the extracted markdown
    citations_result = extract_citations(
        markdown_file=pdf_result['markdown_path'],
        output_dir='/tmp/citations'
    )
    
    if citations_result['success']:
        print(f"Found {len(citations_result['citations'])} citations")
```

### Batch Processing Pipeline
```python
# Process entire directory through all three tools
input_dir = '/path/to/pdfs'
work_dir = '/tmp/research_work'

# Step 1: Extract all PDFs
pdf_results = process_pdf_directory(input_dir, f'{work_dir}/extracted')

# Step 2: Extract citations from all
citation_results = extract_citations_batch(
    f'{work_dir}/extracted',
    f'{work_dir}/citations'
)

# Step 3: Analyze themes across corpus
theme_results = analyze_themes_batch(
    f'{work_dir}/extracted',
    f'{work_dir}/themes'
)

# Step 4: Combine into briefing
generate_briefing(pdf_results, citation_results, theme_results)
```

## Ask Copilot to Generate Variations

### Example Prompts

**Create error-handling wrapper:**
```
Create a function that calls our MCP tools with proper error handling.
It should retry on transient failures and log errors.
```

**Add progress tracking:**
```
Wrap our MCP batch calls to show progress indicators:
[1/50] Processing paper1.pdf...
    ✓ Extracted (45,230 chars)
[2/50] Processing paper2.pdf...
```

**Parallel processing:**
```
Modify this to process multiple PDFs in parallel using ThreadPoolExecutor.
Use our MCP process_pdf tool for each file.
```

**Cost tracking:**
```
Add cost tracking to this workflow. Each citation extraction costs ~$0.02.
Show running total and final cost.
```

## MCP Server Development with Copilot

### Creating New MCP Server

**Prompt:**
```
Create a new MCP server for extracting image figures from academic PDFs.

Follow the pattern from pdf_processor_mcp.py:
- Use FastMCP
- Two tools: process_single and process_batch
- Return format: {success, data, error}
- Use pdfplumber for PDF access
- Save images to output directory
```

### Extending Existing Server

**Prompt:**
```
Add a new tool to citation_extractor_mcp.py that validates citations 
against a known bibliography. Return validation report with:
- Matched citations
- Unmatched citations  
- Possible matches (fuzzy)
```

### Testing MCP Servers

**Prompt:**
```
Create a test suite for pdf_processor_mcp.py that:
- Tests both single file and batch processing
- Uses sample academic PDFs
- Verifies output format
- Checks error handling
```

## Integration Patterns

### With Claude Agent SDK (Future)
```python
from claude_agent_sdk import Agent

agent = Agent(
    mcp_servers={
        'pdf': 'path/to/pdf_processor_mcp.py',
        'citations': 'path/to/citation_extractor_mcp.py',
        'themes': 'path/to/theme_analyzer_mcp.py'
    }
)

# Agent autonomously decides when to use which tool
response = agent.run("Analyze all papers on AI ethics")
```

### Manual Orchestration (Current)
```python
# You orchestrate the tools programmatically
def research_pipeline(pdf_directory):
    # Step 1: Extract
    pdfs = process_pdf_directory(pdf_directory, '/tmp/extracted')
    
    # Step 2: Analyze
    citations = extract_citations_batch('/tmp/extracted', '/tmp/cites')
    themes = analyze_themes_batch('/tmp/extracted', '/tmp/themes')
    
    # Step 3: Synthesize
    return create_briefing(pdfs, citations, themes)
```

## Troubleshooting with Copilot

### MCP Server Not Working

**Prompt:**
```
This MCP server call is failing with [error message].
The server definition is in [filename].
Help me debug and fix it.
```

### Understanding MCP Returns

**Prompt:**
```
Explain the structure of the return value from citation_extractor_mcp.
What fields are guaranteed? What's optional? Show examples.
```

### Converting Standalone to MCP

**Prompt:**
```
I have this standalone function [paste code].
Convert it to an MCP tool that follows our server pattern.
```

## Best Practices

### 1. Keep MCP Servers Simple
Each tool should do one thing well. Don't create monolithic servers.

### 2. Consistent Return Format
Always return `{success: bool, data: any, error: str}` from MCP tools.

### 3. Document Tool Signatures
Include clear docstrings with parameter types and return format.

### 4. Test Independently
Each MCP server should be testable without the agent.

### 5. Version Your MCP Servers
As you improve them, maintain backward compatibility or version properly.

## Next Steps

1. **Try the examples** - Copy a pattern and ask Copilot to adapt it
2. **Build a pipeline** - Chain your three MCP servers together
3. **Add error handling** - Let Copilot help make it robust
4. **Test with real data** - Use your actual academic PDFs
5. **Document patterns** - Add successful patterns to custom instructions

## Questions for Copilot Chat

- "Show me how to call all three MCP servers in sequence"
- "Create error handling for this MCP pipeline"
- "Add logging to track what each MCP tool is doing"
- "Generate a summary report from MCP tool outputs"
- "Create a CLI that wraps these MCP calls"

---

**Remember:** Copilot knows about your MCP servers when the files are open. Keep them visible when building on top of them!
