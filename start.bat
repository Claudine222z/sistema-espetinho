@echo off
echo ========================================
echo    Sistema Espetinho - Inicializando
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

REM Verificar se ambiente virtual existe
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate

REM Instalar dependências
echo Instalando dependencias...
pip install -r requirements.txt

REM Criar arquivo .env se não existir
if not exist ".env" (
    echo Criando arquivo de configuração...
    copy env.example .env
    echo Arquivo .env criado! Configure as variáveis se necessário.
)

REM Iniciar o sistema
echo.
echo ========================================
echo    Sistema iniciando...
echo    Acesse: http://localhost:5000
echo    Usuario: admin
echo    Senha: admin123
echo ========================================
echo.

python app.py

pause 