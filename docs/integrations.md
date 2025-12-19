<<<<<<< HEAD
# Design and productivity integrations
This guide documents supported SDKs for Figma, Notion, and Slack with examples in Node.js/TypeScript and Python. Ensure your `.env` file (or environment variables in your secret manager) includes the required tokens and is never committed to source control.
## Environment variables
```bash
FIGMA_TOKEN=...   # Figma personal access token
NOTION_TOKEN=...  # Notion integration secret
SLACK_TOKEN=...   # Slack bot token
```
## Node.js / TypeScript
Install the official or community SDKs with npm:

> **Note:** There is no official Figma SDK for Node.js.  
> However, Figma provides an [official REST API](https://www.figma.com/developers/api), which is the authoritative reference for programmatic access. The community SDKs below are convenient wrappers around this API.
> - [`figma-js`](https://www.npmjs.com/package/figma-js) ([GitHub](https://github.com/jongold/figma-js)) is a community-maintained REST client.  
> - [`@figma-js/sdk`](https://www.npmjs.com/package/@figma-js/sdk) ([GitHub](https://github.com/figma-js/sdk)) is an alternative, also community-maintained.  
> **Recommendation:**  
> - [`figma-js`](https://www.npmjs.com/package/figma-js) is more widely used and has more GitHub stars, but its maintenance activity has slowed in recent years (as of June 2024).  
> - [`@figma-js/sdk`](https://www.npmjs.com/package/@figma-js/sdk) is newer, has more active recent development, and offers better TypeScript support out of the box (as of June 2024).  
> If you need strong TypeScript support or want a more actively maintained package, prefer `@figma-js/sdk`. For broader community usage and more examples, `figma-js` may be preferable. **Be sure to check their [npm](https://www.npmjs.com/package/figma-js) and [GitHub](https://github.com/jongold/figma-js) pages for `figma-js`, and [npm](https://www.npmjs.com/package/@figma-js/sdk) and [GitHub](https://github.com/figma-js/sdk) for `@figma-js/sdk`, to verify their current maintenance status before deciding.**
```bash
# Figma REST client (community SDK)
npm install figma-js                # Or: npm install @figma-js/sdk
# Notion API client (official)
npm install @notionhq/client
# Slack Web API client (official)
npm install @slack/web-api
# If you want to generate types or interact with Figma design tokens
npm install --save-dev figma-export
```
Usage examples (choose one Figma package):
```ts
// figma.ts — using figma-js
import { Client as FigmaClient } from 'figma-js';
export const figma = FigmaClient({ personalAccessToken: process.env.FIGMA_TOKEN });
// figma-sdk.ts — using @figma-js/sdk
// import { Figma } from '@figma-js/sdk';
// export const figmaSdk = new Figma({ personalAccessToken: process.env.FIGMA_TOKEN });
// notion.ts
import { Client as NotionClient } from '@notionhq/client';
export const notion = new NotionClient({ auth: process.env.NOTION_TOKEN });
// slack.ts
import { WebClient } from '@slack/web-api';
export const slack = new WebClient(process.env.SLACK_TOKEN);
```
To export Figma tokens via CLI:
```bash
# Install globally
npm install -g figma-export
# Or run via npx
npx figma-export tokens --file-id <your-file-id> --token <your-figma-token>
```
## Python
Install the corresponding packages with pip:
```bash
# Figma API (community library)
pip install figma-python
# Notion SDK (official)
pip install notion-client
# Slack SDK (official)
pip install slack-sdk
```
Usage example:
```python
import os
from figma import Figma
from notion_client import Client as NotionClient
from slack_sdk import WebClient
figma_client = Figma(access_token=os.getenv("FIGMA_TOKEN"))
notion_client = NotionClient(auth=os.getenv("NOTION_TOKEN"))
slack_client = WebClient(token=os.getenv("SLACK_TOKEN"))
# Example: get a file from Figma
# file = figma_client.file("FIGMA_FILE_KEY")
```
Export the environment variables for local sessions:
```bash
export FIGMA_TOKEN=<your-figma-token>
export NOTION_TOKEN=<your-notion-integration-secret>
export SLACK_TOKEN=<your-slack-bot-token>
=======
# Integrations Guide: Figma, Notion, and Slack SDKs

This guide explains how to set up and use the official SDKs for Figma, Notion, and Slack in Node.js/TypeScript and Python. It lists the environment variables you need, installation commands, and minimal client initialization snippets so you can keep secrets out of your code and in your runtime configuration.

## Environment variables

Export these values before running the examples:

- `FIGMA_PERSONAL_ACCESS_TOKEN`: Figma personal access token with file read access.
- `FIGMA_FILE_ID`: Figma file ID used for figma-export or SDK reads.
- `NOTION_TOKEN`: Internal integration token for Notion.
- `NOTION_DATABASE_ID`: Database ID for querying Notion content.
- `SLACK_BOT_TOKEN`: Slack bot token (starts with `xoxb-`).
- `SLACK_SIGNING_SECRET`: Slack signing secret for request verification.

```bash
# Mac/Linux shell examples
export FIGMA_PERSONAL_ACCESS_TOKEN="<token>"
export FIGMA_FILE_ID="<file_id>"
export NOTION_TOKEN="<token>"
export NOTION_DATABASE_ID="<database_id>"
export SLACK_BOT_TOKEN="<token>"
export SLACK_SIGNING_SECRET="<signing_secret>"
```

## Node.js / TypeScript setup

### Install SDKs

Choose the packages that match your preferred Figma client:

```bash
# Figma clients (pick one)
npm install figma-js
# or
npm install @figma-js/sdk

# Notion and Slack
npm install @notionhq/client @slack/web-api

# Figma token export CLI
npm install --save-dev figma-export
```

### Usage examples (TypeScript)

#### Figma client (figma-js)

```ts
import { Client } from 'figma-js'

const figma = Client({
  personalAccessToken: process.env.FIGMA_PERSONAL_ACCESS_TOKEN!,
})

async function getFileNodes() {
  const fileId = process.env.FIGMA_FILE_ID!
  const response = await figma.file(fileId)
  return response.data.document.children
}
```

#### Figma client (@figma-js/sdk)

```ts
import { Figma } from '@figma-js/sdk'

const figma = new Figma({
  personalAccessToken: process.env.FIGMA_PERSONAL_ACCESS_TOKEN!,
})

async function getFileName() {
  const fileId = process.env.FIGMA_FILE_ID!
  const file = await figma.getFile(fileId)
  return file.name
}
```

#### Notion client

```ts
import { Client } from '@notionhq/client'

const notion = new Client({ auth: process.env.NOTION_TOKEN })

async function listDatabasePages() {
  const databaseId = process.env.NOTION_DATABASE_ID!
  const response = await notion.databases.query({ database_id: databaseId })
  return response.results.map((page) => page.id)
}
```

#### Slack Web API client

```ts
import { WebClient } from '@slack/web-api'

const slack = new WebClient(process.env.SLACK_BOT_TOKEN)

async function postHealthCheck(channelId: string) {
  await slack.chat.postMessage({
    channel: channelId,
    text: 'ABACO integrations are live.',
  })
}
```

### Export design tokens from Figma

Use [`figma-export`](https://github.com/marcomontalbano/figma-export) to pull design tokens from a Figma file:

```bash
npx figma-export --file-id "$FIGMA_FILE_ID" \
  --figma-token "$FIGMA_PERSONAL_ACCESS_TOKEN" \
  --output-dir ./exports/tokens \
  --format json
```

## Python setup

### Install SDKs

```bash
pip install figma-python notion-client slack-sdk google-auth google-auth-oauthlib
```

### Usage examples (Python)

#### Figma client

```python
from figma import Figma
import os

figma = Figma(os.environ["FIGMA_PERSONAL_ACCESS_TOKEN"])

file_id = os.environ["FIGMA_FILE_ID"]
file = figma.get_file(file_id)
print(file["name"])
```

#### Notion client

```python
from notion_client import Client
import os

notion = Client(auth=os.environ["NOTION_TOKEN"])

def list_database_pages():
    database_id = os.environ["NOTION_DATABASE_ID"]
    response = notion.databases.query(database_id=database_id)
    return [page["id"] for page in response["results"]]
```

#### Slack SDK

```python
from slack_sdk import WebClient
import os

slack = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

slack.chat_postMessage(
    channel="#integrations",
    text="ABACO integrations are live.",
)
```

## Architecture visuals

### SDK client class diagram

```mermaid
classDiagram
  class FigmaClient {
    +getFile(fileId)
  }
  class NotionClient {
    +queryDatabase(databaseId)
  }
  class SlackWebClient {
    +chatPostMessage(channel, text)
  }
  FigmaClient <|-- figma~js~Client
  FigmaClient <|-- figma_sdk_Figma
  NotionClient <|-- NotionClientImpl
  SlackWebClient <|-- SlackWebClientImpl
```

### Integration choice flow

```mermaid
flowchart TD
  Start([Start]) --> Lang{Language}
  Lang -->|Node.js / TS| NodeSetup["Install SDKs via npm\n(figma-js or @figma-js/sdk, @notionhq/client, @slack/web-api)"]
  Lang -->|Python| PySetup["Install SDKs via pip\n(figma-python, notion-client, slack-sdk)"]
  NodeSetup --> Env["Export env vars\nFIGMA_PERSONAL_ACCESS_TOKEN, NOTION_TOKEN, SLACK_BOT_TOKEN, etc."]
  PySetup --> Env
  Env --> Choice{Need tokens?}
  Choice -->|Design tokens| FigmaExport["Run figma-export CLI\nwith FIGMA_FILE_ID"]
  Choice -->|API data| SDKUse["Call SDKs\n(Figma file read, Notion query, Slack message)"]
  SDKUse --> Done([Integrations ready])
  FigmaExport --> Done
>>>>>>> main
```
