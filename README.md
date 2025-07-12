# 🍖 Sistema Espetinho

Sistema completo de gerenciamento para ponto de espetinho com suporte a câmera para leitura de código de barras.

## ✨ Funcionalidades

- 📊 **Dashboard** com estatísticas em tempo real
- 🛒 **Gestão de Vendas** com múltiplas formas de pagamento
- 📦 **Controle de Estoque** com alertas de baixo estoque
- 📷 **Leitor de Código de Barras** com câmera
- 📈 **Relatórios** detalhados de vendas e lucratividade
- 👥 **Sistema de Usuários** com diferentes níveis de acesso
- 📱 **PWA** (Progressive Web App) para uso offline
- 🔐 **HTTPS Local** para câmera em todos os navegadores

## 🚀 Como Usar

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/sistema-espetinho.git
cd sistema-espetinho

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o sistema (com câmera)
python iniciar_com_camera.py
```

### Acesso

- **Local**: `https://localhost:5000`
- **Rede**: `https://[SEU_IP]:5000`
- **Login**: `admin` / `admin123`

## 📱 Câmera em Todos os Navegadores

O sistema inclui configuração automática de HTTPS local para garantir que a câmera funcione em **todos os navegadores e dispositivos** da rede.

### Para ativar a câmera:

```bash
# Opção automática (recomendado)
python iniciar_com_camera.py

# Opção manual
python gerar_certificados.py
python app.py
```

📖 [Guia completo da câmera](README_CAMERA.md)

## 🛠️ Tecnologias

- **Backend**: Flask, SQLAlchemy
- **Frontend**: Bootstrap 5, JavaScript
- **Câmera**: QuaggaJS
- **PWA**: Service Workers
- **HTTPS**: OpenSSL (auto-configurado)

## 📋 Estrutura do Projeto

```
espetinho/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências Python
├── iniciar_com_camera.py # Script de inicialização com HTTPS
├── templates/            # Templates HTML
├── static/              # Arquivos estáticos (CSS, JS, ícones)
├── instance/            # Banco de dados SQLite
└── README_CAMERA.md     # Documentação da câmera
```

## 👥 Níveis de Acesso

- **Admin**: Acesso total ao sistema
- **Gerente**: Gestão de produtos, estoque e relatórios
- **Vendedor**: Apenas vendas e visualização básica

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development
```

### Banco de Dados

O sistema cria automaticamente o banco SQLite na primeira execução.

## 📊 Funcionalidades Principais

### Dashboard
- Vendas do dia
- Produtos com estoque baixo
- Estatísticas em tempo real

### Vendas
- Múltiplas formas de pagamento
- Descontos
- Histórico completo

### Estoque
- Controle de entrada/saída
- Alertas automáticos
- Custo unitário

### Código de Barras
- Leitura por câmera
- Busca manual
- Cadastro automático de produtos

### Relatórios
- Vendas por período
- Lucratividade
- Produtos mais vendidos

## 🌐 Deploy

### Local (Desenvolvimento)
```bash
python app.py
```

### Produção (com HTTPS)
```bash
python iniciar_com_camera.py
```

### Heroku
```bash
# O projeto já está configurado para Heroku
git push heroku main
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Se encontrar algum problema:

1. Verifique a [documentação da câmera](README_CAMERA.md)
2. Abra uma [issue](https://github.com/seu-usuario/sistema-espetinho/issues)
3. Consulte as [FAQ](https://github.com/seu-usuario/sistema-espetinho/wiki/FAQ)

---

**Desenvolvido com ❤️ para facilitar a gestão de pontos de espetinho!** 