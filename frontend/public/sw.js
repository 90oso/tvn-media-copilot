/* TVN: solo copias para consultar, nunca se interceptan POST ni respuestas de Gemini. */
const SHELL = "tvn-shell-v1";
const API_CACHE = "tvn-public-evidence-v1";
self.addEventListener("install", event => {
  event.waitUntil(caches.open(SHELL).then(cache => cache.add("/").catch(() => {})).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(Promise.all([
    caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("tvn-") && k !== SHELL && k !== API_CACHE).map(k => caches.delete(k)))),
    self.clients.claim(),
  ]));
});
self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  const isApiSnapshot = url.pathname === "/agenda" || url.pathname === "/explore" || /^\/topics\/[^/]+\/analysis$/.test(url.pathname);
  if (url.origin !== self.location.origin && !isApiSnapshot) return;
  if (isApiSnapshot) {
    event.respondWith(caches.open(API_CACHE).then(async cache => {
      try {
        const response = await fetch(request);
        if (response.ok && response.type !== "opaque") await cache.put(request, response.clone());
        return response;
      } catch {
        return (await cache.match(request)) || Response.json({detail: "Esta consulta no fue guardada antes de perder la conexión."}, {status: 503});
      }
    }));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).then(async response => {
      if (response.ok) { const cache = await caches.open(SHELL); await cache.put("/", response.clone()); }
      return response;
    }).catch(async () => (await caches.match("/")) || new Response("Conéctate para abrir TVN Media Copilot por primera vez.", {status:503})));
    return;
  }
  if (url.pathname.startsWith("/_next/static/") || url.pathname.startsWith("/static/")) {
    event.respondWith(caches.open(SHELL).then(async cache => {
      const saved = await cache.match(request);
      if (saved) return saved;
      const response = await fetch(request);
      if (response.ok) await cache.put(request, response.clone());
      return response;
    }));
  }
});
