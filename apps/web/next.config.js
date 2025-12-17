/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    dirs: ['app', 'pages', 'components', 'lib', 'src'],
  },
  // Explicitly tell Turbopack this is the root to avoid confusion with parent directories
  experimental: {
    turbopack: {
      root: '.',
    },
  },
};

module.exports = nextConfig;
