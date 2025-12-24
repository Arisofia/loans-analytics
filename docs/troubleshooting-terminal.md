# Terminal and Tooling Troubleshooting
## Login shell exits with code 1

A login shell (`bash -l`) reads `/etc/profile` then one of `~/.bash_profile`, `~/.bash_login`, or `~/.profile`. If any command inside those files fails, the shell terminates with exit code `1`.
**How to diagnose**

1. Open an existing working shell session.
2. Trace the startup script to find the failing line:
   - `bash -x ~/.bash_profile` if that file exists, otherwise
   - `bash -x ~/.profile`
3. Review the trace output to identify the command returning a non-zero status.
**How to fix**

- Remove or comment out the failing command while you repair it.
- Ensure commands that depend on optional tools (e.g., `pyenv`, `nvm`) guard against missing binaries.
- Reopen the terminal to confirm the shell now starts cleanly.
## VS Code Python terminals not loading `.env`

If environment variables from `.env` are not injected into VS Code terminals, enable the built-in setting so new terminals source the file automatically.
**Enable injection**

1. Open **Settings (JSON)** in VS Code.
2. Add the following entry:
   ```json
   "python.terminal.useEnvFile": true
   ```
3. Open a new terminal; it will now include variables from `.env`.
## Sourcery configuration version error

Sourcery expects the `version` field in `.sourcery.yaml` to be the integer `1`. Any other value triggers a configuration error.
**Validate configuration**

- Ensure the top of `.sourcery.yaml` reads:
  ```yaml
  version: 1
  ```
- Restart or rerun Sourcery to verify the configuration loads without errors.
