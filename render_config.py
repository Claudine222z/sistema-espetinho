#!/usr/bin/env python3
"""
Configuração específica para o Render
Este arquivo garante que o sistema use apenas o domínio do Render
"""

import os

# Configurações específicas para Render - usar apenas o domínio do Render
RENDER_CONFIG = {
    'HOST': '0.0.0.0',  # Permitir qualquer host (Render gerencia isso)
    'PORT': 5000,
    'SERVER_NAME': None,  # Não forçar nome do servidor
    'PREFERRED_URL_SCHEME': 'https',  # Render usa HTTPS
    'SESSION_COOKIE_SECURE': True,  # HTTPS requer cookies seguros
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_DOMAIN': None,  # Usar apenas o domínio do Render
    'SESSION_COOKIE_PATH': '/',
    'PERMANENT_SESSION_LIFETIME': 86400,  # 24 horas
    'FLASK_ENV': 'production',
    'FLASK_DEBUG': False,
    'SEND_FILE_MAX_AGE_DEFAULT': 0,  # Desabilita cache
    'TEMPLATES_AUTO_RELOAD': False,  # Não recarregar templates em produção
    'HOST_URL': 'https://sistema-espetinho-4.onrender.com'  # URL do Render
}

def apply_render_config(app):
    """Aplica configurações específicas do Render"""
    print("🌐 Aplicando configurações do Render...")
    print(f"📱 Host: {RENDER_CONFIG['HOST']}")
    print(f"🔌 Porta: {RENDER_CONFIG['PORT']}")
    print(f"🌍 Server Name: {RENDER_CONFIG['SERVER_NAME']}")
    print(f"🔒 HTTPS: {RENDER_CONFIG['PREFERRED_URL_SCHEME']}")
    print(f"🍪 Cookies seguros: {RENDER_CONFIG['SESSION_COOKIE_SECURE']}")
    
    for key, value in RENDER_CONFIG.items():
        app.config[key] = value
    
    print("✅ Configurações do Render aplicadas com sucesso!")
    print("🎯 Sistema configurado para usar apenas o domínio do Render")
    return app 