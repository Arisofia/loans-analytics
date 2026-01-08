#!/usr/bin/env python3
"""Extract inline `run` blocks from GitHub Actions workflows."""
import re
from pathlib import Path


def process_workflow(wf, out, run_pattern):
    """Process a single workflow file to extract run blocks."""
    if 'extracted_runs' in str(wf):
        return 0

    text = wf.read_text()
    lines = text.splitlines()
    count = 0
    i = 0
    c = 0
    while i < len(lines):
        line = lines[i]
        match = run_pattern.match(line)
        if match:
            indent_str, dash_prefix, pipe, rest = match.groups()
            # The total indentation of the 'run:' key itself
            base_indent = len(indent_str) + len(dash_prefix)

            c += 1
            block = []

            if pipe == '|':
                # Multi-line block
                i += 1
                while i < len(lines):
                    current_line = lines[i]
                    if not current_line.strip():
                        block.append('')
                        i += 1
                        continue

                    l_indent = len(current_line) - len(current_line.lstrip())
                    if l_indent <= base_indent:
                        # End of block
                        break

                    # Strip the base indentation from the block
                    block.append(current_line[base_indent+2:] if len(current_line) > base_indent+2
                                 else current_line.lstrip())
                    i += 1
            else:
                # Single-line run
                if rest.strip():
                    block.append(rest.strip())
                i += 1

            if block:
                fn = out / f"{wf.name}.run.{c}.sh"
                content = '\n'.join(block).rstrip() + '\n'
                if not content.startswith('#!'):
                    content = '#!/usr/bin/env bash\nset -euo pipefail\n\n' + content
                fn.write_text(content)
                fn.chmod(0o755)
                count += 1
            continue
        i += 1
    return count


def main():
    """Main entry point for extracting run blocks."""
    root = Path('.github/workflows')
    out = Path('.github/workflows/extracted_runs')
    out.mkdir(parents=True, exist_ok=True)

    # remove old files
    for f in out.glob('*.sh'):
        f.unlink()

    total_count = 0
    # Match lines like:
    # - run: |
    # - run: command
    #   run: |
    #   run: command
    run_pattern = re.compile(r'^(\s*)(-?\s*)run:\s*(\|?)(.*)$')

    for wf in sorted(root.glob('*.yml')) + sorted(root.glob('*.yaml')):
        total_count += process_workflow(wf, out, run_pattern)

    print(f'Extracted {total_count} run blocks into {out}')


if __name__ == '__main__':
    main()
