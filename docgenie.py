#!/usr/bin/env python3
# /// script
# dependencies = [
#     "google-generativeai>=0.8.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""
DocGenie - Technical Documentation Generator
Generates technical documentation for code repositories using Gemini 2.5 Pro
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict
import google.generativeai as genai
from dataclasses import dataclass
from dotenv import load_dotenv

MODEL = 'gemini-2.5-pro'

# File and directory exclusion patterns
SKIP_DIRS = {
    '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv', 'venv', 'env', 
    'build', 'dist', '.DS_Store', 'migrations', 'migration', 'db_migrations'
}

ALLOWED_EXTENSIONS = {
    # TypeScript/JavaScript
    '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',
    # .NET
    '.cs', '.fs', '.vb', '.csproj', '.fsproj', '.vbproj', '.sln',
    # Java/Kotlin
    '.java', '.kt', '.kts',
    # Configuration & Data
    '.json', '.yaml', '.yml', '.toml', '.xml', '.config',
    # Documentation & Text
    '.md', '.txt', '.rst', '.adoc',
    # Other common code files
    '.html', '.css', '.scss', '.sass', '.less',
    '.sql', '.graphql', '.gql',
    # Build & Config files (without extension)
    ''  # This allows files without extensions like Dockerfile, Makefile, etc.
}

SKIP_FILES = {
    'yarn.lock', 'package-lock.json', 'poetry.lock', 'Pipfile.lock',
    'composer.lock', 'Gemfile.lock', 'go.sum', 'cargo.lock'
}

@dataclass
class FileContent:
    """Represents a file and its content"""
    path: str
    content: str
    size: int
    loc: int  # Lines of Code count


def get_all_files_recursively(directory: Path, additional_excludes: List[str] = None) -> List[FileContent]:
    """
    Recursively get all files from the directory and return their contents.
    Skips binary files, lock files, migrations, and common non-code directories.
    """
    import fnmatch
    
    additional_excludes = additional_excludes or []
    files = []
    
    for root, dirs, filenames in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in filenames:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(directory)
            
            # Skip specific files (lock files, etc.)
            if filename in SKIP_FILES:
                continue
            
            # Only include files with allowed extensions
            if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
                
            # Skip hidden files
            if filename.startswith('.'):
                continue
            
            # Check additional exclusions (supports glob patterns)
            skip_file = False
            for exclude_pattern in additional_excludes:
                if fnmatch.fnmatch(str(relative_path), exclude_pattern) or fnmatch.fnmatch(filename, exclude_pattern):
                    skip_file = True
                    break
            if skip_file:
                continue
                
            try:
                # Try to read as text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip very large files (>1MB)
                if len(content) > 1024 * 1024:
                    print(f"Skipping large file: {file_path}")
                    continue
                
                relative_path = file_path.relative_to(directory)
                # Calculate lines of code (non-empty lines)
                loc = len([line for line in content.split('\n') if line.strip()])
                
                files.append(FileContent(
                    path=str(relative_path),
                    content=content,
                    size=len(content),
                    loc=loc
                ))
                
            except (UnicodeDecodeError, PermissionError, OSError) as e:
                print(f"Skipping file {file_path}: {e}")
                continue
    
    return files


def create_documentation_prompt(files: List[FileContent], repo_path: str, prompt_file: str) -> str:
    """Create a comprehensive prompt for documentation generation"""
    
    # Load prompt template from file
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file '{prompt_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading prompt file '{prompt_file}': {e}")
        sys.exit(1)
    
    # Create file listing with content
    files_content = []
    for file in files:
        files_content.append(f"File: {file.path}\n```\n{file.content}\n```\n")
    
    # Format the prompt template with actual values
    prompt = prompt_template.format(
        repo_path=repo_path,
        files_content=''.join(files_content)
    )
    
    return prompt


def generate_documentation_with_gemini(prompt: str, api_key: str) -> str:
    """Generate documentation using Gemini 2.5 Pro"""
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Use Gemini 2.5 Pro
    model = genai.GenerativeModel(MODEL)
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=16384,
            )
        )
        
        return response.text
        
    except Exception as e:
        print(f"Error generating documentation: {e}")
        sys.exit(1)


