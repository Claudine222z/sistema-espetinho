#!/usr/bin/env python3
"""
Configuração específica para o Render
Este arquivo garante que o sistema use o IP 10.0.0.105:5000
"""

import os

# Configurações específicas para Render - simular comportamento do IP local
RENDER_CONFIG = {
    'HOST': '0.0.0.0',  # Permitir qualquer host
    'PORT': 5000,
    'SERVER_NAME': None,  # Não forçar nome do servidor
    'PREFERRED_URL_SCHEME': 'https',  # Render usa HTTPS
    'SESSION_COOKIE_SECURE': True,  # HTTPS requer cookies seguros
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'FLASK_ENV': 'production',
    'FLASK_DEBUG': False,
    'HOST_URL': 'https://sistema-espetinho-4.onrender.com'  # URL do Render
}

def apply_render_config(app):
    """Aplica configurações específicas do Render"""
    print("🌐 Aplicando configurações do Render...")
    print(f"📱 Host: {RENDER_CONFIG['HOST']}")
    print(f"🔌 Porta: {RENDER_CONFIG['PORT']}")
    print(f"🌍 Server Name: {RENDER_CONFIG['SERVER_NAME']}")
    
    for key, value in RENDER_CONFIG.items():
        app.config[key] = value
    
    print("✅ Configurações do Render aplicadas com sucesso!")
    return app 