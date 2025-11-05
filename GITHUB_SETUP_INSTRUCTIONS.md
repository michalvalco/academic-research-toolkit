# GitHub Repository Setup Instructions

## Repository Details

**Name:** `academic-research-toolkit`  
**Owner:** `michalvalco`  
**URL:** <https://github.com/michalvalco/academic-research-toolkit>

## Steps to Complete Setup

### ✅ Already Done

1. ✅ Git repository initialized
2. ✅ Initial commit created (28 files, 7,431 lines)
3. ✅ Main branch renamed to 'main'
4. ✅ Comprehensive README created and committed

### 🔄 Next Steps (Do These Now)

#### Step 1: Create Repository on GitHub

1. Go to: <https://github.com/new>
2. Configure:
   - Repository name: **`academic-research-toolkit`**
   - Description: **`A suite of Python tools for processing, analyzing, and extracting insights from academic research papers`**
   - Visibility: **Public** (recommended for open-source) or **Private**
   - ❌ **DO NOT check** "Initialize this repository with:"
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license
   - (We already have all of these locally)
3. Click **"Create repository"**

#### Step 2: Connect Local Repository to GitHub

After creating the repo on GitHub, run these commands in PowerShell:

```powershell
# Navigate to your project (if not already there)
cd "C:\Users\valco\OneDrive\Documents\AI Tools\AI Agents\AI App Builder"

# Add the remote repository
git remote add origin https://github.com/michalvalco/academic-research-toolkit.git

# Verify the remote was added
git remote -v

# Push your code to GitHub
git push -u origin main
```

You may be prompted to authenticate with GitHub. Options:

- **GitHub Personal Access Token** (recommended)
- **SSH key**
- **GitHub Desktop**

#### Step 3: Verify Upload

After pushing, visit:
<https://github.com/michalvalco/academic-research-toolkit>

You should see:

- ✅ All 28 files
- ✅ Comprehensive README with badges and documentation
- ✅ `.github/copilot-instructions.md` for AI agent development
- ✅ All Python tools (standalone + MCP versions)

## Optional: Add Topics/Tags

On GitHub, add these topics to make your repo more discoverable:

```text
academic-research
pdf-processing
citation-extraction
python
mcp-server
research-tools
nlp
text-analysis
```

## Optional: Create a License

If you want to add an open-source license:

1. On GitHub, click "Add file" → "Create new file"
2. Type filename: `LICENSE`
3. Click "Choose a license template"
4. Select **MIT License** (recommended for open-source tools)
5. Fill in your name: **Michal Valčo**
6. Commit the file

## Future: Clone to Other Machines

To work on this repo from another computer:

```bash
git clone https://github.com/michalvalco/academic-research-toolkit.git
cd academic-research-toolkit
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install pdfplumber pypdf anthropic fastmcp
```

## Troubleshooting

### If push fails due to authentication

#### Option 1: Personal Access Token (PAT)

1. Go to: <https://github.com/settings/tokens>
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (all), `workflow`
4. Generate and copy the token
5. When prompted for password, use the PAT instead

#### Option 2: GitHub CLI

```powershell
# Install GitHub CLI from https://cli.github.com/
gh auth login
# Follow the prompts
```

#### Option 3: SSH Key

```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add to GitHub: https://github.com/settings/keys
```

### If remote already exists

```bash
# Check current remotes
git remote -v

# Remove existing origin
git remote remove origin

# Add the correct one
git remote add origin https://github.com/michalvalco/academic-research-toolkit.git
```

---

**Ready?** Go to <https://github.com/new> and create your repository now! 🚀
