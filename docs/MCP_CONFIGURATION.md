# MCP Configuration Guide

This guide shows how to add and manage Model Context Protocol (MCP) servers when working with Codex, either through the CLI or by editing the `config.toml` file directly.

## CLI usage

Add a new MCP server with environment variables using `codex mcp add`:

```bash
codex mcp add <server-name> --env VAR1=VALUE1 --env VAR2=VALUE2 -- <stdio server-command>
```

For example, to add Context7 (a free MCP server for developer documentation), run:

```bash
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

Use `codex mcp --help` to see all available MCP CLI commands.

### Terminal UI (TUI)

After launching Codex and opening the TUI, run `/mcp` to see your actively connected MCP servers.

## Config file (`config.toml`)

<<<<<<< HEAD
For granular control, edit `~/.codex/config.toml`. In the IDE extension, open the gear icon in the top right, choose **MCP settings**, then **Open config.toml**.
=======
For granular control, edit `~/.codex/config.toml` (on Windows, `%USERPROFILE%\\.codex\\config.toml`). In the IDE extension, open the gear icon in the top right, choose **MCP settings**, then **Open config.toml** to modify the active config file.
>>>>>>> origin/main

Each MCP server uses its own `[mcp_servers.<server-name>]` table.

### STDIO servers
- `command` (required): command to launch the server.
- `args` (optional): arguments passed to the server.
- `env` (optional): environment variables to set for the server.
- `env_vars` (optional): additional environment variables to whitelist/forward.
- `cwd` (optional): working directory to launch the server from.

### Streamable HTTP servers
- `url` (required): URL to access the server.
- `bearer_token_env_var` (optional): env var name containing a bearer token for the `Authorization` header.
- `http_headers` (optional): map of header names to static values.
- `env_http_headers` (optional): map of header names to env var names (values pulled from env).

### Other options
- `startup_timeout_sec` (optional): timeout in seconds for the server to start (default 10).
- `tool_timeout_sec` (optional): timeout in seconds for tools to run (default 60).
- `enabled` (optional): set `false` to disable a configured server without deleting it.
- `enabled_tools` (optional): allow-list of tools exposed from the server.
<<<<<<< HEAD
- `disabled_tools` (optional): deny-list of tools to hide (applied after `enabled_tools`).
=======
- `disabled_tools` (optional): deny-list of tools to hide; it overrides overlaps with `enabled_tools`.
>>>>>>> origin/main
- `[features].rmcp_client` (optional): enables the Rust MCP client for STDIO servers and OAuth on streamable HTTP.
- `experimental_use_rmcp_client` (optional): older flag for OAuth/streamable HTTP; prefer `[features].rmcp_client`.
- Set feature flags inside the top-level `[features]` table (not under a specific server).

### Examples

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]

[mcp_servers.context7.env]
MY_ENV_VAR = "MY_ENV_VALUE"

[features]
rmcp_client = true
```

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
```

```toml
[mcp_servers.chrome_devtools]
url = "http://localhost:3000/mcp"
enabled_tools = ["open", "screenshot"]
<<<<<<< HEAD
disabled_tools = ["screenshot"] # applied after enabled_tools
=======
disabled_tools = ["open"] # disabled takes precedence even if also listed in enabled_tools
>>>>>>> origin/main
startup_timeout_sec = 20
tool_timeout_sec = 45
enabled = true
```

## Examples of useful MCP servers

Common MCP servers to connect with Codex include:
- **Context7** — access a wide range of developer documentation.
- **Figma Local/Remote** — access your Figma designs.
- **Playwright** — control and inspect a browser using Playwright.
- **Chrome Developer Tools** — control and inspect a Chrome browser.
- **Sentry** — access Sentry logs.
- **GitHub** — manage GitHub data beyond git (PRs, issues, etc.).

## Running Codex as an MCP server

Codex itself can run as an MCP server so other MCP clients (including those built with the OpenAI Agents SDK) can connect.

Start the Codex MCP server:

```bash
codex mcp-server
```

You can launch it with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector codex mcp-server
```

Sending a `tools/list` request will reveal two tools:
- **codex** — runs a Codex session. Parameters mirror the Codex Config struct.
- **codex-reply** — continues a Codex session given the conversation ID.

### `codex` tool properties
- `prompt` (required): initial user prompt to start the Codex conversation.
- `approval-policy`: approval policy for shell commands (`untrusted`, `on-failure`, `never`).
- `base-instructions`: set of instructions to use instead of defaults.
- `config`: config object overriding values in `$CODEX_HOME/config.toml`.
- `cwd`: working directory for the session (relative paths resolved from the server process).
- `include-plan-tool`: whether to include the plan tool in the conversation.
- `model`: optional override for the model name (e.g., `o3`, `o4-mini`).
- `profile`: configuration profile from `config.toml` to specify default options.
- `sandbox`: sandbox mode (`read-only`, `workspace-write`, or `danger-full-access`).

### `codex-reply` tool properties
- `prompt` (required): next user prompt to continue the Codex conversation.
- `conversationId` (required): ID of the conversation to continue.
