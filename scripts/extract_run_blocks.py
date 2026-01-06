#!/usr/bin/env python3
from pathlib import Path
import re

root=Path('.github/workflows')
out=Path('.github/workflows/extracted_runs')
out.mkdir(parents=True, exist_ok=True)
# remove old files
for f in out.glob('*.sh'):
    f.unlink()

count=0
for wf in sorted(root.glob('*.yml')) + sorted(root.glob('*.yaml')):
    text=wf.read_text()
    lines=text.splitlines()
    i=0
    c=0
    while i < len(lines):
        line=lines[i]
        # match step-level '- run:' possibly with trailing |
        if re.match(r'^\s*-\s*run:\s*(\||$)', line):
            c+=1
            # collect following indented lines (at least 1 more space than this indent)
            indent = len(line) - len(line.lstrip(' '))
            i+=1
            block=[]
            while i < len(lines):
                l=lines[i]
                # blank or comment -> include as blank
                if l.strip()=='' or re.match(r'^\s*#', l):
                    if l.strip()=='':
                        block.append('')
                        i+=1
                        continue
                    else:
                        i+=1
                        continue
                lead = len(l) - len(l.lstrip(' '))
                # If indentation is less-or-equal than the '- run' line, we've reached the end of this block
                if lead <= indent:
                    break
                # strip up to content
                block.append(l.lstrip())
                i+=1
            if block:
                fn=out / f"{wf.name}.run.{c}.sh"
                content='\n'.join(block).rstrip() + '\n'
                # add shebang and strict mode if not present
                if not content.startswith('#!'):
                    content = '#!/usr/bin/env bash\nset -euo pipefail\n\n' + content
                fn.write_text(content)
                fn.chmod(0o755)
                count+=1
            continue
        i+=1
print('Extracted', count, 'run blocks into', out)
