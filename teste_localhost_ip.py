#!/usr/bin/env python3
"""
Script para testar se o problema localhost vs IP foi resolvido
"""

import requests
import json
import time

def test_url(url, description):
    """Testa uma URL específica"""
    print(f"\n🔍 Testando: {description}")
    print(f"   URL: {url}")
    
    try:
        # Teste 1: Acesso básico
        response = requests.get(url, timeout=5)
        print(f"   ✅ Status: {response.status_code}")
        
        # Teste 2: Rota de teste específica
        test_url = f"{url}/teste-localhost-ip"
        response = requests.get(test_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Teste específico: OK")
            print(f"   📊 Host detectado: {data.get('host', 'N/A')}")
        else:
            print(f"   ❌ Teste específico: {response.status_code}")
            
        # Teste 3: Verificar se é redirecionamento para login
        if response.status_code in [200, 302]:
            print(f"   ✅ Acesso funcionando")
        else:
            print(f"   ❌ Erro de acesso")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erro de conexão - servidor não está rodando")
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout - servidor muito lento")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    print("🚀 Teste de Compatibilidade localhost vs IP")
    print("=" * 50)
    
    # URLs para testar
    urls_to_test = [
        ("http://localhost:5000", "Localhost"),
        ("http://127.0.0.1:5000", "127.0.0.1"),
        ("http://10.0.0.105:5000", "IP da Rede")
    ]
    
    for url, description in urls_to_test:
        test_url(url, description)
        time.sleep(1)  # Pequena pausa entre testes
    
    print("\n" + "=" * 50)
    print("📋 Instruções:")
    print("1. Certifique-se de que o servidor está rodando: python app.py")
    print("2. Execute este script: python teste_localhost_ip.py")
    print("3. Se todos os testes passarem, o problema foi resolvido!")
    print("4. Se algum falhar, verifique se o servidor está rodando no host correto")

if __name__ == "__main__":
    main() 