// Service Worker para o Sistema Espetinho PWA

const CACHE_NAME = 'espetinho-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Instalar Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Cache aberto');
                return cache.addAll(urlsToCache);
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Retornar do cache se disponível
                if (response) {
                    return response;
                }

                // Se não estiver no cache, buscar da rede
                return fetch(event.request)
                    .then(response => {
                        // Verificar se a resposta é válida
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clonar a resposta
                        const responseToCache = response.clone();

                        // Adicionar ao cache
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // Se offline e não estiver no cache, retornar página offline
                        if (event.request.destination === 'document') {
                            return caches.match('/offline.html');
                        }
                    });
            })
    );
});

// Sincronização em background
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

// Notificações push
self.addEventListener('push', event => {
    const options = {
        body: event.data ? event.data.text() : 'Nova notificação do Sistema Espetinho',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-192x192.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'Ver detalhes',
                icon: '/static/icons/icon-192x192.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/icons/icon-192x192.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Sistema Espetinho', options)
    );
});

// Clique em notificação
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Função para sincronização em background
function doBackgroundSync() {
    // Implementar sincronização de dados offline
    console.log('Sincronizando dados em background...');
    
    // Exemplo: sincronizar vendas offline
    return new Promise((resolve) => {
        // Aqui você pode implementar a lógica para sincronizar
        // dados que foram salvos offline
        setTimeout(() => {
            console.log('Sincronização concluída');
            resolve();
        }, 1000);
    });
}

// Mensagens do cliente
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

// Atualização automática do Service Worker
self.addEventListener('install', event => {
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(clients.claim());
}); 