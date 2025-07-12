#!/usr/bin/env python3
"""
Script para iniciar o Sistema Espetinho com suporte completo à câmera
Este script configura HTTPS local automaticamente para garantir que a câmera funcione em todos os navegadores
"""

import os
import sys
import subprocess
import time

def verificar_dependencias():
    """Verifica se as dependências necessárias estão instaladas"""
    print("🔍 Verificando dependências...")
    
    # Verificar Python
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Verificar OpenSSL
    try:
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ OpenSSL: {result.stdout.strip()}")
            return True
        else:
            print("❌ OpenSSL não encontrado")
            return False
    except FileNotFoundError:
        print("❌ OpenSSL não encontrado")
        return False

def gerar_certificados_ssl():
    """Gera certificados SSL auto-assinados"""
    print("🔐 Gerando certificados SSL...")
    
    # Criar pasta para certificados
    certs_dir = "certs"
    if not os.path.exists(certs_dir):
        os.makedirs(certs_dir)
    
    key_path = os.path.join(certs_dir, "key.pem")
    cert_path = os.path.join(certs_dir, "cert.pem")
    
    # Comando para gerar certificado
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096", 
        "-keyout", key_path, "-out", cert_path, "-days", "365", 
        "-nodes", "-subj", "/C=BR/ST=SP/L=SaoPaulo/O=Espetinho/CN=localhost"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Certificados SSL gerados com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao gerar certificados: {e}")
        return False

def obter_ip_local():
    """Obtém o IP local da máquina"""
    import socket
    try:
        # Conectar a um endereço externo para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "10.0.0.105"  # IP padrão se não conseguir detectar

def main():
    print("🚀 Sistema Espetinho - Inicialização com Câmera")
    print("=" * 50)
    
    # Verificar dependências
    if not verificar_dependencias():
        print("\n❌ Dependências não atendidas!")
        print("📋 Para instalar o OpenSSL:")
        print("   Windows: winget install OpenSSL")
        print("   Ou baixe de: https://slproweb.com/products/Win32OpenSSL.html")
        return
    
    # Verificar se os certificados já existem
    cert_path = 'certs/cert.pem'
    key_path = 'certs/key.pem'
    
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        print("\n🔐 Certificados SSL não encontrados. Gerando...")
        if not gerar_certificados_ssl():
            print("❌ Falha ao gerar certificados SSL")
            return
    else:
        print("✅ Certificados SSL já existem")
    
    # Obter IP local
    ip_local = obter_ip_local()
    
    print("\n🎯 Configuração final:")
    print(f"   Local: https://localhost:5000")
    print(f"   Rede:  https://{ip_local}:5000")
    print("   Login: admin / admin123")
    
    print("\n⚠️  IMPORTANTE:")
    print("   - Aceite o aviso de certificado não confiável no navegador")
    print("   - A câmera funcionará em TODOS os navegadores e dispositivos")
    print("   - O sistema estará disponível em toda a rede local")
    
    print("\n🚀 Iniciando o sistema...")
    print("=" * 50)
    
    # Aguardar um pouco para o usuário ler
    time.sleep(2)
    
    # Importar e executar o app
    try:
        from app import app
        with app.app_context():
            app.run(debug=True, host='0.0.0.0', port=5000, 
                   ssl_context=(cert_path, key_path))
    except KeyboardInterrupt:
        print("\n👋 Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar o sistema: {e}")

if __name__ == "__main__":
    main() 