const CACHE_NAME = 'carpintaria-os-v4.5';
const ASSETS_TO_CACHE = [
    '/',
    '/store',
    '/office',
    '/static/css/style.css',
    '/static/assets/js/main.js',
    '/static/images/logo-192.png',
    '/static/Entrada.html',
    '/static/dumbanengue.html',
    '/static/Escritorio.html',
    '/static/manifest.json',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;600&display=swap'
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Precaching assets...');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => self.skipWaiting())
    );
});

// Ativação e limpeza de caches antigos
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('Removing old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Estratégia de Fetch (Network First com Fallback para Cache)
self.addEventListener('fetch', (event) => {
    // Apenas interceptar requisições GET
    if (event.request.method !== 'GET') return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Se a rede funcionar, salvar no cache
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => {
                // Se a rede falhar, tentar o cache
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) return cachedResponse;

                    // Se não estiver no cache e for uma navegação HTML, retornar a Entrada.html
                    if (event.request.headers.get('accept').includes('text/html')) {
                        return caches.match('/static/Entrada.html');
                    }
                });
            })
    );
});
