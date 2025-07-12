#!/usr/bin/env python3
"""
Configuração específica para o Render
Este arquivo garante que o sistema use o IP 10.0.0.105:5000
"""

import os

# Configurações específicas para Render
RENDER_CONFIG = {
    'HOST': '10.0.0.105',
    'PORT': 5000,
    'SERVER_NAME': '10.0.0.105:5000',
    'PREFERRED_URL_SCHEME': 'http',
    'SESSION_COOKIE_SECURE': False,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'FLASK_ENV': 'production',
    'FLASK_DEBUG': False
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