const path = require('node:path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    turbopack: {
      // Point Turbopack to the workspace containing your Next app
      root: path.join(__dirname, 'apps', 'web'),
    },
  },
};

module.exports = nextConfig;
