/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@zroky/shared-types'],
  output: 'standalone',
};

module.exports = nextConfig;
