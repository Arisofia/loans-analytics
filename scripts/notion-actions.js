// scripts/notion-actions.js
const { Client } = require('@notionhq/client')

function extractNotionId(value) {
  if (!value) return null;
  const raw = value.trim();
  const plainMatch = raw.match(/[0-9a-fA-F]{32}/);
  if (plainMatch) return plainMatch[0];
  const dashedMatch = raw.match(
    /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/
  );
  if (dashedMatch) return dashedMatch[0].replace(/-/g, '');
  return raw;
}

const NOTION_TOKEN =
  process.env.NOTION_API_KEY ||
  process.env.NOTION_TOKEN ||
  process.env.NOTION_INTEGRATION_TOKEN;
const DATABASE_ID = extractNotionId(
  process.env.NOTION_DATABASE_ID ||
    process.env.NOTION_DATABASE_URL ||
    process.env.NOTION_DATABASE
);

if (!NOTION_TOKEN || !DATABASE_ID) {
  console.error('Missing NOTION_TOKEN/NOTION_API_KEY or NOTION_DATABASE_ID/URL.');
  process.exit(1);
}

const notion = new Client({ auth: NOTION_TOKEN })

// Property names can differ across databases. Override via env if needed.
const TITLE_PROP = process.env.NOTION_TITLE_PROP || 'Name'
const STATUS_PROP = process.env.NOTION_STATUS_PROP || null // e.g. "Status"
const STATUS_NEW_VALUE = process.env.NOTION_STATUS_NEW_VALUE || 'In Progress'
const STATUS_DONE_VALUE = process.env.NOTION_STATUS_DONE_VALUE || 'Done'
const PEOPLE_PROP = process.env.NOTION_PEOPLE_PROP || null // e.g. "Owner"
const PEOPLE_ID = process.env.NOTION_PEOPLE_ID || null // optional person ID

async function getDatabaseProperties() {
  const db = await notion.databases.retrieve({ database_id: DATABASE_ID })
  const available = Object.keys(db.properties)
  console.log('Available properties:', available.join(', '))
  return db.properties
}

// Utility: query with a filter
async function queryFiltered() {
  if (!STATUS_PROP) {
    console.log('Skipping filter query: NOTION_STATUS_PROP not set.')
    return []
  }
  const res = await notion.databases.query({
    database_id: DATABASE_ID,
    filter: {
      property: STATUS_PROP,
      status: { equals: STATUS_NEW_VALUE },
    },
  })
  console.log('Filtered results:', res.results.length)
  return res.results
}

// Create a new page
async function createPage() {
  const baseProps = {
    [TITLE_PROP]: { title: [{ text: { content: 'New entry' } }] },
  }

  if (STATUS_PROP) {
    baseProps[STATUS_PROP] = { status: { name: STATUS_NEW_VALUE } }
  }

  if (PEOPLE_PROP && PEOPLE_ID) {
    baseProps[PEOPLE_PROP] = { people: [{ id: PEOPLE_ID }] }
  }

  const res = await notion.pages.create({
    parent: { database_id: DATABASE_ID },
    properties: baseProps,
    // optional rich text body
    children: [
      {
        object: 'block',
        type: 'paragraph',
        paragraph: { rich_text: [{ text: { content: 'Body text here.' } }] },
      },
    ],
  })
  console.log('Created page:', res.id)
  return res.id
}

// Update an existing page
async function updatePage(pageId) {
  const props = {}
  if (STATUS_PROP) props[STATUS_PROP] = { status: { name: STATUS_DONE_VALUE } }

  const res = await notion.pages.update({
    page_id: pageId,
    properties: props,
  })
  console.log('Updated page:', res.id)
}

;(async () => {
  try {
    await getDatabaseProperties()
    await queryFiltered()
    const newPageId = await createPage()
    await updatePage(newPageId)
  } catch (err) {
    console.error('Notion error:', err.message)
    process.exit(1)
  }
})()
