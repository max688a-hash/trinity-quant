// TRINITY QUANT 工业级离线缓存与高速 Service Worker
const CACHE_NAME = 'trinity-quant-v1.0.0';
const STATIC_ASSETS = [
  '/',
  '/trinity_dashboard.html',
  '/manifest.json'
];

// 安装阶段：预缓存核心静态文件
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// 激活阶段：清理旧版本缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// 请求拦截：API 接口网络优先 (Network-First)，静态资源缓存优先 (Cache-First)
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 动态 API 接口：网络优先，网络断开时降级报错或返回健康兜底
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({ offline: true, message: "本地离线脱网模式运行中" }),
          { headers: { "Content-Type": "application/json; charset=utf-8" } }
        );
      })
    );
    return;
  }

  // 静态页面及资源：缓存优先，后台更新 (Stale-While-Revalidate)
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
