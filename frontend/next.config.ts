import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: { bodySizeLimit: "50mb" },
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default config;
