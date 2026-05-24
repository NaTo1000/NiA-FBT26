/**
 * public/sw.js
 *
 * NiA-FBT26 Service Worker — PWA Offline Support & Runtime Caching
 *
 * Strategy:
 *  • Static assets  → Cache-First  (long-lived, versioned via CACHE_VERSION)
 *  • API responses  → Network-First with 5 s timeout, fall back to cache
 *  • HTML pages     → Stale-While-Revalidate
 */

const CACHE_VERSION = "nia-fbt26-v2";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE    = `${CACHE_VERSION}-api`;

const PRECACHE_URLS = [
  "/",
  "/manifest.json",
  "/favicon.ico",
];

// ---------------------------------------------------------------------------
// Install — precache shell resources
// ---------------------------------------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// ---------------------------------------------------------------------------
// Activate — clean up stale caches
// ---------------------------------------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== STATIC_CACHE && k !== API_CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// Fetch — routing strategies
// ---------------------------------------------------------------------------
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin requests
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  // API routes — always Network-Only (no caching for authenticated/dynamic data)
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(networkOnly(request));
    return;
  }

  // Static assets (_next/static) — Cache-First
  if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // HTML navigation — Stale-While-Revalidate
  if (request.headers.get("accept")?.includes("text/html")) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  // Everything else — Cache-First
  event.respondWith(cacheFirst(request, STATIC_CACHE));
});

// ---------------------------------------------------------------------------
// Strategy implementations
// ---------------------------------------------------------------------------

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
  }
  return response;
}

async function networkOnly(request) {
  try {
    return await fetch(request);
  } catch {
    return new Response(
      JSON.stringify({
        error: "Unable to reach server. Please check your connection and try again.",
      }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

async function networkFirstWithTimeout(request, cacheName, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(request, { signal: controller.signal });
    clearTimeout(timer);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    clearTimeout(timer);
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({
        error: "Unable to reach server. Please check your connection and try again.",
      }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) cache.put(request, response.clone());
    return response;
  });

  return cached ?? fetchPromise;
}
