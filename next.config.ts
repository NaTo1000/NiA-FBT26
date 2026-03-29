import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // -------------------------------------------------------------------------
  // TypeScript & ESLint
  // -------------------------------------------------------------------------
  typescript: {
    // Fail CI builds on type errors
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },

  // -------------------------------------------------------------------------
  // Image Optimisation (Vercel native)
  // -------------------------------------------------------------------------
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      { protocol: "https", hostname: "huggingface.co" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
    ],
    minimumCacheTTL: 86400, // 24 h
  },

  // -------------------------------------------------------------------------
  // HTTP Headers
  // -------------------------------------------------------------------------
  async headers() {
    const isProd = process.env.NODE_ENV === "production";
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-DNS-Prefetch-Control", value: "on" },
          // HSTS is only safe in production; applying it on localhost would
          // permanently redirect the browser to HTTPS on that port.
          ...(isProd
            ? [
                {
                  key: "Strict-Transport-Security",
                  value: "max-age=63072000; includeSubDomains; preload",
                },
              ]
            : []),
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ];
  },

  // -------------------------------------------------------------------------
  // Rewrites
  // -------------------------------------------------------------------------
  async rewrites() {
    return [
      { source: "/api/orchestrate", destination: "/api/orchestrator" },
      { source: "/api/ai/stream", destination: "/api/stream" },
    ];
  },

  // -------------------------------------------------------------------------
  // Experimental features
  // -------------------------------------------------------------------------
  experimental: {
    // Optimise package imports to reduce bundle size
    optimizePackageImports: ["lucide-react"],
  },

  // -------------------------------------------------------------------------
  // Webpack — enable WASM support for signal parsers
  // -------------------------------------------------------------------------
  webpack(config) {
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
      layers: true,
    };
    return config;
  },
};

export default nextConfig;
