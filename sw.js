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

// 系统原生通知点击交互：唤醒或前台置顶 TRINITY QUANT
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('trinity_dashboard') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/trinity_dashboard.html');
      }
    })
  );
});

// 监听前台或后台分发的原生系统级锁屏通知
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { title, body, icon, tag } = event.data;
    self.registration.showNotification(title || 'TRINITY QUANT 顶级量化预警', {
      body: body || '量化雷达捕捉到核心造血信号或风控异动',
      icon: icon || '/data/icon-192.png',
      badge: '/data/icon-192.png',
      tag: tag || 'trinity-alert',
      vibrate: [200, 100, 200],
      requireInteraction: true,
      data: { url: '/trinity_dashboard.html' }
    });
  }
});
