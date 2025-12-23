
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

For granular control, edit `~/.codex/config.toml` (on Windows, `%USERPROFILE%\.codex\config.toml`). In the IDE extension, open the gear icon in the top right, choose **MCP settings**, then **Open config.toml** to modify the active config file.

Each MCP server uses its own `[mcp_servers.<server-name>]` table.

### STDIO servers

### Streamable HTTP servers

### Other options

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
disabled_tools = ["open"] # disabled takes precedence even if also listed in enabled_tools
startup_timeout_sec = 20
tool_timeout_sec = 45
enabled = true
```

## Examples of useful MCP servers

Common MCP servers to connect with Codex include:

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

### `codex` tool properties

### `codex-reply` tool properties
