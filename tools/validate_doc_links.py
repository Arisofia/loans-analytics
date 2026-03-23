import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple
DOCS_ROOT = Path(__file__).parent.parent / 'docs'
REPO_ROOT = Path(__file__).parent.parent

def find_markdown_files() -> List[Path]:
    files: List[Path] = []
    for pattern in ['*.md', 'docs/**/*.md', 'config/**/*.md']:
        files.extend(REPO_ROOT.glob(pattern))
    return sorted(set(files))

def extract_markdown_links(content: str) -> List[Tuple[str, int]]:
    links = []
    pattern = '\\[.+?\\]\\((.+?)\\)'
    for line_num, line in enumerate(content.split('\n'), 1):
        for match in re.finditer(pattern, line):
            link = match.group(1)
            if not link.startswith(('http://', 'https://', 'mailto:', '#')):
                links.append((link, line_num))
    return links

def resolve_link(link: str, from_file: Path) -> Path | None:
    if link.startswith('../') or link.startswith('./'):
        resolved = (from_file.parent / link).resolve()
    elif link.startswith('/'):
        resolved = (REPO_ROOT / link.lstrip('/')).resolve()
    else:
        resolved = (from_file.parent / link).resolve()
    if resolved.is_file() and resolved.is_relative_to(REPO_ROOT):
        return resolved
    return None

def validate_links() -> Tuple[int, List[str]]:
    errors = []
    markdown_files = find_markdown_files()
    for md_file in markdown_files:
        if 'validate_doc_links' in str(md_file):
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            errors.append(f'{md_file}: Failed to read — {e}')
            continue
        links = extract_markdown_links(content)
        for link, line_num in links:
            resolved = resolve_link(link, md_file)
            if resolved is None and (not link.startswith('#')):
                errors.append(f'{md_file}:{line_num}: Broken link → {link}')
    return (len(errors), errors)

def main():
    parser = argparse.ArgumentParser(description='Validate documentation links')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix broken links')
    args = parser.parse_args()
    error_count, errors = validate_links()
    if error_count == 0:
        print('✓ All documentation links valid')
        return 0
    print(f'✗ Found {error_count} broken documentation link(s):\n')
    for error in errors:
        print(f'  {error}')
    if args.fix:
        print('\n[FIX NOT IMPLEMENTED] Manual review required')
        print('See: docs/operations/MASTER_DELIVERY_TODO.md, Phase 3 Documentation')
    return 1
if __name__ == '__main__':
    sys.exit(main())
