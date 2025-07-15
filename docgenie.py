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
    '.sh', '.py',
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


@dataclass
class IgnoredFile:
    """Represents an ignored file and the reason it was ignored"""
    path: str
    size: int
    reason: str


def get_all_files_recursively(directory: Path, additional_excludes: List[str] = None, additional_includes: List[str] = None, track_ignored: bool = False) -> tuple[List[FileContent], List[IgnoredFile]]:
    """
    Recursively get all files from the directory and return their contents.
    Skips binary files, lock files, migrations, and common non-code directories.
    If additional_includes is provided, only files matching those patterns will be processed (whitelist mode).
    Returns tuple of (included_files, ignored_files) if track_ignored is True, else (included_files, [])
    """
    import fnmatch
    
    additional_excludes = additional_excludes or []
    additional_includes = additional_includes or []
    files = []
    ignored_files_info = []
    
    # Determine if we're in whitelist mode (includes specified)
    whitelist_mode = bool(additional_includes)
    
    for root, dirs, filenames in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in filenames:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(directory)
            
            # Skip specific files (lock files, etc.)
            if filename in SKIP_FILES:
                if track_ignored:
                    try:
                        file_size = file_path.stat().st_size
                    except (OSError, PermissionError):
                        file_size = 0
                    ignored_files_info.append(IgnoredFile(
                        path=str(relative_path),
                        size=file_size,
                        reason="Lock file or dependency file"
                    ))
                continue
            
            # Check whitelist mode - if includes are specified, file must match at least one include pattern
            if whitelist_mode:
                include_matched = False
                matched_include_pattern = None
                for include_pattern in additional_includes:
                    if fnmatch.fnmatch(str(relative_path), include_pattern) or fnmatch.fnmatch(filename, include_pattern):
                        include_matched = True
                        matched_include_pattern = include_pattern
                        break
                
                if not include_matched:
                    if track_ignored:
                        try:
                            file_size = file_path.stat().st_size
                        except (OSError, PermissionError):
                            file_size = 0
                        ignored_files_info.append(IgnoredFile(
                            path=str(relative_path),
                            size=file_size,
                            reason="Not matching any include pattern (whitelist mode)"
                        ))
                    continue
            else:
                # Original logic: Only include files with allowed extensions (when not in whitelist mode)
                if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    if track_ignored:
                        try:
                            file_size = file_path.stat().st_size
                        except (OSError, PermissionError):
                            file_size = 0
                        ignored_files_info.append(IgnoredFile(
                            path=str(relative_path),
                            size=file_size,
                            reason=f"Unsupported extension: {file_path.suffix or '(no extension)'}"
                        ))
                    continue
                
            # Skip hidden files
            if filename.startswith('.'):
                if track_ignored:
                    try:
                        file_size = file_path.stat().st_size
                    except (OSError, PermissionError):
                        file_size = 0
                    ignored_files_info.append(IgnoredFile(
                        path=str(relative_path),
                        size=file_size,
                        reason="Hidden file"
                    ))
                continue
            
            # Check additional exclusions (supports glob patterns)
            skip_file = False
            matched_pattern = None
            for exclude_pattern in additional_excludes:
                if fnmatch.fnmatch(str(relative_path), exclude_pattern) or fnmatch.fnmatch(filename, exclude_pattern):
                    matched_pattern = exclude_pattern
                    skip_file = True
                    break
            if skip_file:
                if track_ignored:
                    try:
                        file_size = file_path.stat().st_size
                    except (OSError, PermissionError):
                        file_size = 0
                    ignored_files_info.append(IgnoredFile(
                        path=str(relative_path),
                        size=file_size,
                        reason=f"Excluded by pattern: {matched_pattern}"
                    ))
                continue
                
            try:
                # Try to read as text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Skip very large files (>1MB)
                if len(content) > 1024 * 1024:
                    print(f"Skipping large file: {file_path}")
                    if track_ignored:
                        ignored_files_info.append(IgnoredFile(
                            path=str(relative_path),
                            size=len(content),
                            reason="File too large (>1MB)"
                        ))
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
                if track_ignored:
                    try:
                        file_size = file_path.stat().st_size
                    except (OSError, PermissionError):
                        file_size = 0
                    ignored_files_info.append(IgnoredFile(
                        path=str(relative_path),
                        size=file_size,
                        reason=f"Read error: {type(e).__name__}"
                    ))
                continue
    
    return files, ignored_files_info


