/* 농마니 앱: 홈 화면 설치용. 화면 파일만 저장하고, 주문·입찰 자료는 항상 서버에서 새로 받습니다. */
const V = "nm-app-4";
const SHELL = ["./", "index.html", "nm-claude.js", "vendor/supabase.js", "manifest.webmanifest", "icon.svg", "icon-192.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return; // Supabase 등 외부 요청은 그대로
  // 화면 파일(html·js)은 매번 서버에 새 버전이 있는지 확인 (옛 화면이 남지 않게)
  const go = (e.request.mode === "navigate" || /\.(html|js)$/.test(u.pathname)) ? fetch(u.href, { cache: "no-cache", credentials: "same-origin" }) : fetch(e.request);
  e.respondWith(go.then(r => { const c = r.clone(); caches.open(V).then(x => x.put(e.request, c)); return r; })
    .catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match("index.html"))));
});
