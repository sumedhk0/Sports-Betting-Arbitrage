/** @type {import('next').NextConfig} */
const nextConfig = {
  // Ignore the api folder (Python serverless functions)
  webpack: (config) => {
    config.externals = config.externals || [];
    return config;
  },
};

module.exports = nextConfig;
