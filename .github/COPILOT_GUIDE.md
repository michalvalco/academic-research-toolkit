# Using GitHub Copilot with Custom Instructions - Quick Start

**Setup Complete!** Your Copilot is now configured to understand your research tools project.

## What Just Happened

You now have:
1. ✅ Custom instructions that tell Copilot about your project context
2. ✅ VS Code settings optimized for Python development with Copilot
3. ✅ File associations and exclusions for cleaner workspace

## How Copilot Will Help You

### 1. Context-Aware Code Suggestions

When you start typing, Copilot will suggest code that matches your project patterns.

**Example:** Start typing a new MCP server:
```python
# Type this comment:
# MCP server for extracting metadata from PDFs

# Copilot will suggest something like:
from fastmcp import FastMCP

mcp = FastMCP("PDF Metadata Extractor")

@mcp.tool()
def extract_metadata(pdf_path: str) -> Dict:
    """Extract metadata from a PDF file."""
    # ... it knows your patterns!
```

### 2. Project-Specific Completions

Copilot understands your:
- MCP server patterns
- File processing workflows
- Academic text handling (including Slovak characters)
- Error handling style
- Documentation preferences

### 3. Smart Refactoring

Ask Copilot to help refactor code to match your patterns:
- Select code
- Open Copilot Chat (Ctrl+Shift+I)
- Ask: "Refactor this to match our MCP server pattern"

## How to Use Copilot Effectively

### In-line Suggestions
As you type, Copilot suggests completions:
- **Accept:** Press `Tab`
- **Reject:** Keep typing or press `Esc`
- **See alternatives:** `Alt+]` (next) or `Alt+[` (previous)

### Copilot Chat (Your AI Pair Programmer)

**Open Chat:** `Ctrl+Shift+I` (Windows) or `Cmd+Shift+I` (Mac)

**Best Prompts for Your Project:**

1. **Creating New Tools:**
   ```
   Create an MCP server that extracts bibliographic metadata from 
   academic PDFs. Follow our project patterns.
   ```

2. **Debugging:**
   ```
   This citation extractor is failing on Slovak author names with 
   special characters. How should I fix it?
   ```

3. **Refactoring:**
   ```
   Refactor this function to match our file processing pattern with 
   proper error handling and progress indicators.
   ```

4. **Testing:**
   ```
   Write a test for this function using real academic PDF data. 
   Include edge cases for corrupted files.
   ```

5. **Documentation:**
   ```
   Add docstrings and comments to this code following our style guide.
   ```

### Workspace Context

Copilot can see:
- ✅ Your custom instructions (`.github/copilot-instructions.md`)
- ✅ Files currently open in your editor
- ✅ The file you're currently editing
- ✅ Your project structure

**Tip:** Open relevant files before asking Copilot for help. It learns from the code you have open.

## Practical Workflows

### Starting a New Tool

1. Create a new Python file
2. Write a comment describing what you want:
   ```python
   # MCP server for analyzing themes across multiple academic papers
   # Should batch process a directory of PDFs and identify concept clusters
   ```
3. Press Enter and watch Copilot suggest the structure
4. Accept what works, modify what doesn't

### Converting Standalone Script to MCP Server

1. Open your standalone script
2. Open Copilot Chat
3. Ask: "Convert this standalone script to an MCP server following our project patterns"
4. Review the suggestions
5. Test the converted code

### Debugging with Context

1. Highlight the problematic code
2. Open Copilot Chat
3. Describe the issue with context:
   ```
   This is failing when processing academic PDFs with footnotes. 
   The regex patterns don't handle citations spread across multiple lines.
   ```
4. Copilot will suggest fixes that understand your citation formats

## Making Copilot Smarter Over Time

### Update Instructions When Patterns Change

If you develop new patterns or preferences, update `.github/copilot-instructions.md`:

```markdown
## New Pattern: API Cost Tracking

When making Claude API calls, always track and display costs:
```python
estimated_cost = len(text) / 1000000 * 3
print(f"💰 Estimated cost: ${estimated_cost:.4f}")
# ... make API call
print(f"💰 Actual cost: ${actual_cost:.4f}")
```
```

