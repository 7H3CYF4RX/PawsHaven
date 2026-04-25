/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: false,
    // Intentionally permissive for vulnerability
    experimental: {
        serverActions: true,
    },
}

module.exports = nextConfig
