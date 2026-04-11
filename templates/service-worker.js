const CACHE_NAME = "saleshub-v29";

const APP_SHELL_URLS = [
    "/",
    "/sales/pos/",
    "/sales/pos-offline-shell/",
    "/static/manifest.json",
    "/static/css/app.css",
    "/static/js/offline-db.js",
    "/static/js/pos-engine.js"
];

self.addEventListener("install", event => {
    event.waitUntil((async () => {
        const cache = await caches.open(CACHE_NAME);

        for (const url of APP_SHELL_URLS) {
            try {
                const response = await fetch(url, { cache: "no-store" });
                if (response.ok) {
                    await cache.put(url, response.clone());
                }
            } catch (error) {
                console.warn("Failed to precache:", url, error);
            }
        }

        await self.skipWaiting();
    })());
});

self.addEventListener("activate", event => {
    event.waitUntil((async () => {
        const keys = await caches.keys();

        await Promise.all(
            keys.map(key => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            })
        );

        await self.clients.claim();
    })());
});

self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== "GET") return;

    if (request.mode === "navigate") {
        event.respondWith((async () => {
            const cache = await caches.open(CACHE_NAME);

            try {
                const networkResponse = await fetch(request);
                if (networkResponse && networkResponse.ok) {
                    await cache.put(request.url, networkResponse.clone());
                }
                return networkResponse;
            } catch (error) {
                if (url.pathname === "/sales/pos/" || url.pathname.startsWith("/sales/pos")) {
                    const cachedOfflinePOS = await cache.match("/sales/pos-offline-shell/");
                    if (cachedOfflinePOS) return cachedOfflinePOS;
                }

                const cachedByUrl = await cache.match(request.url);
                if (cachedByUrl) return cachedByUrl;

                const cachedHome = await cache.match("/");
                if (cachedHome) return cachedHome;

                return new Response(
                    `
                    <!DOCTYPE html>
                    <html lang="ar" dir="rtl">
                    <head>
                        <meta charset="UTF-8">
                        <title>غير متصل</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                padding: 24px;
                                background: #f8f9fa;
                                color: #111;
                            }
                            .box {
                                max-width: 600px;
                                margin: 40px auto;
                                background: #fff;
                                padding: 24px;
                                border-radius: 12px;
                                border: 1px solid #ddd;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="box">
                            <h2>لا يوجد اتصال بالإنترنت</h2>
                            <p>صفحة نقطة البيع غير متوفرة في الكاش بعد.</p>
                            <p>افتح صفحة POS مرة واحدة أثناء وجود الإنترنت ثم أعد المحاولة.</p>
                        </div>
                    </body>
                    </html>
                    `,
                    {
                        headers: { "Content-Type": "text/html; charset=utf-8" }
                    }
                );
            }
        })());
        return;
    }

    if (url.origin === self.location.origin) {
        event.respondWith((async () => {
            const cache = await caches.open(CACHE_NAME);

            const cachedResponse = await cache.match(request.url);
            if (cachedResponse) return cachedResponse;

            try {
                const networkResponse = await fetch(request);
                if (networkResponse && networkResponse.ok) {
                    await cache.put(request.url, networkResponse.clone());
                }
                return networkResponse;
            } catch (error) {
                return new Response("", { status: 504, statusText: "Offline" });
            }
        })());
        return;
    }

    event.respondWith((async () => {
        try {
            return await fetch(request);
        } catch (error) {
            return new Response("", { status: 504, statusText: "Offline" });
        }
    })());
});