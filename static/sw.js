// Service Worker para o Sistema Espetinho PWA

const CACHE_NAME = 'espetinho-v3-chrome-fix';
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
    console.log('Service Worker instalando...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Cache aberto');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.log('Erro ao instalar cache:', error);
            })
    );
    self.skipWaiting();
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker ativando...');
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
        }).then(() => {
            return clients.claim();
        })
    );
});

// Interceptar requisições - versão simplificada para evitar problemas
self.addEventListener('fetch', event => {
    // Ignorar requisições chrome-extension e outras não suportadas
    if (event.request.url.startsWith('chrome-extension://') || 
        event.request.url.startsWith('chrome://') ||
        event.request.url.startsWith('moz-extension://') ||
        event.request.url.startsWith('edge://')) {
        return;
    }

    // Ignorar requisições POST, PUT, DELETE
    if (event.request.method !== 'GET') {
        return;
    }

    // Ignorar requisições de navegação (páginas) - deixar passar direto
    if (event.request.mode === 'navigate') {
        return;
    }

    // Ignorar requisições de API e formulários
    if (event.request.url.includes('/api/') || 
        event.request.url.includes('/login') ||
        event.request.url.includes('/logout') ||
        event.request.url.includes('/venda/') ||
        event.request.url.includes('/estoque/') ||
        event.request.url.includes('/produto/')) {
        return;
    }

    // Apenas cachear recursos estáticos
    if (event.request.url.includes('/static/') || 
        event.request.url.includes('cdn.jsdelivr.net') ||
        event.request.url.includes('cdnjs.cloudflare.com')) {
        
        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    // Retornar do cache se disponível
                    if (response) {
                        console.log('Cache hit:', event.request.url);
                        return response;
                    }

                    console.log('Cache miss:', event.request.url);

                    // Se não estiver no cache, buscar da rede
                    return fetch(event.request)
                        .then(response => {
                            // Verificar se a resposta é válida
                            if (!response || response.status !== 200) {
                                return response;
                            }

                            // Clonar a resposta
                            const responseToCache = response.clone();

                            // Adicionar ao cache
                            caches.open(CACHE_NAME)
                                .then(cache => {
                                    cache.put(event.request, responseToCache);
                                    console.log('Adicionado ao cache:', event.request.url);
                                })
                                .catch(error => {
                                    console.log('Erro ao adicionar ao cache:', error);
                                });

                            return response;
                        })
                        .catch(error => {
                            console.log('Erro na requisição:', error);
                            return new Response('Erro de rede', { status: 503 });
                        });
                })
        );
    }
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