#!/usr/bin/env python3
"""Extract inline `run` blocks from GitHub Actions workflows."""
import re
from pathlib import Path

def main():
    root = Path('.github/workflows')
    out = Path('.github/workflows/extracted_runs')
    out.mkdir(parents=True, exist_ok=True)

    # remove old files
    for f in out.glob('*.sh'):
        f.unlink()

    count = 0
    # Match lines like:
    # - run: |
    # - run: command
    #   run: |
    #   run: command
    run_pattern = re.compile(r'^(\s*)(-?\s*)run:\s*(\|?)(.*)$')

    for wf in sorted(root.glob('*.yml')) + sorted(root.glob('*.yaml')):
        if 'extracted_runs' in str(wf):
            continue
            
        text = wf.read_text()
        lines = text.splitlines()
        
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
                        l = lines[i]
                        if not l.strip():
                            block.append('')
                            i += 1
                            continue
                        
                        l_indent = len(l) - len(l.lstrip())
                        if l_indent <= base_indent:
                            # End of block
                            break
                        
                        # Strip the base indentation from the block
                        block.append(l[base_indent+2:] if len(l) > base_indent+2 else l.lstrip())
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

    print(f'Extracted {count} run blocks into {out}')

if __name__ == '__main__':
    main()
