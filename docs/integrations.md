
## Environment variables

Export these values before running the examples:

- `NOTION_TOKEN`: Internal integration token for Notion.
- `NOTION_DATABASE_ID`: Database ID for querying Notion content.

```bash
# Mac/Linux shell examples
export NOTION_TOKEN="<token>"
export NOTION_DATABASE_ID="<database_id>"
<<<<<<< HEAD
=======
export SLACK_BOT_TOKEN="<token>"
export SLACK_SIGNING_SECRET="<signing_secret>"
```

Choose the packages that match your preferred Figma client:

```bash
# Figma clients (pick one)
npm install figma-js
# or
npm install @figma-js/sdk


# Figma token export CLI
npm install --save-dev figma-export
```

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
>>>>>>> copilot/refactor-test-import-structure
```

*** End Patch
  PySetup --> Env
  Env --> Choice{Need tokens?}
  SDKUse --> Done([Integrations ready])
```
