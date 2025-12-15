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
```
