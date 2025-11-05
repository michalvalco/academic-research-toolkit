# GitHub Copilot - Quick Reference Card

## Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|--------------|-----|
| Accept suggestion | `Tab` | `Tab` |
| Reject suggestion | `Esc` | `Esc` |
| Next suggestion | `Alt+]` | `Option+]` |
| Previous suggestion | `Alt+[` | `Option+[` |
| Open Copilot Chat | `Ctrl+Shift+I` | `Cmd+Shift+I` |
| Inline chat | `Ctrl+I` | `Cmd+I` |
| Toggle Copilot | `Ctrl+Shift+P` → "Copilot" | `Cmd+Shift+P` → "Copilot" |

## Best Prompts for Research Tools

### Creating New Tools
```
Create an MCP server for [purpose] that follows our project patterns.
Use pdfplumber for PDF extraction and include proper error handling.
```

### Debugging
```
This [component] fails when [scenario]. 
The issue is [specific error].
Fix it following our error handling pattern.
```

### Refactoring
```
Refactor this to match our [pattern name] pattern from the custom instructions.
Maintain the same functionality but improve code quality.
```

### Documentation
```
Generate comprehensive docstrings for this function.
Include parameter descriptions, return value, and usage example.
```

### Testing
```
Create test cases for this function that handle:
- [edge case 1]
- [edge case 2]
- [error scenario]
Use real academic PDF data patterns.
```

## Common Patterns to Request

### MCP Server Structure
```
Create an MCP server following our standard pattern with:
- FastMCP initialization
- @mcp.tool() decorated functions
- Proper return format (success, data, error)
- Error handling
```

### File Processing
```
Create a file processor that:
- Uses pathlib.Path
- Includes progress indicators
- Has proper error handling
- Returns structured results
```

### Batch Processing
```
Add batch processing capability that:
- Processes directories
- Shows progress for each file
- Tracks successes and failures
- Generates summary statistics
```

### API Integration
```
Add Claude API integration that:
- Estimates cost before calling
- Shows actual cost after calling
- Handles rate limits
- Returns structured JSON
```

## Quick Fixes

### Fix Slovak Character Handling
```
Update this regex to handle Slovak characters:
á, č, ď, é, í, ľ, ň, ó, ô, ŕ, š, ť, ú, ý, ž
```

### Add Error Handling
```
Add comprehensive error handling that:
- Catches specific exceptions
- Provides actionable error messages
- Returns error dict instead of raising
- Logs errors for debugging
```

### Improve Console Output
```
Update console output to match our style:
- Use ═ for major sections
- Use ─ for minor sections
- Use ✓ for success, ✗ for failure
- Include emoji indicators (📊 💰 📄)
```

## Context Tips

### Before Asking Copilot
1. Open relevant files (Copilot sees open files)
2. Select code you're asking about
3. Include specific error messages in prompts
4. Reference patterns from custom instructions

### For Better Suggestions
1. Write descriptive comments first
2. Use meaningful variable names
3. Follow project naming conventions
4. Keep functions focused and small

### When Stuck
1. Ask Copilot to explain existing code
2. Request step-by-step breakdown
3. Ask for alternative approaches
4. Request debugging guidance

## Custom Instructions Location

Your project context is defined in:
```
.github/copilot-instructions.md
```

Update this file when:
- You develop new patterns
- Requirements change
- You discover better approaches
- New tools are added to stack

## Copilot Chat Commands

In Copilot Chat, try:

**Explain Code:**
```
/explain [selected code]
```

**Fix Problems:**
```
/fix [describe issue]
```

**Generate Tests:**
```
/tests for [function name]
```

**Optimize:**
```
/optimize this code for [performance/readability]
```

## Project-Specific Reminders

### Always Include
- Type hints for function parameters
- Docstrings with return format
- Error handling with useful messages
- Progress indicators for batch operations
- Cost estimates for API calls

### Never Use
- Generic variable names (x, y, temp)
- Bare except clauses
- Hard-coded paths
- Magical numbers without comments
- Complex regex without explanation

### Preferred Libraries
- `pathlib.Path` (not string paths)
- `dataclasses` (for structured data)
- `argparse` (for CLI)
- `pdfplumber` (for PDFs)
- `anthropic` (for Claude API)
- `fastmcp` (for MCP servers)

## Troubleshooting

### Copilot Not Working
1. Check status bar (bottom right)
2. Verify GitHub authentication
3. Reload VS Code window
4. Check internet connection
5. Review VS Code output panel

### Wrong Suggestions
1. Update custom instructions
2. Open reference files
3. Be more specific in prompts
4. Use explicit examples
5. Reference project patterns by name

### Need Help
1. Read `.github/COPILOT_GUIDE.md`
2. Check `.github/copilot-instructions.md`
3. Ask Copilot Chat directly
4. Review GitHub Copilot documentation

---

**Print this out or keep it handy while coding!** 📋
