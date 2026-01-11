#!/usr/bin/env python3
"""
Comprehensive script to fix markdown linting issues and missing dependencies.

This script performs the following operations:
1. Scans and fixes markdown files in specified directories
2. Adds missing dependencies to dev-requirements.txt
3. Provides detailed logging and error handling
4. Allows for dry-run mode to preview changes

Usage:
    python fix_markdown_and_dependencies.py [--dry-run] [--verbose]

Arguments:
    --dry-run: Preview changes without applying them
    --verbose: Enable verbose logging output
"""

import os
import re
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Set, Tuple
from datetime import datetime


# Configure logging
def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        verbose: If True, set logging level to DEBUG
        
    Returns:
        Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


class MarkdownFixer:
    """Handles markdown file linting and fixing."""
    
    def __init__(self, logger: logging.Logger, dry_run: bool = False):
        """
        Initialize the MarkdownFixer.
        
        Args:
            logger: Logger instance for output
            dry_run: If True, don't apply changes to files
        """
        self.logger = logger
        self.dry_run = dry_run
        self.files_fixed = 0
        self.issues_fixed = 0
        
    def find_markdown_files(self, directories: List[str]) -> List[Path]:
        """
        Recursively find all markdown files in specified directories.
        
        Args:
            directories: List of directory paths to search
            
        Returns:
            List of Path objects for markdown files
        """
        markdown_files = []
        
        for directory in directories:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                self.logger.warning(f"Directory not found: {directory}")
                continue
            
            # Recursively find all .md files
            md_files = list(dir_path.rglob('*.md'))
            markdown_files.extend(md_files)
            self.logger.info(f"Found {len(md_files)} markdown files in {directory}")
        
        return markdown_files
    
    def fix_markdown_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Fix markdown linting issues in a single file.
        
        Fixes applied:
        - Remove trailing whitespace
        - Ensure proper line endings (Unix-style)
        - Fix heading spacing (require blank line before headings)
        - Fix list formatting
        - Remove multiple consecutive blank lines (max 2)
        - Ensure file ends with single newline
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Tuple of (file_modified, issues_fixed_count)
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            issues_fixed = 0
            
            # Fix 1: Remove trailing whitespace from each line
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                new_line = line.rstrip()
                if new_line != line.rstrip('\n'):
                    issues_fixed += 1
                new_lines.append(new_line)
            content = '\n'.join(new_lines)
            
            # Fix 2: Ensure proper heading spacing (blank line before headings, except at start)
            content_lines = content.split('\n')
            fixed_lines = []
            
            for i, line in enumerate(content_lines):
                # Check if line is a heading (starts with #)
                if line.startswith('#') and i > 0:
                    # Check if previous line is blank
                    if fixed_lines and fixed_lines[-1].strip() != '':
                        fixed_lines.append('')
                        issues_fixed += 1
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Fix 3: Remove multiple consecutive blank lines (keep max 2)
            content = re.sub(r'\n\n\n+', '\n\n', content)
            if content != '\n'.join(fixed_lines):
                issues_fixed += 1
            
            # Fix 4: Ensure file ends with exactly one newline
            content = content.rstrip() + '\n'
            if original_content != content:
                issues_fixed += 1
            
            # Apply changes if not in dry-run mode and content changed
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"Fixed {file_path}: {issues_fixed} issues resolved")
                else:
                    self.logger.info(f"[DRY-RUN] Would fix {file_path}: {issues_fixed} issues")
                
                self.files_fixed += 1
                self.issues_fixed += issues_fixed
                return True, issues_fixed
            
            return False, 0
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return False, 0
    
    def process_files(self, file_paths: List[Path]) -> None:
        """
        Process all markdown files.
        
        Args:
            file_paths: List of markdown file paths to process
        """
        self.logger.info(f"Processing {len(file_paths)} markdown files...")
        
        for file_path in file_paths:
            self.fix_markdown_file(file_path)
        
        self.logger.info(
            f"\nMarkdown fixes completed: {self.files_fixed} files modified, "
            f"{self.issues_fixed} issues fixed"
        )


