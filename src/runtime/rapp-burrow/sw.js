const SHELL='burrow-v1';
const ASSETS=['./','burrow.html','manifest.json','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(SHELL).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim());});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(u.pathname.endsWith('/status')||u.pathname.endsWith('/control')){ return; } // live, never cache
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