def main():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Generate technical documentation for a code repository using Gemini 2.5 Pro"
    )
    parser.add_argument(
        "--code", 
        required=True, 
        help="Input directory containing the code to document"
    )
    parser.add_argument(
        "--doc", 
        required=True, 
        help="Output file path for the generated documentation"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (can also be set via GEMINI_API_KEY environment variable or .env file)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview files and token count without making API call"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed file information, including largest files sorted by size"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="Additional files/directories to exclude (can be used multiple times). Supports glob patterns."
    )
    parser.add_argument(
        "--prompt",
        default="prompts/readme.txt",
        help="Path to the prompt template file (default: prompts/readme.txt)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    code_dir = Path(args.code)
    if not code_dir.exists() or not code_dir.is_dir():
        print(f"Error: Input directory '{args.code}' does not exist or is not a directory")
        sys.exit(1)
    
    # Get API key (only required if not dry-run)
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key and not args.dry_run:
        print("Error: Gemini API key is required. Set GEMINI_API_KEY in .env file, environment variable, or use --api-key")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_path = Path(args.doc)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Scanning directory: {code_dir}")
    
    # Get all files recursively
    files = get_all_files_recursively(code_dir, args.exclude)
    
    if not files:
        print("No suitable files found in the directory")
        sys.exit(1)
    
    print(f"Found {len(files)} files to analyze")
    total_size = sum(f.size for f in files)
    total_loc = sum(f.loc for f in files)
    print(f"Total content size: {total_size:,} characters")
    print(f"Total lines of code: {total_loc:,} lines")
    
    # Show detailed file information if verbose
    if args.verbose:
        print("\nFile analysis (sorted by size):")
        sorted_files = sorted(files, key=lambda f: f.size, reverse=True)
        for i, file in enumerate(sorted_files[:20], 1):  # Show top 20 largest files
            print(f"{i:2d}. {file.path:<50} {file.size:>8,} chars  {file.loc:>6,} LOC")
        if len(files) > 20:
            print(f"    ... and {len(files) - 20} more files")
        
        # Show size distribution
        large_files = [f for f in files if f.size > 10000]
        medium_files = [f for f in files if 1000 <= f.size <= 10000]
        small_files = [f for f in files if f.size < 1000]
        
        print(f"\nSize distribution:")
        print(f"  Large files (>10K chars):  {len(large_files):3d} files, {sum(f.size for f in large_files):,} chars, {sum(f.loc for f in large_files):,} LOC")
        print(f"  Medium files (1K-10K):     {len(medium_files):3d} files, {sum(f.size for f in medium_files):,} chars, {sum(f.loc for f in medium_files):,} LOC")
        print(f"  Small files (<1K chars):   {len(small_files):3d} files, {sum(f.size for f in small_files):,} chars, {sum(f.loc for f in small_files):,} LOC")
    
    # Create documentation prompt
    prompt = create_documentation_prompt(files, str(code_dir), args.prompt)
    
    # Count tokens in the prompt (if API key available)
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL)
        token_count = model.count_tokens(prompt)
        print(f"Input tokens: {token_count.total_tokens:,}")
    
    # If dry-run, just show file list and exit
    if args.dry_run:
        print("\nDry run - Files to be processed:")
        for file in files:
            print(f"  {file.path} ({file.size:,} chars, {file.loc:,} LOC)")
        print(f"\nTotal files: {len(files)}")
        print(f"Total characters: {total_size:,}")
        print(f"Total lines of code: {total_loc:,}")
        if api_key:
            print(f"Input tokens: {token_count.total_tokens:,}")
        else:
            print("Input tokens: Unable to count (no API key provided)")
        return
    
    print("Generating documentation with Gemini 2.5 Pro...")
    
    # Generate documentation
    documentation = generate_documentation_with_gemini(prompt, api_key)
    
    # Add GenAI attribution footer
    footer = """

### Generated with GenAI
This document was generated with [docgenie](https://github.com/spencermiles/docgenie) using Gemini 2.5. Some inaccuracies may be present as a result.
"""
    
    # Write documentation to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(documentation + footer)
    
    print(f"Documentation generated successfully: {output_path}")


if __name__ == "__main__":
    main()