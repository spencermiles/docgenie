# DocGenie 🧞‍♂️

Generate comprehensive technical documentation for your code repositories using Google's Gemini 2.5 Pro.

## Overview

DocGenie is a Python CLI tool that analyzes your entire codebase and generates detailed technical documentation. It recursively scans all files in a directory, sends them to Gemini 2.5 Pro, and produces comprehensive markdown documentation covering architecture, setup, usage, and more.

## Features

- 🔍 **Recursive file scanning** - Analyzes all code files in your repository
- 🎯 **Whitelist & Blacklist filtering** - Include only specific files or exclude unwanted ones with glob patterns
- 🤖 **AI-powered documentation** - Uses Gemini 2.5 Pro for intelligent analysis
- 📝 **Comprehensive output** - Generates structured documentation with multiple sections
- ⚡ **Easy setup** - Works directly with `uv` for dependency management
- 🔒 **Secure** - Uses `.env` files for API key management
- 🎛️ **Response control** - Control LLM output format and starting text

## Quick Start

1. **Clone or download** the `docgenie.py` script

2. **Set up your API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

3. **Run DocGenie**:
   ```bash
   uv run docgenie.py --code ./your-repo --doc ./output.md
   ```

## Installation

### Option 1: Direct execution with uv (Recommended)
No installation required! The script includes dependency declarations that `uv` will automatically handle.

### Option 2: Traditional pip install
```bash
pip install -r requirements.txt
python docgenie.py --code ./repo --doc ./output.md
```

## Usage

### Basic Usage
```bash
uv run docgenie.py --code <input-directory> --doc <output-file>
```

### Examples

#### Basic Usage
```bash
# Generate docs for current directory
uv run docgenie.py --code . --doc README.md

# Generate docs for a specific project
uv run docgenie.py --code ./my-project --doc ./my-project/DOCS.md

# Use a specific API key
uv run docgenie.py --code ./repo --doc ./docs.md --api-key your-api-key-here
```

#### Preview and Analysis
```bash
# Preview what files will be processed (no API call)
uv run docgenie.py --code ./repo --doc ./output.md --dry-run

# Show detailed file analysis with size breakdown
uv run docgenie.py --code ./repo --doc ./output.md --verbose --dry-run

# Check token usage before generating docs
uv run docgenie.py --code ./repo --doc ./output.md --verbose
```

#### Custom Inclusions (Whitelist)
```bash
# Only process Python files
uv run docgenie.py --code ./repo --doc ./docs.md --include "*.py"

# Only process specific file types  
uv run docgenie.py --code ./repo --doc ./docs.md --include "*.ts" --include "*.js" --include "*.json"

# Include files from specific directories only
uv run docgenie.py --code ./repo --doc ./docs.md --include "src/**/*.ts" --include "lib/**/*.js"

# Focus on documentation files
uv run docgenie.py --code ./repo --doc ./docs.md --include "*.md" --include "*.txt" --include "*.rst"

# Combine whitelist with exclusions - include all TypeScript but exclude tests
uv run docgenie.py --code ./repo --doc ./docs.md --include "*.ts" --exclude "*.test.ts" --exclude "*.spec.ts"
```

#### Custom Exclusions
```bash
# Exclude test files
uv run docgenie.py --code ./repo --doc ./docs.md --exclude "*.test.*" --exclude "*.spec.*"

# Exclude multiple directories
uv run docgenie.py --code ./repo --doc ./docs.md --exclude "tests/*" --exclude "legacy/*" --exclude "temp/*"

# Exclude generated code and build artifacts
uv run docgenie.py --code ./repo --doc ./docs.md --exclude "**/generated/*" --exclude "*.generated.*" --exclude "build/*"

# Complex exclusion patterns
uv run docgenie.py --code ./repo --doc ./docs.md \
  --exclude "**/*.test.ts" \
  --exclude "**/mocks/*" \
  --exclude "src/legacy/**" \
  --exclude "*.backup.*"
```

#### Response Control
```bash
# Control the first character/text of the LLM response
uv run docgenie.py --code ./repo --doc ./docs.md --response-prefix "#"

# Use system instructions to control behavior
uv run docgenie.py --code ./repo --doc ./docs.md --system-instruction "You are a technical writer. Always start with a project title."

# Combine response controls
uv run docgenie.py --code ./repo --doc ./docs.md \
  --response-prefix "## " \
  --system-instruction "Write concise, developer-focused documentation"
```

### Arguments

- `--code` (required): Input directory containing the code to document
- `--doc` (required): Output file path for the generated documentation  
- `--api-key` (optional): Gemini API key (overrides environment variables)
- `--dry-run` (optional): Preview files and token count without making API call
- `-v, --verbose` (optional): Show detailed file information and size analysis
- `--include` (optional): Files/directories to include as whitelist (supports glob patterns, can be used multiple times). If specified, only matching files will be processed
- `--exclude` (optional): Additional files/directories to exclude (supports glob patterns, can be used multiple times)
- `--prompt` (optional): Path to custom prompt template file (default: prompts/readme.txt)
- `--response-prefix` (optional): Specific character or text that the LLM should start its response with
- `--system-instruction` (optional): System instruction to control the model's behavior and response format

