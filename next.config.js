/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    turbopack: {
      // Point Turbopack to the workspace containing your Next app
      root: './apps/web',
    },
  },
};

module.exports = nextConfig;
