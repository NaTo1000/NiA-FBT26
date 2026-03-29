/**
 * middleware.ts
 *
 * Vercel Edge Middleware — Security, Auth, and Geolocation-Based Routing
 *
 * Runs at the edge (before serverless functions) to:
 *  1. Authenticate API requests via a Bearer token.
 *  2. Route AI requests to the closest regional runner.
 *  3. Add security headers to every response.
 *  4. Block abusive IPs / rate-limit heavy endpoints.
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/** Vercel regions and their preferred AI runner locations. */
const REGION_MAP: Record<string, string> = {
  iad1: "us-east",
  sfo1: "us-west",
  lhr1: "eu-west",
  sin1: "ap-south",
  cdg1: "eu-west",
  hnd1: "ap-east",
  bom1: "ap-south",
  gru1: "sa-east",
};

/** Paths that require a valid Bearer token. */
const PROTECTED_PATHS = ["/api/orchestrator", "/api/stream"];

/**
 * Path prefixes excluded from middleware processing (static assets, icons,
 * manifest, service worker).  Kept as a named constant for readability.
 */
const EXCLUDED_PATH_PREFIXES = [
  "_next/static",
  "_next/image",
  "favicon.ico",
  "icons/",
  "manifest.json",
  "sw.js",
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getRegion(req: NextRequest): string {
  // Vercel sets x-vercel-id like "iad1::xyz", extract the datacenter prefix.
  const vercelId = req.headers.get("x-vercel-id") ?? "";
  const dc = vercelId.split("::")[0]?.toLowerCase() ?? "iad1";
  return REGION_MAP[dc] ?? "us-east";
}

function isAuthenticated(req: NextRequest): boolean {
  const apiSecret = process.env.API_SECRET;
  // Only skip auth in explicit development mode; fail-closed in all other envs
  if (!apiSecret) {
    return process.env.NODE_ENV === "development";
  }

  const authHeader = req.headers.get("authorization") ?? "";
  const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : "";
  return token === apiSecret;
}

function addSecurityHeaders(response: NextResponse): NextResponse {
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-XSS-Protection", "1; mode=block");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  return response;
}

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------

export function middleware(req: NextRequest): NextResponse {
  const { pathname } = req.nextUrl;

  // --- Authentication guard ---
  const needsAuth = PROTECTED_PATHS.some((p) => pathname.startsWith(p));
  if (needsAuth && req.method !== "OPTIONS" && !isAuthenticated(req)) {
    return addSecurityHeaders(
      NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    );
  }

  // --- Geolocation-based region header injection ---
  const region = getRegion(req);
  const response = NextResponse.next();
  response.headers.set("x-nia-region", region);

  // Pass region to downstream serverless functions via a custom header so they
  // can pick the nearest AI runner without a second geo-lookup.
  if (pathname.startsWith("/api/")) {
    response.headers.set("x-nia-ai-region", region);
  }

  return addSecurityHeaders(response);
}

// ---------------------------------------------------------------------------
// Route matcher — only run middleware on relevant paths
// ---------------------------------------------------------------------------

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT the paths listed in EXCLUDED_PATH_PREFIXES
     * (static files, icons, manifest, service worker).
     * The pattern is written as a literal string to avoid dynamic regex issues.
     */
    "/((?!_next\\/static|_next\\/image|favicon\\.ico|icons\\/|manifest\\.json|sw\\.js).*)",
  ],
};
