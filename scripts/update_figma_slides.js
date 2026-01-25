const axios = require('axios');
const { Client } = require('figma-js');

// These would normally come from environment variables or config
const FIGMA_TOKEN = process.env.FIGMA_TOKEN || 'YOUR_FIGMA_API_TOKEN';
const FILE_KEY = process.env.FIGMA_FILE_KEY || 'YOUR_FIGMA_FILE_KEY';
const ANALYTICS_URL = process.env.ANALYTICS_URL || 'URL_TO_YOUR_ANALYTICS_JSON';

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
