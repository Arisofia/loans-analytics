# Python Development Setup

## Fix "Unable to import 'pydantic'" Error

This error occurs when your IDE cannot find the Python packages. Follow these steps:

### Quick Fix

1. **Create virtual environment** (if not exists):
   ```bash
   python3 -m venv .venv
   ```

2. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate  # On macOS/Linux
   # OR
   .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install setuptools  # Required for Python 3.14+
   ```

4. **Reload VS Code/Windsurf**:
   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Python: Select Interpreter"
   - Choose `.venv/bin/python`

### Verify Setup

```bash
source .venv/bin/activate
python -c "import pydantic; print(f'✅ Pydantic {pydantic.__version__}')"
python -m pytest python/multi_agent/test_historical_context.py -q
```

Expected output:
```
✅ Pydantic 2.12.5
..............                                                                                                               [100%]
14 passed, 7 warnings in 1.15s
```

### VS Code Configuration

The workspace is already configured in `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.autoSearchPaths": true
}
```

### Troubleshooting

If you still see the import error after setup:

1. **Restart VS Code/Windsurf** completely
2. **Check Python interpreter** in the status bar (bottom-right)
3. **Verify virtual environment**:
   ```bash
   which python  # Should show: /path/to/project/.venv/bin/python
   ```

4. **Reinstall packages**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

### Why Virtual Environments?

- ✅ **Isolates dependencies** per project
- ✅ **Prevents conflicts** between package versions
- ✅ **IDE compatibility** - easier for tools to find packages
- ✅ **Reproducible builds** - same environment for all developers
- ✅ **Python 3.14+ compatibility** - handles newer Python versions properly

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'pkg_resources'` | `pip install setuptools` |
| `No module named 'pytest'` | `pip install -r requirements-dev.txt` |
| IDE shows import error but tests pass | Reload IDE and select `.venv/bin/python` interpreter |
| Wrong Python version | Recreate venv with correct Python: `python3.14 -m venv .venv` |

---

**Note**: The virtual environment (`.venv/`) is excluded from git via `.gitignore`. Each developer must create their own virtual environment.
