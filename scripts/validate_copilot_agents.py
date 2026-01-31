#!/usr/bin/env python3
"""
Validate GitHub Copilot agent configurations in .github/agents/

This script checks that all *.md files in .github/agents/ have:
1. Valid YAML frontmatter
2. Required fields (name, description, target, tools)
3. Proper formatting and structure
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter from markdown content.
    
    Args:
        content: Full markdown file content
        
    Returns:
        Tuple of (parsed YAML dict, remaining markdown content)
        
    Raises:
        ValueError: If frontmatter is malformed
    """
    if not content.startswith('---'):
        raise ValueError("No YAML frontmatter found (must start with '---')")
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Malformed YAML frontmatter (must be enclosed by '---')")
    
    yaml_content = parts[1]
    markdown_content = parts[2]
    
    try:
        config = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax: {e}")
    
    if not isinstance(config, dict):
        raise ValueError("YAML frontmatter must be a dictionary")
    
    return config, markdown_content


def validate_agent_config(config: Dict, filename: str) -> List[str]:
    """Validate agent configuration has required fields.
    
    Args:
        config: Parsed YAML configuration
        filename: Name of the file being validated
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = {
        'name': str,
        'description': str,
        'target': str,
        'tools': list,
    }
    
    for field, expected_type in required_fields.items():
        if field not in config:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(config[field], expected_type):
            errors.append(
                f"Field '{field}' must be {expected_type.__name__}, "
                f"got {type(config[field]).__name__}"
            )
    
    # Validate specific field values
    if 'target' in config:
        valid_targets = ['vscode', 'github', 'all']
        if config['target'] not in valid_targets:
            errors.append(
                f"Invalid target '{config['target']}'. "
                f"Must be one of: {', '.join(valid_targets)}"
            )
    
    if 'tools' in config and isinstance(config['tools'], list):
        if not config['tools']:
            errors.append("Field 'tools' cannot be empty")
        
        valid_tools = ['read', 'edit', 'search', 'grep', 'bash', 'web_search']
        for tool in config['tools']:
            if not isinstance(tool, str):
                errors.append(f"Tool '{tool}' must be a string")
            elif tool not in valid_tools:
                errors.append(
                    f"Unknown tool '{tool}'. "
                    f"Valid tools: {', '.join(valid_tools)}"
                )
    
    # Validate optional fields
    if 'infer' in config and not isinstance(config['infer'], bool):
        errors.append(f"Field 'infer' must be boolean, got {type(config['infer']).__name__}")
    
    return errors


def validate_agent_file(filepath: Path) -> Tuple[bool, List[str]]:
    """Validate a single agent configuration file.
    
    Args:
        filepath: Path to the agent .md file
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Failed to read file: {e}"]
    
    try:
        config, markdown = extract_frontmatter(content)
    except ValueError as e:
        return False, [str(e)]
    
    # Validate configuration
    config_errors = validate_agent_config(config, filepath.name)
    if config_errors:
        errors.extend(config_errors)
    
    # Validate markdown content exists
    if not markdown.strip():
        errors.append("Agent instructions (markdown content after frontmatter) cannot be empty")
    
    # Check for minimum documentation
    if len(markdown.strip().split('\n')) < 10:
        errors.append("Agent instructions should be comprehensive (at least 10 lines)")
    
    return len(errors) == 0, errors


def main():
    """Main validation entry point."""
    repo_root = Path(__file__).parent.parent
    agents_dir = repo_root / '.github' / 'agents'
    
    print("=" * 70)
    print("GitHub Copilot Agent Configuration Validator")
    print("=" * 70)
    print()
    
    if not agents_dir.exists():
        print(f"✗ Agents directory not found: {agents_dir}")
        return 1
    
    # Find all agent files (exclude README and other non-agent files)
    # Agent files are identified by having YAML frontmatter, but we exclude known docs
    excluded_files = {'README.md', 'USAGE_EXAMPLES.md'}
    agent_files = [
        f for f in agents_dir.glob('*.md')
        if f.name not in excluded_files
    ]
    
    if not agent_files:
        print(f"⚠ No agent files found in {agents_dir}")
        print("  (Looking for *.md files, excluding README.md and USAGE_EXAMPLES.md)")
        return 0
    
    print(f"Found {len(agent_files)} agent file(s) to validate:\n")
    
    all_valid = True
    results = []
    
    for filepath in sorted(agent_files):
        print(f"Validating: {filepath.relative_to(repo_root)}")
        is_valid, errors = validate_agent_file(filepath)
        
        if is_valid:
            print("  ✓ Valid")
        else:
            print("  ✗ Invalid")
            for error in errors:
                print(f"    - {error}")
            all_valid = False
        
        print()
        results.append((filepath.name, is_valid, errors))
    
    # Summary
    print("=" * 70)
    valid_count = sum(1 for _, is_valid, _ in results if is_valid)
    total_count = len(results)
    
    if all_valid:
        print(f"✓ All {total_count} agent configuration(s) are valid")
        print("=" * 70)
        return 0
    else:
        print(f"✗ {total_count - valid_count} of {total_count} agent(s) failed validation")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
