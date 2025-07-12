import os
import subprocess
import sys

def gerar_certificados():
    """Gera certificados SSL auto-assinados para HTTPS local"""
    
    # Criar pasta para certificados se não existir
    certs_dir = "certs"
    if not os.path.exists(certs_dir):
        os.makedirs(certs_dir)
    
    print("🔐 Gerando certificados SSL para HTTPS local...")
    
    # Gerar chave privada
    key_path = os.path.join(certs_dir, "key.pem")
    cert_path = os.path.join(certs_dir, "cert.pem")
    
    # Comando para gerar certificado auto-assinado
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:4096", 
        "-keyout", key_path, "-out", cert_path, "-days", "365", 
        "-nodes", "-subj", "/C=BR/ST=SP/L=SaoPaulo/O=Espetinho/CN=localhost"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Certificados gerados com sucesso!")
        print(f"   Chave: {key_path}")
        print(f"   Certificado: {cert_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao gerar certificados: {e}")
        print("💡 Certifique-se de que o OpenSSL está instalado")
        return False
    except FileNotFoundError:
        print("❌ OpenSSL não encontrado no sistema")
        print("💡 Instale o OpenSSL ou use a opção alternativa")
        return False

def verificar_openssl():
    """Verifica se o OpenSSL está instalado"""
    try:
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ OpenSSL encontrado: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

if __name__ == "__main__":
    print("🔍 Verificando OpenSSL...")
    if verificar_openssl():
        gerar_certificados()
    else:
        print("❌ OpenSSL não está instalado")
        print("\n📋 Para instalar o OpenSSL:")
        print("   Windows: Baixe de https://slproweb.com/products/Win32OpenSSL.html")
        print("   Ou use: winget install OpenSSL")
        print("\n💡 Alternativa: Use o Caddy (mais simples)") 