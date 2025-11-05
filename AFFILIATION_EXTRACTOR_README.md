# Author Affiliation Extractor

**Status:** Production Ready  
**Type:** Dual-architecture tool (Standalone CLI + MCP Server)  
**Cost:** Free (heuristic-based, no API required)

## What It Does

Extracts author names and institutional affiliations from academic PDFs using pattern matching and heuristics. Works best with standard academic paper formats where authors appear on the first page.

## Features

✅ **Heuristic-based extraction** - No API costs, runs completely offline  
✅ **Multi-language support** - Handles English and Slovak academic text  
✅ **Structured output** - Parses affiliations into department, institution, location  
✅ **Email extraction** - Automatically matches emails to authors  
✅ **Dual output formats** - JSON for machines, Markdown for humans  
✅ **Batch processing** - Process entire directories of PDFs

## Usage

### Standalone CLI

```bash
# Process a single directory
python affiliation_extractor.py --input ./pdfs --output ./authors

# Short form
python affiliation_extractor.py -i ~/papers -o ~/results
```

### MCP Server

```bash
# Start the MCP server
python mcp_servers/affiliation_extractor_mcp.py
```

Then call via MCP client:

- `extract_authors(pdf_path, output_dir)` - Process single PDF
- `extract_authors_batch(input_dir, output_dir)` - Process directory

## Output Example

**Markdown Report (`paper_authors.md`):**

```markdown
# Author Affiliations: ethics_paper.pdf

**Processed:** 2025-11-05T10:30:00
**Authors Found:** 2

---

## 1. Dr. John Smith

**Email:** j.smith@stanford.edu
**Institution:** Stanford University
**Department:** Department of Philosophy
**Location:** CA

**Full Affiliation:**
Department of Philosophy, Stanford University, Stanford, CA

*Confidence: 70.0%*
```

**JSON Output (`paper_authors.json`):**

```json
{
  "source": "ethics_paper.pdf",
  "processed": "2025-11-05T10:30:00",
  "count": 2,
  "authors": [
    {
      "name": "Dr. John Smith",
      "email": "j.smith@stanford.edu",
      "department": "Department of Philosophy",
      "institution": "Stanford University",
      "location": "CA",
      "affiliation": "Department of Philosophy, Stanford University, Stanford, CA",
      "confidence": 0.7
    }
  ]
}
```

## How It Works

### Extraction Process

1. **Extract first page** - Author info typically appears here
2. **Identify author blocks** - Split before "Abstract" or "Introduction"
3. **Pattern matching** - Detect names vs. affiliations using heuristics
4. **Parse affiliations** - Extract department, institution, location
5. **Match emails** - Link email addresses to authors
6. **Output results** - Save as JSON and Markdown

### Heuristics Used

**Author Name Detection:**

- 1-5 words with initial capitals
- May include academic titles (Dr., Prof., Ph.D., etc.)
- Excludes affiliation keywords
- Excludes location patterns (e.g., "City, State")

**Affiliation Detection:**

- Keywords: university, college, department, faculty, institute
- Slovak keywords: univerzita, fakulta, katedra, institut
- Parsed into components: department, institution, location

**Email Extraction:**

- Standard email regex pattern
- Matched to authors in order of appearance

## Supported Languages

- **English** - Full support for English academic text
- **Slovak** - Handles Slovak keywords and special characters (á, č, ď, é, í, ľ, ň, ó, ô, ŕ, š, ť, ú, ý, ž)

## Limitations

⚠️ **Heuristic-based** - Not 100% accurate, uses pattern matching  
⚠️ **First page only** - Assumes authors appear on page 1  
⚠️ **Format dependent** - Works best with standard academic formats  
⚠️ **Confidence scores** - Currently fixed at 70% for heuristic extraction

For complex formats or higher accuracy, consider using AI-powered extraction with Claude API (see `citation_extractor_ai.py` for example).

## Testing

Run validation tests:

```bash
python test_affiliation_extractor.py
```

This tests the extraction logic without requiring actual PDFs.

## Dependencies

```bash
pip install pdfplumber
```

No other dependencies required for standalone version.  
MCP version also requires: `pip install fastmcp`

## Integration with Research Library Agent

This tool can be integrated into the batch processor workflow:

```python
from affiliation_extractor import AffiliationExtractor

# Process all PDFs
extractor = AffiliationExtractor(input_dir="./pdfs", output_dir="./authors")
extractor.process_all()

# Results saved to:
# - ./authors/paper1_authors.json
# - ./authors/paper1_authors.md
# - ./authors/paper2_authors.json
# - ./authors/paper2_authors.md
```

## When to Use

**Good for:**

- Standard academic paper formats
- Batch processing large PDF collections
- Quick author identification
- Offline processing (no API costs)

**Not ideal for:**

- Scanned PDFs (no text layer)
- Non-standard layouts
- When 100% accuracy is required

For complex cases, consider AI-powered extraction with Claude API.

---

**Created:** November 5, 2025  
**Part of:** Research Tools Suite - AI App Builder
