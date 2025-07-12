#!/usr/bin/env python3
"""
Script para testar especificamente o problema do estoque
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Produto, Estoque, User

def verificar_estoque():
    """Verifica o estado do estoque"""
    print("=== VERIFICAÇÃO DO ESTOQUE ===")
    
    with app.app_context():
        try:
            # Verificar se há produtos
            produtos = Produto.query.filter_by(ativo=True).all()
            print(f"📦 Total de produtos ativos: {len(produtos)}")
            
            if not produtos:
                print("❌ Nenhum produto encontrado!")
                return False
            
            # Verificar estoque de cada produto
            for produto in produtos:
                estoque_atual = sum(e.quantidade for e in produto.estoque_items)
                print(f"  - {produto.nome}: {estoque_atual} unidades")
                
                # Mostrar detalhes das entradas de estoque
                if produto.estoque_items:
                    for item in produto.estoque_items:
                        print(f"    → Entrada {item.id}: {item.quantidade} un. (R$ {item.custo_unitario:.2f})")
                else:
                    print("    → Sem entradas de estoque")
            
            return True
                
        except Exception as e:
            print(f"❌ Erro ao verificar estoque: {e}")
            return False

def testar_adicionar_estoque():
    """Testa adicionar estoque a um produto"""
    print("\n=== TESTE DE ADICIONAR ESTOQUE ===")
    
    with app.app_context():
        try:
            # Buscar um produto para testar
            produto = Produto.query.filter_by(ativo=True).first()
            if not produto:
                print("❌ Nenhum produto encontrado para testar!")
                return False
            
            print(f"📝 Testando com produto: {produto.nome}")
            
            # Verificar estoque antes
            estoque_antes = sum(e.quantidade for e in produto.estoque_items)
            print(f"📊 Estoque antes: {estoque_antes} unidades")
            
            # Criar entrada de estoque
            estoque_teste = Estoque(
                produto_id=produto.id,
                quantidade=10,
                custo_unitario=5.50
            )
            
            print(f"➕ Adicionando 10 unidades a R$ 5,50 cada...")
            
            db.session.add(estoque_teste)
            db.session.commit()
            
            print(f"✅ Estoque adicionado! ID: {estoque_teste.id}")
            
            # Verificar estoque depois
            estoque_depois = sum(e.quantidade for e in produto.estoque_items)
            print(f"📊 Estoque depois: {estoque_depois} unidades")
            
            if estoque_depois > estoque_antes:
                print("✅ Estoque foi atualizado corretamente!")
            else:
                print("❌ Estoque não foi atualizado!")
            
            # Remover o estoque de teste
            db.session.delete(estoque_teste)
            db.session.commit()
            print("🧹 Estoque de teste removido")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao testar estoque: {e}")
            db.session.rollback()
            return False

def verificar_tabela_estoque():
    """Verifica se a tabela estoque existe e tem dados"""
    print("\n=== VERIFICAÇÃO DA TABELA ESTOQUE ===")
    
    with app.app_context():
        try:
            # Verificar se a tabela existe
            estoque_count = Estoque.query.count()
            print(f"📋 Total de entradas na tabela estoque: {estoque_count}")
            
            # Listar todas as entradas
            estoque_items = Estoque.query.all()
            if estoque_items:
                print("📋 Entradas de estoque:")
                for item in estoque_items:
                    produto = Produto.query.get(item.produto_id)
                    nome_produto = produto.nome if produto else f"Produto {item.produto_id}"
                    print(f"  - ID: {item.id}, Produto: {nome_produto}, Qtd: {item.quantidade}, Custo: R$ {item.custo_unitario:.2f}")
            else:
                print("  Nenhuma entrada de estoque encontrada")
                
        except Exception as e:
            print(f"❌ Erro ao verificar tabela estoque: {e}")

if __name__ == "__main__":
    print("🔍 INICIANDO TESTE DO SISTEMA DE ESTOQUE")
    print("=" * 50)
    
    # Verificar tabela estoque
    verificar_tabela_estoque()
    
    # Verificar estoque atual
    if verificar_estoque():
        # Testar adicionar estoque
        testar_adicionar_estoque()
    
    print("\n" + "=" * 50)
    print("🏁 TESTE CONCLUÍDO") 