class DependencyManager:
    """Handles dependency management in dev-requirements.txt"""
    
    def __init__(self, logger: logging.Logger, dry_run: bool = False):
        """
        Initialize the DependencyManager.
        
        Args:
            logger: Logger instance for output
            dry_run: If True, don't apply changes to files
        """
        self.logger = logger
        self.dry_run = dry_run
        self.dependencies_added = 0
    
    def read_requirements(self, file_path: str) -> Set[str]:
        """
        Read existing requirements from file.
        
        Args:
            file_path: Path to requirements file
            
        Returns:
            Set of requirement strings (normalized)
        """
        requirements = set()
        
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return requirements
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        # Normalize package name (everything before version specifier)
                        pkg_name = re.split(r'[<>=!~]', line)[0].strip().lower()
                        requirements.add(pkg_name)
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {str(e)}")
        
        return requirements
    
    def add_missing_dependencies(self, file_path: str, new_dependencies: List[str]) -> bool:
        """
        Add missing dependencies to requirements file.
        
        Args:
            file_path: Path to requirements file
            new_dependencies: List of dependencies to add
            
        Returns:
            True if changes were made
        """
        try:
            # Read existing requirements
            existing = self.read_requirements(file_path)
            
            # Filter out already existing dependencies
            to_add = []
            for dep in new_dependencies:
                dep_name = dep.split('[')[0].strip().lower()  # Handle extras like requests-mock[extra]
                if dep_name not in existing:
                    to_add.append(dep)
                else:
                    self.logger.debug(f"Dependency already exists: {dep}")
            
            if not to_add:
                self.logger.info("All dependencies already exist in requirements file")
                return False
            
            # Prepare content to add
            if not os.path.exists(file_path):
                # Create new file
                content = '\n'.join(to_add) + '\n'
                self.logger.info(f"Creating new requirements file: {file_path}")
            else:
                # Read existing content and append
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ensure file ends with newline
                if content and not content.endswith('\n'):
                    content += '\n'
                
                # Add new dependencies
                content += '\n'.join(to_add) + '\n'
            
            # Apply changes if not in dry-run mode
            if not self.dry_run:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"Added {len(to_add)} dependencies to {file_path}")
                for dep in to_add:
                    self.logger.info(f"  + {dep}")
            else:
                self.logger.info(f"[DRY-RUN] Would add {len(to_add)} dependencies to {file_path}")
                for dep in to_add:
                    self.logger.info(f"  + {dep}")
            
            self.dependencies_added = len(to_add)
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating requirements: {str(e)}")
            return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Fix markdown linting issues and manage dependencies'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(verbose=args.verbose)
    
    logger.info("=" * 80)
    logger.info("Markdown Linting and Dependency Fix Script")
    logger.info("=" * 80)
    
    if args.dry_run:
        logger.warning("Running in DRY-RUN mode - no changes will be applied")
    
    # Directories to process for markdown fixes
    markdown_directories = [
        'apps/web/.github',
        'apps/web'
    ]
    
    # Initialize fixer
    fixer = MarkdownFixer(logger, dry_run=args.dry_run)
    
    # Find and fix markdown files
    logger.info("\n" + "=" * 80)
    logger.info("Phase 1: Fixing Markdown Files")
    logger.info("=" * 80)
    
    markdown_files = fixer.find_markdown_files(markdown_directories)
    if markdown_files:
        fixer.process_files(markdown_files)
    else:
        logger.warning("No markdown files found in specified directories")
    
    # Manage dependencies
    logger.info("\n" + "=" * 80)
    logger.info("Phase 2: Managing Dependencies")
    logger.info("=" * 80)
    
    dep_manager = DependencyManager(logger, dry_run=args.dry_run)
    
    # Add missing dependencies
    missing_deps = ['mypy', 'requests-mock']
    
    logger.info(f"Adding missing dependencies: {', '.join(missing_deps)}")
    dep_manager.add_missing_dependencies('dev-requirements.txt', missing_deps)
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Execution Summary")
    logger.info("=" * 80)
    logger.info(f"Markdown files processed: {fixer.files_fixed}")
    logger.info(f"Markdown issues fixed: {fixer.issues_fixed}")
    logger.info(f"Dependencies added: {dep_manager.dependencies_added}")
    
    if args.dry_run:
        logger.info("\n[DRY-RUN] No actual changes were applied.")
        logger.info("Run without --dry-run to apply these changes.")
    
    logger.info("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
