/* RAPP VUI service worker — installable PWA + offline app shell.
   Never touches POST /chat (GET-only). CDN deps (three, mediapipe) are
   cache-first so a home-screen launch works offline after the first load. */
const CACHE = "rapp-vui-v1";
const SHELL = ["./", "./index.html", "./manifest.json", "./icon-180.png", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()).catch(()=>{}));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;                       // /chat is POST — leave it alone
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    // app shell: network-first, fall back to cache (so updates land, offline still works)
    e.respondWith(
      fetch(req).then(r => { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); return r; })
                .catch(() => caches.match(req).then(m => m || caches.match("./index.html")))
    );
  } else {
    // CDN (three.js, mediapipe wasm/models): cache-first for offline
    e.respondWith(
      caches.match(req).then(m => m || fetch(req).then(r => { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); return r; }).catch(() => m))
    );
  }
});