def create_documentation_prompt(files: List[FileContent], repo_path: str, prompt_file: str) -> str:
    """Create a comprehensive prompt for documentation generation"""
    
    # Resolve prompt file path - if not absolute, make it relative to script location
    if not Path(prompt_file).is_absolute():
        script_dir = Path(__file__).parent
        prompt_file_path = script_dir / prompt_file
    else:
        prompt_file_path = Path(prompt_file)
    
    print(f"Looking for prompt file: {prompt_file_path}")
    
    # Load prompt template from file
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file '{prompt_file_path}' not found")
        print(f"Script location: {Path(__file__).parent}")
        print(f"Current working directory: {Path.cwd()}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading prompt file '{prompt_file_path}': {e}")
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


def generate_documentation_with_gemini(prompt: str, api_key: str, response_prefix: str = None, system_instruction: str = None) -> str:
    """Generate documentation using Gemini 2.5 Pro"""
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Use Gemini 2.5 Pro with optional system instruction
    if system_instruction:
        model = genai.GenerativeModel(MODEL, system_instruction=system_instruction)
    else:
        model = genai.GenerativeModel(MODEL)
    
    # Add response prefix instruction to prompt if specified
    if response_prefix:
        prompt = f"{prompt}\n\nIMPORTANT: Start your response with exactly this character or text: '{response_prefix}'"
    
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
        "--include",
        action="append", 
        help="Files/directories to include as whitelist (can be used multiple times). Supports glob patterns. If specified, only matching files will be processed."
    )
    parser.add_argument(
        "--prompt",
        default="prompts/readme.txt",
        help="Path to the prompt template file (default: prompts/readme.txt, relative to script location)"
    )
    parser.add_argument(
        "--response-prefix",
        help="Specific character or text that the LLM should start its response with"
    )
    parser.add_argument(
        "--system-instruction",
        help="System instruction to control the model's behavior and response format"
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
    
    # Show filtering mode
    if args.include:
        print(f"Whitelist mode: Only including files matching {len(args.include)} include pattern(s)")
        for pattern in args.include:
            print(f"  Include: {pattern}")
    
    if args.exclude:
        print(f"Excluding files matching {len(args.exclude)} exclude pattern(s)")
        for pattern in args.exclude:
            print(f"  Exclude: {pattern}")
    
    # Get all files recursively
    files, ignored_files_info = get_all_files_recursively(code_dir, args.exclude, args.include, track_ignored=True)
    
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
    
        # Show ignored files information
        if ignored_files_info:
            print(f"\nIgnored files analysis:")
            print(f"Total ignored files: {len(ignored_files_info)}")
            
            # Show largest ignored files
            sorted_ignored = sorted(ignored_files_info, key=lambda f: f.size, reverse=True)
            print(f"\nLargest ignored files:")
            for i, ignored_file in enumerate(sorted_ignored[:10], 1):  # Show top 10 ignored files
                size_str = f"{ignored_file.size:,}" if ignored_file.size > 0 else "unknown"
                print(f"{i:2d}. {ignored_file.path:<50} {size_str:>12} bytes - {ignored_file.reason}")
            
            if len(ignored_files_info) > 10:
                print(f"    ... and {len(ignored_files_info) - 10} more ignored files")
            
            # Show ignored files by reason
            from collections import defaultdict
            reasons_count = defaultdict(int)
            reasons_size = defaultdict(int)
            for ignored_file in ignored_files_info:
                reasons_count[ignored_file.reason] += 1
                reasons_size[ignored_file.reason] += ignored_file.size
            
            print(f"\nIgnored files by reason:")
            for reason in sorted(reasons_count.keys()):
                total_size = reasons_size[reason]
                size_str = f"{total_size:,}" if total_size > 0 else "unknown"
                print(f"  {reason:<40} {reasons_count[reason]:3d} files, {size_str:>12} bytes")
    
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
        
        if ignored_files_info:
            print(f"\nIgnored files: {len(ignored_files_info)}")
            if args.verbose:
                print("Top 5 largest ignored files:")
                sorted_ignored = sorted(ignored_files_info, key=lambda f: f.size, reverse=True)
                for i, ignored_file in enumerate(sorted_ignored[:5], 1):
                    size_str = f"{ignored_file.size:,}" if ignored_file.size > 0 else "unknown"
                    print(f"  {i}. {ignored_file.path} ({size_str} bytes) - {ignored_file.reason}")
        
        if api_key:
            print(f"Input tokens: {token_count.total_tokens:,}")
        else:
            print("Input tokens: Unable to count (no API key provided)")
        return
    
    print("Generating documentation with Gemini 2.5 Pro...")
    
    # Generate documentation
    documentation = generate_documentation_with_gemini(prompt, api_key, args.response_prefix, args.system_instruction)
    
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