### Add Project-Specific Examples

As you build more tools, add successful patterns to the instructions:

```markdown
## Successful Patterns

### Theme Analysis Workflow
[Add your best theme analyzer code here]

### Citation Extraction for Complex Formats  
[Add the pattern that works well]
```

## Keyboard Shortcuts (VS Code)

- **Accept suggestion:** `Tab`
- **Reject suggestion:** `Esc`
- **Next suggestion:** `Alt+]`
- **Previous suggestion:** `Alt+[`
- **Open Copilot Chat:** `Ctrl+Shift+I` (Windows) or `Cmd+Shift+I` (Mac)
- **Inline chat:** `Ctrl+I` (Windows) or `Cmd+I` (Mac)

## When Copilot Gets It Wrong

Copilot isn't perfect. Here's what to do:

### 1. Give More Context
Instead of: "Fix this"
Try: "This PDF processor fails on scanned PDFs because they don't have extractable text. Add error handling that detects this and gives a helpful message."

### 2. Show Examples
```
Create a function like this one [paste example] but for extracting 
journal article citations instead of books.
```

### 3. Reference Project Files
```
Use the same pattern as pdf_processor_mcp.py to create a new MCP server 
for image extraction.
```

### 4. Break Down Complex Tasks
Instead of: "Build a complete research agent"
Try:
1. "Create the basic MCP server structure"
2. "Add PDF processing capability"
3. "Add citation extraction"
4. "Add theme analysis"
5. "Wire everything together"

## Advanced Tips

### 1. Use Copilot for Documentation
Select your code, open Copilot Chat:
```
Generate a README explaining how to use this tool, with actual command 
examples and explanation of output formats.
```

### 2. Generate Test Cases
```
Create test cases for this citation extractor that handle:
- Books with multiple authors
- Slovak author names (special characters)
- Incomplete citations (missing publisher)
- Citations spanning multiple lines
```

### 3. Explain Complex Code
Select confusing code, ask Copilot:
```
Explain this regex pattern and why it works for Slovak citations.
```

### 4. Code Reviews
Before committing, ask Copilot:
```
Review this code against our project style guide. What should be improved?
```

## Common Issues

### Copilot Not Suggesting Code
- ✓ Check VS Code status bar - is Copilot enabled?
- ✓ Reload window: `Ctrl+Shift+P` → "Reload Window"
- ✓ Check GitHub authentication
- ✓ Open relevant project files for context

### Suggestions Don't Match Project Style
- ✓ Update `.github/copilot-instructions.md`
- ✓ Open example files showing preferred patterns
- ✓ Use more specific prompts in Copilot Chat
- ✓ Reference specific patterns in your prompts

### Copilot Suggests Wrong Technology
- ✓ Update instructions to exclude unwanted suggestions
- ✓ Be explicit: "Use only the libraries listed in our project stack"

## Integration with Your Workflow

### Morning Start
1. Open VS Code in your project
2. Open the files you'll work on
3. Review yesterday's TODO comments
4. Let Copilot help complete unfinished functions

### During Development
1. Write comment describing what you need
2. Let Copilot suggest implementation
3. Review and modify suggestions
4. Test with real academic PDFs
5. Iterate

### Before Committing
1. Ask Copilot to review your code
2. Generate/update documentation
3. Add usage examples
4. Test one more time

## Next Steps

Now that Copilot is configured:

1. **Try it out:** Create a new Python file and start with a comment describing what you want to build
2. **Experiment with Chat:** Open Copilot Chat and ask it to explain parts of your existing code
3. **Refactor existing code:** Use Copilot to improve your current tools
4. **Build something new:** Let Copilot help you create the next research tool

## Questions?

The custom instructions are in `.github/copilot-instructions.md` - you can edit them anytime to improve Copilot's understanding of your project.

**Remember:** Copilot is a tool to make you faster, not to replace your thinking. You still decide what to build and how. Copilot just handles the boilerplate and suggests patterns you might have forgotten.

---

**Happy coding with your AI pair programmer!** 🚀