## Configuration

### API Key Setup

DocGenie needs a Google Gemini API key. You can provide it in three ways:

1. **`.env` file** (recommended):
   ```bash
   cp .env.example .env
   # Edit .env:
   GEMINI_API_KEY=your_actual_api_key_here
   ```

2. **Environment variable**:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

3. **Command line argument**:
   ```bash
   uv run docgenie.py --api-key your_api_key_here --code ./repo --doc ./docs.md
   ```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

## Generated Documentation

DocGenie generates comprehensive documentation including:

1. **Project Overview** - Purpose and main functionality
2. **Architecture** - High-level design and patterns (with mermaid diagrams)
3. **Directory Structure** - Project organization explanation
4. **Key Components** - Main modules, classes, and functions
5. **Dependencies** - External libraries and frameworks
6. **Setup and Installation** - How to get started
7. **Usage Examples** - How to use main features
8. **API Documentation** - Interfaces and endpoints (if applicable)
9. **Configuration** - Settings and environment variables
10. **Development** - Contributing, building, testing, and deployment

## File Processing

DocGenie supports two modes for processing your codebase:

### Default Mode (Extension-Based Filtering)
When no `--include` patterns are specified, DocGenie uses a predefined list of allowed file extensions:

#### Included File Types
- **TypeScript/JavaScript**: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`
- **.NET**: `.cs`, `.fs`, `.vb`, `.csproj`, `.fsproj`, `.vbproj`, `.sln`
- **Python/Shell**: `.py`, `.sh`
- **Configuration**: `.json`, `.yaml`, `.yml`, `.toml`, `.xml`, `.config`
- **Documentation**: `.md`, `.txt`, `.rst`, `.adoc`
- **Web/Styling**: `.html`, `.css`, `.scss`, `.sass`, `.less`
- **Database/API**: `.sql`, `.graphql`, `.gql`
- **Build files**: `Dockerfile`, `Makefile`, etc. (files without extensions)

### Whitelist Mode (Custom Includes)
When `--include` patterns are specified, **only** files matching those patterns are processed, regardless of extension:

```bash
# Only process specific file types
--include "*.py" --include "*.md"

# Include files from specific directories
--include "src/**/*.ts" --include "docs/**/*"

# Complex patterns
--include "**/*.{js,ts,json}" --include "README.*"
```

### Always Excluded
Regardless of mode, these are automatically excluded:
- **Lock files**: `yarn.lock`, `package-lock.json`, `poetry.lock`, `Pipfile.lock`, `composer.lock`, `Gemfile.lock`, `go.sum`, `cargo.lock`
- **Directories**: `node_modules`, `__pycache__`, `.git`, `.venv`, `build`, `dist`, `migrations`
- **Large files**: Files over 1MB
- **Hidden files**: Files starting with `.`
- **Binary files**: Images, executables, archives, etc.

### Custom Exclusions
Use the `--exclude` flag with glob patterns for additional filtering (works in both modes):

```bash
# Exclude patterns
--exclude "*.test.*"        # All test files
--exclude "**/generated/*"  # Generated code directories
--exclude "legacy/**"       # Entire legacy directory tree
--exclude "src/temp/*"      # Temporary files in src
```

### Processing Priority
1. **Always excluded** files are skipped first
2. **Include patterns** are checked (if specified) - file must match at least one
3. **Extension filtering** is applied (default mode only)
4. **Exclude patterns** are checked - file must not match any
5. **File size and readability** checks are performed

## Requirements

- Python 3.7+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Google Gemini API key

### Dependencies
- `google-generativeai>=0.8.0`
- `python-dotenv>=1.0.0`

## Troubleshooting

### Common Issues

**ModuleNotFoundError**: Make sure you're using `uv run` or have installed dependencies:
```bash
pip install -r requirements.txt
```

**API Key Error**: Verify your API key is set correctly in `.env` or environment variables.

**Empty Output**: Check that your input directory contains files with supported extensions. Use `--verbose --dry-run` to see what files are being processed.

**Too Many Tokens**: Use `--exclude` to filter out test files, generated code, or large data files. Use `--verbose` to see which files are largest.

**Large Repository**: For very large codebases, consider documenting specific subdirectories.

## License

MIT License - feel free to use and modify as needed.

## Contributing

This is a simple single-file tool. To contribute:
1. Fork the repository
2. Make your changes to `docgenie.py`
3. Test with various codebases
4. Submit a pull request

---

*Generated documentation quality depends on your codebase structure and the provided context. For best results, ensure your code is well-organized with clear naming conventions.*