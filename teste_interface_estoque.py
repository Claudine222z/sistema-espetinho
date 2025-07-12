#!/usr/bin/env python3
"""
Script para testar a interface do estoque
"""

import requests
import json

def testar_interface_estoque():
    """Testa a interface web do estoque"""
    
    print("🔍 TESTANDO INTERFACE DO ESTOQUE")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # Criar sessão
        session = requests.Session()
        
        # Fazer login
        print("🔐 Fazendo login...")
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(f"{base_url}/login", data=login_data)
        if response.status_code != 200:
            print(f"❌ Erro no login: {response.status_code}")
            return
        
        print("✅ Login realizado com sucesso")
        
        # Acessar página de estoque
        print("\n📦 Acessando página de estoque...")
        response = session.get(f"{base_url}/estoque")
        if response.status_code == 200:
            print("✅ Página de estoque acessada")
            
            # Verificar se há produtos na página
            if "Situação do Estoque" in response.text:
                print("✅ Tabela de estoque encontrada")
            else:
                print("❌ Tabela de estoque não encontrada")
                
        else:
            print(f"❌ Erro ao acessar estoque: {response.status_code}")
        
        # Acessar página de adicionar estoque
        print("\n➕ Acessando página de adicionar estoque...")
        response = session.get(f"{base_url}/estoque/adicionar")
        if response.status_code == 200:
            print("✅ Página de adicionar estoque acessada")
            
            # Verificar se há produtos no select
            if "Selecione um produto" in response.text:
                print("✅ Select de produtos encontrado")
            else:
                print("❌ Select de produtos não encontrado")
                
        else:
            print(f"❌ Erro ao acessar adicionar estoque: {response.status_code}")
        
        # Testar adicionar estoque via POST
        print("\n📝 Testando adicionar estoque...")
        
        # Primeiro, buscar um produto via API
        response = session.get(f"{base_url}/api/produtos")
        if response.status_code == 200:
            produtos = response.json()
            if produtos:
                produto_teste = produtos[0]
                print(f"✅ Produto encontrado para teste: {produto_teste['nome']}")
                
                # Tentar adicionar estoque
                estoque_data = {
                    'produto_id': produto_teste['id'],
                    'quantidade': '5',
                    'custo_unitario': '10.00'
                }
                
                response = session.post(f"{base_url}/estoque/adicionar", data=estoque_data)
                print(f"📊 Resposta do POST: {response.status_code}")
                
                if response.status_code == 302:  # Redirecionamento
                    print("✅ Redirecionamento após adicionar estoque")
                    
                    # Verificar se foi redirecionado para a página de estoque
                    if "estoque" in response.headers.get('Location', ''):
                        print("✅ Redirecionamento correto para página de estoque")
                    else:
                        print("❌ Redirecionamento incorreto")
                        
                else:
                    print(f"❌ Erro no POST: {response.status_code}")
                    print(f"Resposta: {response.text[:200]}...")
            else:
                print("❌ Nenhum produto encontrado para teste")
        else:
            print(f"❌ Erro ao buscar produtos: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTE DA INTERFACE DO ESTOQUE")
    print("=" * 50)
    
    testar_interface_estoque()
    
    print("\n" + "=" * 50)
    print("🏁 TESTE CONCLUÍDO") 