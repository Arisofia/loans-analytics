from pathlib import Path

changed = []
for p in Path(".github/workflows").glob("*"):
    if p.is_file():
        s = p.read_text()
        new = "\n".join(line.rstrip() for line in s.splitlines()) + "\n"
        if new != s:
            p.write_text(new)
            changed.append(str(p))
print("Files updated:", changed)
if changed:
    import subprocess

    subprocess.run(["git", "add"] + changed, check=True)
    subprocess.run(
        ["git", "commit", "-m", "ci: strip trailing whitespace from workflow files"], check=True
    )
