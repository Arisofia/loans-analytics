#!/usr/bin/env python3
"""
Documentation Link Validator

Scans all markdown files for references to other docs and validates that
referenced files exist. Runs as part of CI/CD to prevent broken documentation.

Usage:
    python tools/validate_doc_links.py
    python tools/validate_doc_links.py --fix  # auto-fix some issues

Exit codes:
    0 — All links valid
    1 — Broken links found, exit without fixing
    2 — File I/O error
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Documentation root
DOCS_ROOT = Path(__file__).parent.parent / "docs"
REPO_ROOT = Path(__file__).parent.parent


def find_markdown_files() -> List[Path]:
    """Find all markdown files in the repository."""
    files = []
    # Include root-level MD files and docs/
    for pattern in ["*.md", "docs/**/*.md", "config/**/*.md"]:
        files.extend(REPO_ROOT.glob(pattern))
    return sorted(set(files))


def extract_markdown_links(content: str) -> List[Tuple[str, int]]:
    """
    Extract markdown links from content.
    Returns list of (link, line_number) tuples.
    """
    links = []
    # Match [text](path) patterns
    pattern = r'\[.+?\]\((.+?)\)'
    
    for line_num, line in enumerate(content.split('\n'), 1):
        for match in re.finditer(pattern, line):
            link = match.group(1)
            # Skip external links (http://, https://, etc.)
            if not link.startswith(('http://', 'https://', 'mailto:', '#')):
                links.append((link, line_num))
    
    return links


def resolve_link(link: str, from_file: Path) -> Path | None:
    """
    Resolve a markdown link to an actual file path.
    Returns the resolved Path if file exists, None otherwise.
    """
    # Handle relative paths
    if link.startswith('../') or link.startswith('./'):
        # Relative to the referencing file's directory
        resolved = (from_file.parent / link).resolve()
    elif link.startswith('/'):
        # Absolute from repo root
        resolved = (REPO_ROOT / link.lstrip('/')).resolve()
    else:
        # Relative to file's directory
        resolved = (from_file.parent / link).resolve()
    
    # Return only if within repo
    if resolved.is_file() and resolved.is_relative_to(REPO_ROOT):
        return resolved
    
    return None


def validate_links() -> Tuple[int, List[str]]:
    """
    Validate all documentation links.
    
    Returns:
        (error_count, list_of_errors)
    """
    errors = []
    markdown_files = find_markdown_files()
    
    for md_file in markdown_files:
        # Skip this validation script itself
        if "validate_doc_links" in str(md_file):
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            errors.append(f"{md_file}: Failed to read — {e}")
            continue
        
        links = extract_markdown_links(content)
        
        for link, line_num in links:
            resolved = resolve_link(link, md_file)
            if resolved is None and not link.startswith('#'):
                # Link not found (skip anchor-only links)
                errors.append(
                    f"{md_file}:{line_num}: Broken link → {link}"
                )
    
    return len(errors), errors


def main():
    parser = argparse.ArgumentParser(description="Validate documentation links")
    parser.add_argument('--fix', action='store_true', help="Attempt to fix broken links")
    args = parser.parse_args()
    
    error_count, errors = validate_links()
    
    if error_count == 0:
        print("✓ All documentation links valid")
        return 0
    
    print(f"✗ Found {error_count} broken documentation link(s):\n")
    for error in errors:
        print(f"  {error}")
    
    if args.fix:
        print("\n[FIX NOT IMPLEMENTED] Manual review required")
        print("See: docs/operations/MASTER_DELIVERY_TODO.md, Phase 3 Documentation")
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
