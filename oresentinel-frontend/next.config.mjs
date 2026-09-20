import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // No ESLint config is shipped with this scaffold; don't fail the build on lint.
  eslint: { ignoreDuringBuilds: true },
  images: {
    remotePatterns: [{ protocol: 'https', hostname: '**' }],
  },
  // Pin the workspace root to this folder. Without this, Next.js gets
  // confused if a stray package-lock.json ever ends up in a parent
  // directory (e.g. someone ran `npm install` from the repo root by
  // mistake) and silently picks the wrong root.
  outputFileTracingRoot: __dirname,
};
export default nextConfig;
