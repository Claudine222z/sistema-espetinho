#!/usr/bin/env python3
"""
Script para testar se o bloqueio do localhost está funcionando
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
        response = requests.get(url, timeout=5, allow_redirects=False)
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"   🔄 Redirecionamento para: {response.headers.get('Location', 'N/A')}")
            print(f"   ✅ Localhost bloqueado e redirecionado!")
        elif response.status_code == 200:
            print(f"   ✅ Acesso permitido")
        else:
            print(f"   ❌ Erro: {response.status_code}")
            
        # Teste 2: Rota de teste específica
        test_url = f"{url}/teste-bloqueio-localhost"
        response = requests.get(test_url, timeout=5, allow_redirects=False)
        
        if response.status_code == 302:
            print(f"   🔄 Rota de teste redirecionada para: {response.headers.get('Location', 'N/A')}")
        elif response.status_code == 200:
            data = response.json()
            print(f"   ✅ Rota de teste: {data.get('message', 'OK')}")
        else:
            print(f"   ❌ Rota de teste: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erro de conexão - servidor não está rodando")
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout - servidor muito lento")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    print("🚀 Teste de Bloqueio Localhost")
    print("=" * 50)
    
    # URLs para testar
    urls_to_test = [
        ("http://localhost:5000", "Localhost (DEVE ser bloqueado)"),
        ("http://127.0.0.1:5000", "127.0.0.1 (DEVE ser bloqueado)"),
        ("http://10.0.0.105:5000", "IP da Rede (DEVE funcionar)")
    ]
    
    for url, description in urls_to_test:
        test_url(url, description)
        time.sleep(1)  # Pequena pausa entre testes
    
    print("\n" + "=" * 50)
    print("📋 Resultado Esperado:")
    print("✅ localhost:5000 -> REDIRECIONADO para 10.0.0.105:5000")
    print("✅ 127.0.0.1:5000 -> REDIRECIONADO para 10.0.0.105:5000")
    print("✅ 10.0.0.105:5000 -> FUNCIONANDO normalmente")
    print("\n🎯 Se os redirecionamentos funcionarem, o problema está resolvido!")

if __name__ == "__main__":
    main() 