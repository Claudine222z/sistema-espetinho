#!/bin/bash

echo "========================================"
echo "   Sistema Espetinho - Inicializando"
echo "========================================"
echo

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 não encontrado!"
    echo "Instale o Python 3.8+ e tente novamente."
    exit 1
fi

# Verificar se ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Criar arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo "Criando arquivo de configuração..."
    cp env.example .env
    echo "Arquivo .env criado! Configure as variáveis se necessário."
fi

# Iniciar o sistema
echo
echo "========================================"
echo "   Sistema iniciando..."
echo "   Acesse: http://localhost:5000"
echo "   Usuário: admin"
echo "   Senha: admin123"
echo "========================================"
echo

python app.py 