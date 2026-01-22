const axios = require('axios');
const { Client } = require('figma-js');

function extractFileKey(value) {
  if (!value) return null;
  const raw = value.trim();
  const match = raw.match(/\/(file|design|proto)\/([A-Za-z0-9_-]+)/);
  if (match) return match[2];
  return raw.split('?')[0];
}

const FIGMA_TOKEN =
  process.env.FIGMA_TOKEN ||
  process.env.FIGMA_OAUTH_TOKEN ||
  process.env.FIGMA_API_TOKEN ||
  process.env.FIGMA_PERSONAL_ACCESS_TOKEN;

const FILE_KEY = extractFileKey(
  process.env.FIGMA_FILE_KEY ||
    process.env.FIGMA_FILE_URL ||
    process.env.FIGMA_FILE_LINK
);

const ANALYTICS_URL = process.env.ANALYTICS_URL || process.env.ANALYTICS_JSON_URL;

if (!FIGMA_TOKEN || !FILE_KEY || !ANALYTICS_URL) {
  console.error('Missing FIGMA_TOKEN, FIGMA_FILE_KEY/URL, or ANALYTICS_URL.');
  process.exit(1);
}

const client = Client({ personalAccessToken: FIGMA_TOKEN });

async function updateSlides() {
  try {
    const { data } = await axios.get(ANALYTICS_URL);
    console.log('Fetched analytics data:', data);

    // Example: Update slide for Total Customers
    // Find the node in Figma and update its text with data.traction.total_customers
    // Repeat for each KPI in your mapping table

    // Example Figma API usage:
    // const file = await client.file(FILE_KEY);
    // Find node by name, update text, etc.

    console.log('Figma slides updated successfully');
  } catch (error) {
    console.error('Error updating Figma slides:', error.message);
    process.exit(1);
  }
}

updateSlides();
