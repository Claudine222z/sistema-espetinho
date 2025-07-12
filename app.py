from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

# Configuração específica para garantir banco único
app = Flask(__name__, instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')

# Usar caminho absoluto para o banco de dados
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
db_path = os.path.join(instance_path, 'espetinho.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração unificada - funciona em qualquer ambiente
is_render = os.environ.get('RENDER', False)

if is_render:
    # Configuração específica para Render - simular comportamento do IP local
    app.config['SERVER_NAME'] = None
    app.config['PREFERRED_URL_SCHEME'] = 'https'  # Render usa HTTPS
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    print("🌐 Configuração RENDER ativada - simula comportamento do IP local")
else:
    # Configuração para desenvolvimento local
    app.config['SERVER_NAME'] = None  # Aceita qualquer hostname
    app.config['PREFERRED_URL_SCHEME'] = 'http'  # Usa HTTP por padrão
    app.config['SESSION_COOKIE_SECURE'] = False  # Não força HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_DOMAIN'] = None  # Permite qualquer domínio
    app.config['SESSION_COOKIE_PATH'] = '/'
    print("🌐 Configuração LOCAL ativada")

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Middleware para adicionar headers CORS e resolver problemas de sessão
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # Headers anti-cache fortes
    response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', '0')
    
    # Garantir que cookies de sessão funcionem em todos os hosts
    if 'Set-Cookie' in response.headers:
        # Remover domínio específico dos cookies se existir
        cookies = response.headers.getlist('Set-Cookie')
        new_cookies = []
        for cookie in cookies:
            if 'Domain=' in cookie:
                # Remover especificação de domínio
                cookie = cookie.split('; Domain=')[0]
            new_cookies.append(cookie)
        response.headers.setlist('Set-Cookie', new_cookies)
    
    return response

# Modelos do banco de dados
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='vendedor')  # 'admin', 'gerente', 'vendedor'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'espetinho', 'bebida', 'porcao'
    preco_padrao = db.Column(db.Float, nullable=False)
    preco_custo = db.Column(db.Float, nullable=False, default=0.0)  # Preço de compra
    margem_lucro = db.Column(db.Float, nullable=False, default=30.0)  # Margem de lucro em %
    preco_sugerido = db.Column(db.Float, nullable=False, default=0.0)  # Preço calculado automaticamente
    descricao = db.Column(db.Text)
    codigo_barras = db.Column(db.String(50), unique=True)  # Código de barras único
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calcular_preco_sugerido(self):
        """Calcula o preço sugerido baseado no custo e margem de lucro"""
        if self.preco_custo > 0:
            self.preco_sugerido = self.preco_custo * (1 + self.margem_lucro / 100)
        return self.preco_sugerido
    
    def calcular_lucro_atual(self):
        """Calcula o lucro atual baseado no preço de venda e custo"""
        if self.preco_custo > 0:
            return self.preco_padrao - self.preco_custo
        return 0
    
    def calcular_margem_atual(self):
        """Calcula a margem de lucro atual em %"""
        if self.preco_custo > 0:
            return ((self.preco_padrao - self.preco_custo) / self.preco_custo) * 100
        return 0

class Estoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_entrada = db.Column(db.DateTime, default=datetime.utcnow)
    custo_unitario = db.Column(db.Float, nullable=False)
    produto = db.relationship('Produto', backref='estoque_items')

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    valor_total = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0)
    forma_pagamento = db.Column(db.String(50), default='dinheiro')
    observacoes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='vendas')

class ItemVenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    preco_total = db.Column(db.Float, nullable=False)
    venda = db.relationship('Venda', backref='itens')
    produto = db.relationship('Produto', backref='vendas')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Funções de controle de acesso
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acesso negado. Apenas administradores podem acessar esta área.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def gerente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'gerente']:
            flash('Acesso negado. Apenas gerentes e administradores podem acessar esta área.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def can_view_sales_details():
    """Verifica se o usuário pode ver detalhes das vendas"""
    return current_user.role in ['admin', 'gerente']

# Rotas principais
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)  # Forçar remember=True
            # Garantir que a sessão seja salva
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Estatísticas do dashboard baseadas no papel do usuário
    hoje = datetime.today()
    
    if current_user.role == 'admin':
        # Admin vê todas as vendas do dia
        vendas_hoje = Venda.query.filter(
            db.func.date(Venda.data_venda) == hoje.date()
        ).all()
    elif current_user.role == 'gerente':
        # Gerente vê todas as vendas do dia
        vendas_hoje = Venda.query.filter(
            db.func.date(Venda.data_venda) == hoje.date()
        ).all()
    else:
        # Vendedor vê apenas suas vendas do dia
        vendas_hoje = Venda.query.filter(
            db.func.date(Venda.data_venda) == hoje.date(),
            Venda.user_id == current_user.id
        ).all()
    
    total_hoje = sum(v.valor_total for v in vendas_hoje)
    qtd_vendas_hoje = len(vendas_hoje)
    
    # Produtos com estoque baixo (apenas para admin e gerente)
    produtos_baixo_estoque = []
    if current_user.role in ['admin', 'gerente']:
        for produto in Produto.query.filter_by(ativo=True).all():
            estoque_atual = sum(e.quantidade for e in produto.estoque_items)
            if estoque_atual <= 5:  # Alerta para estoque baixo
                produtos_baixo_estoque.append({
                    'produto': produto,
                    'estoque': estoque_atual
                })
    
    return render_template('dashboard.html', 
                         total_hoje=total_hoje,
                         qtd_vendas_hoje=qtd_vendas_hoje,
                         produtos_baixo_estoque=produtos_baixo_estoque,
                         user_role=current_user.role)

# Rotas de produtos
@app.route('/produtos')
@login_required
def produtos():
    produtos_list = Produto.query.filter_by(ativo=True).all()
    
    # Adicionar informações de estoque e lucratividade para cada produto
    for produto in produtos_list:
        produto.estoque_atual = sum(e.quantidade for e in produto.estoque_items)
        produto.lucro_atual = produto.calcular_lucro_atual()
        produto.margem_atual = produto.calcular_margem_atual()
    
    return render_template('produtos.html', produtos=produtos_list)

@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    # Verificar se o usuário tem permissão para cadastrar produtos
    if current_user.role not in ['admin', 'gerente']:
        flash('Você não tem permissão para cadastrar produtos!', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        try:
            nome = request.form['nome']
            tipo = request.form['tipo']
            preco_padrao = float(request.form['preco_padrao'])
            preco_custo = float(request.form.get('preco_custo', 0))
            margem_lucro = float(request.form.get('margem_lucro', 30))
            descricao = request.form['descricao']
            codigo_barras = request.form.get('codigo_barras', '').strip()
            
            # Verificar se o código de barras já existe
            if codigo_barras and Produto.query.filter_by(codigo_barras=codigo_barras, ativo=True).first():
                flash('Código de barras já cadastrado para outro produto!', 'error')
                return render_template('novo_produto.html')
            
            produto = Produto(
                nome=nome,
                tipo=tipo,
                preco_padrao=preco_padrao,
                preco_custo=preco_custo,
                margem_lucro=margem_lucro,
                descricao=descricao,
                codigo_barras=codigo_barras if codigo_barras else None
            )
            
            # Calcular preço sugerido
            produto.calcular_preco_sugerido()
            
            db.session.add(produto)
            db.session.commit()
            
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('produtos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar produto: {str(e)}', 'error')
            return render_template('novo_produto.html')
    
    return render_template('novo_produto.html')

@app.route('/produto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = request.form['tipo']
        preco_padrao = float(request.form['preco_padrao'])
        preco_custo = float(request.form.get('preco_custo', 0))
        margem_lucro = float(request.form.get('margem_lucro', 30))
        descricao = request.form['descricao']
        codigo_barras = request.form.get('codigo_barras', '').strip()
        
        # Verificar se o código de barras já existe (exceto para o próprio produto)
        if codigo_barras:
            produto_existente = Produto.query.filter_by(codigo_barras=codigo_barras, ativo=True).first()
            if produto_existente and produto_existente.id != produto.id:
                flash('Código de barras já cadastrado para outro produto!', 'error')
                return render_template('editar_produto.html', produto=produto)
        
        produto.nome = nome
        produto.tipo = tipo
        produto.preco_padrao = preco_padrao
        produto.preco_custo = preco_custo
        produto.margem_lucro = margem_lucro
        produto.descricao = descricao
        produto.codigo_barras = codigo_barras if codigo_barras else None
        
        # Recalcular preço sugerido
        produto.calcular_preco_sugerido()
        
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('produtos'))
    
    return render_template('editar_produto.html', produto=produto)

@app.route('/produto/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    
    # Verificar se o produto tem vendas associadas
    if produto.vendas:
        return jsonify({'success': False, 'message': 'Não é possível excluir um produto que possui vendas associadas.'}), 400
    
    # Verificar se o produto tem estoque
    estoque_atual = sum(e.quantidade for e in produto.estoque_items)
    if estoque_atual > 0:
        return jsonify({'success': False, 'message': 'Não é possível excluir um produto que possui estoque. Remova o estoque primeiro.'}), 400
    
    # Marcar como inativo em vez de deletar (soft delete)
    produto.ativo = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Produto excluído com sucesso!'})

@app.route('/produto/<int:id>/zerar-estoque', methods=['POST'])
@login_required
def zerar_estoque(id):
    produto = Produto.query.get_or_404(id)
    
    # Zerar todo o estoque do produto
    estoque_items = Estoque.query.filter_by(produto_id=id).all()
    for item in estoque_items:
        item.quantidade = 0
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Estoque zerado com sucesso!'})

@app.route('/codigo-barras')
@login_required
def codigo_barras():
    return render_template('codigo_barras.html')

@app.route('/api/buscar-produto-codigo/<codigo>')
@login_required
def buscar_produto_codigo(codigo):
    # Buscar produto por código de barras
    produto = Produto.query.filter_by(codigo_barras=codigo, ativo=True).first()
    
    if produto:
        return jsonify({
            'success': True,
            'codigo': codigo,
            'produto': {
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'preco_padrao': produto.preco_padrao,
                'descricao': produto.descricao
            },
            'message': 'Produto encontrado'
        })
    else:
        return jsonify({
            'success': False,
            'codigo': codigo,
            'produto': None,
            'message': 'Produto não encontrado com este código de barras'
        })

@app.route('/api/calcular-preco-sugerido', methods=['POST'])
@login_required
def calcular_preco_sugerido():
    """Calcula o preço sugerido baseado no custo e margem de lucro"""
    try:
        data = request.get_json()
        preco_custo = float(data.get('preco_custo', 0))
        margem_lucro = float(data.get('margem_lucro', 30))
        
        if preco_custo > 0:
            preco_sugerido = preco_custo * (1 + margem_lucro / 100)
            lucro_unitario = preco_sugerido - preco_custo
            
            return jsonify({
                'success': True,
                'preco_sugerido': round(preco_sugerido, 2),
                'lucro_unitario': round(lucro_unitario, 2),
                'margem_lucro': margem_lucro
            })
        else:
            return jsonify({
                'success': False,
                'mensagem': 'Preço de custo deve ser maior que zero'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'mensagem': f'Erro ao calcular: {str(e)}'
        })

# Rotas de estoque
@app.route('/estoque')
@login_required
def estoque():
    produtos = Produto.query.filter_by(ativo=True).all()
    estoque_data = []
    
    for produto in produtos:
        # Buscar estoque diretamente
        estoque_items = Estoque.query.filter_by(produto_id=produto.id).all()
        estoque_atual = sum(e.quantidade for e in estoque_items)
        
        estoque_data.append({
            'produto': produto,
            'quantidade': estoque_atual
        })
    
    return render_template('estoque.html', estoque_data=estoque_data)

@app.route('/estoque/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_estoque():
    if request.method == 'POST':
        try:
            produto_id = int(request.form['produto_id'])
            quantidade = int(request.form['quantidade'])
            custo_unitario = float(request.form['custo_unitario'])
            
            # Verificar se o produto existe
            produto = Produto.query.get(produto_id)
            if not produto:
                flash('Produto não encontrado!', 'error')
                return redirect(url_for('adicionar_estoque'))
            
            estoque = Estoque(
                produto_id=produto_id,
                quantidade=quantidade,
                custo_unitario=custo_unitario
            )
            
            db.session.add(estoque)
            db.session.commit()
            
            flash('Estoque adicionado com sucesso!', 'success')
            return redirect(url_for('estoque'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar estoque: {str(e)}', 'error')
            return redirect(url_for('adicionar_estoque'))
    
    produtos = Produto.query.filter_by(ativo=True).all()
    produto_selecionado = request.args.get('produto_id')
    
    return render_template('adicionar_estoque.html', 
                         produtos=produtos, 
                         produto_selecionado=produto_selecionado)

# Rotas de vendas
@app.route('/vendas')
@login_required
def vendas():
    # Filtrar vendas baseado no papel do usuário
    if current_user.role == 'admin':
        # Admin vê todas as vendas
        vendas_list = Venda.query.order_by(Venda.data_venda.desc()).limit(50).all()
    elif current_user.role == 'gerente':
        # Gerente vê vendas dos últimos 7 dias
        data_limite = datetime.now() - timedelta(days=7)
        vendas_list = Venda.query.filter(Venda.data_venda >= data_limite).order_by(Venda.data_venda.desc()).all()
    else:
        # Vendedor vê apenas suas próprias vendas dos últimos 3 dias
        data_limite = datetime.now() - timedelta(days=3)
        vendas_list = Venda.query.filter(
            Venda.user_id == current_user.id,
            Venda.data_venda >= data_limite
        ).order_by(Venda.data_venda.desc()).all()
    
    return render_template('vendas.html', vendas=vendas_list, can_view_details=can_view_sales_details())

@app.route('/venda/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    if request.method == 'POST':
        data = request.get_json()
        
        # Criar venda
        venda = Venda(
            valor_total=data['valor_total'],
            desconto=data.get('desconto', 0),
            forma_pagamento=data.get('forma_pagamento', 'dinheiro'),
            observacoes=data.get('observacoes', ''),
            user_id=current_user.id
        )
        
        db.session.add(venda)
        db.session.flush()  # Para obter o ID da venda
        
        # Adicionar itens da venda
        for item_data in data['itens']:
            item = ItemVenda(
                venda_id=venda.id,
                produto_id=item_data['produto_id'],
                quantidade=item_data['quantidade'],
                preco_unitario=item_data['preco_unitario'],
                preco_total=item_data['preco_total']
            )
            db.session.add(item)
            
            # Atualizar estoque
            estoque_items = Estoque.query.filter_by(produto_id=item_data['produto_id']).all()
            qtd_restante = item_data['quantidade']
            
            for estoque_item in estoque_items:
                if qtd_restante <= 0:
                    break
                if estoque_item.quantidade >= qtd_restante:
                    estoque_item.quantidade -= qtd_restante
                    qtd_restante = 0
                else:
                    qtd_restante -= estoque_item.quantidade
                    estoque_item.quantidade = 0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'venda_id': venda.id,
            'message': 'Venda registrada com sucesso!'
        })
    
    produtos = Produto.query.filter_by(ativo=True).all()
    return render_template('nova_venda.html', produtos=produtos)

# APIs
@app.route('/api/produtos')
@login_required
def api_produtos():
    produtos = Produto.query.filter_by(ativo=True).all()
    return jsonify([{
        'id': p.id,
        'nome': p.nome,
        'tipo': p.tipo,
        'preco_padrao': p.preco_padrao,
        'descricao': p.descricao
    } for p in produtos])

@app.route('/api/produto/<int:id>')
@login_required
def api_produto(id):
    produto = Produto.query.get_or_404(id)
    return jsonify({
        'id': produto.id,
        'nome': produto.nome,
        'tipo': produto.tipo,
        'preco_padrao': produto.preco_padrao,
        'descricao': produto.descricao
    })

# Rotas de relatórios
@app.route('/relatorios')
@gerente_required
def relatorios():
    return render_template('relatorios.html')

@app.route('/api/relatorio/vendas')
@gerente_required
def api_relatorio_vendas():
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Query base
        query = Venda.query
        
        # Aplicar filtros de data se fornecidos
        if data_inicio:
            query = query.filter(Venda.data_venda >= datetime.strptime(data_inicio, '%Y-%m-%d'))
        if data_fim:
            query = query.filter(Venda.data_venda <= datetime.strptime(data_fim + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        # Ordenar por data
        vendas = query.order_by(Venda.data_venda.desc()).all()
        
        # Preparar dados para o relatório
        dados_vendas = []
        for venda in vendas:
            dados_vendas.append({
                'id': venda.id,
                'data': venda.data_venda.strftime('%d/%m/%Y %H:%M'),
                'valor_total': venda.valor_total,
                'desconto': venda.desconto,
                'valor_liquido': venda.valor_total - venda.desconto,
                'forma_pagamento': venda.forma_pagamento,
                'vendedor': venda.user.nome,
                'observacoes': venda.observacoes or '',
                'itens': [{
                    'produto': item.produto.nome,
                    'quantidade': item.quantidade,
                    'preco_unitario': item.preco_unitario,
                    'preco_total': item.preco_total
                } for item in venda.itens]
            })
        
        # Calcular totais
        total_vendas = len(dados_vendas)
        total_receita = sum(v['valor_liquido'] for v in dados_vendas)
        total_descontos = sum(v['desconto'] for v in dados_vendas)
        
        return jsonify({
            'success': True,
            'vendas': dados_vendas,
            'resumo': {
                'total_vendas': total_vendas,
                'total_receita': total_receita,
                'total_descontos': total_descontos
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/debug/estoque')
@login_required
def debug_estoque():
    """Rota de debug para verificar dados do estoque"""
    try:
        produtos = Produto.query.filter_by(ativo=True).all()
        debug_data = []
        
        for produto in produtos:
            estoque_items = Estoque.query.filter_by(produto_id=produto.id).all()
            estoque_total = sum(e.quantidade for e in estoque_items)
            
            debug_data.append({
                'produto_id': produto.id,
                'produto_nome': produto.nome,
                'estoque_total': estoque_total,
                'estoque_items': [{
                    'id': item.id,
                    'quantidade': item.quantidade,
                    'custo_unitario': item.custo_unitario,
                    'data_entrada': item.data_entrada.strftime('%d/%m/%Y %H:%M')
                } for item in estoque_items]
            })
        
        return jsonify({
            'success': True,
            'debug_data': debug_data,
            'total_produtos': len(debug_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/relatorio/lucratividade')
@gerente_required
def api_relatorio_lucratividade():
    try:
        produtos = Produto.query.filter_by(ativo=True).all()
        dados_lucratividade = []
        
        for produto in produtos:
            # Calcular dados de vendas
            vendas_produto = ItemVenda.query.filter_by(produto_id=produto.id).all()
            qtd_vendida = sum(v.quantidade for v in vendas_produto)
            receita_total = sum(v.preco_total for v in vendas_produto)
            
            # Calcular custo total
            estoque_items = Estoque.query.filter_by(produto_id=produto.id).all()
            qtd_comprada = sum(e.quantidade for e in estoque_items)
            custo_total = sum(e.quantidade * e.custo_unitario for e in estoque_items)
            
            # Calcular lucro
            lucro_total = receita_total - custo_total
            margem_lucro = (lucro_total / custo_total * 100) if custo_total > 0 else 0
            
            dados_lucratividade.append({
                'produto_id': produto.id,
                'produto_nome': produto.nome,
                'tipo': produto.tipo,
                'preco_padrao': produto.preco_padrao,
                'preco_custo': produto.preco_custo,
                'qtd_vendida': qtd_vendida,
                'qtd_comprada': qtd_comprada,
                'receita_total': receita_total,
                'custo_total': custo_total,
                'lucro_total': lucro_total,
                'margem_lucro': margem_lucro
            })
        
        # Calcular totais
        total_receita = sum(p['receita_total'] for p in dados_lucratividade)
        total_custo = sum(p['custo_total'] for p in dados_lucratividade)
        total_lucro = sum(p['lucro_total'] for p in dados_lucratividade)
        margem_geral = (total_lucro / total_custo * 100) if total_custo > 0 else 0
        
        return jsonify({
            'success': True,
            'produtos': dados_lucratividade,
            'resumo': {
                'total_receita': total_receita,
                'total_custo': total_custo,
                'total_lucro': total_lucro,
                'margem_geral': margem_geral
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# PWA Routes
@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Sistema Espetinho",
        "short_name": "Espetinho",
        "description": "Sistema de gerenciamento para ponto de espetinho",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#4CAF50",
        "icons": [
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    return send_file('static/sw.js', mimetype='application/javascript')

@app.route('/teste-camera')
def teste_camera():
    return render_template('teste_camera_debug.html')

@app.route('/teste-sessao')
def teste_sessao():
    """Rota para testar se a sessão está funcionando"""
    return jsonify({
        'session_id': session.get('_id', 'Não definido'),
        'user_authenticated': current_user.is_authenticated,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'host': request.host,
        'url': request.url,
        'cookies': dict(request.cookies)
    })

@app.route('/teste-banco')
def teste_banco():
    """Rota para testar o banco de dados"""
    try:
        # Verificar informações do banco
        db_info = {
            'database_uri': app.config['SQLALCHEMY_DATABASE_URI'],
            'database_path': db_path,
            'database_exists': os.path.exists(db_path),
            'database_size': os.path.getsize(db_path) if os.path.exists(db_path) else 0,
            'host': request.host,
            'url': request.url,
            'instance_path': app.instance_path,
            'working_directory': os.getcwd()
        }
        
        # Verificar dados do banco
        with app.app_context():
            produtos_count = Produto.query.count()
            estoque_count = Estoque.query.count()
            vendas_count = Venda.query.count()
            users_count = User.query.count()
            
            # Listar produtos
            produtos = Produto.query.all()
            produtos_list = []
            for p in produtos:
                estoque_items = Estoque.query.filter_by(produto_id=p.id).all()
                estoque_total = sum(e.quantidade for e in estoque_items)
                produtos_list.append({
                    'id': p.id,
                    'nome': p.nome,
                    'ativo': p.ativo,
                    'estoque_total': estoque_total
                })
        
        return jsonify({
            'success': True,
            'db_info': db_info,
            'counts': {
                'produtos': produtos_count,
                'estoque': estoque_count,
                'vendas': vendas_count,
                'users': users_count
            },
            'produtos': produtos_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'db_info': {
                'database_uri': app.config['SQLALCHEMY_DATABASE_URI'],
                'database_path': db_path,
                'host': request.host
            }
                })

@app.route('/sincronizar-banco')
def sincronizar_banco():
    """Rota para forçar sincronização do banco"""
    try:
        # Recriar todas as tabelas
        db.drop_all()
        db.create_all()
        
        # Recriar dados de exemplo
        initialize_app()
        
        return jsonify({
            'success': True,
            'message': 'Banco de dados sincronizado com sucesso!',
            'database_path': db_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/limpar-cache')
def limpar_cache():
    """Rota para forçar limpeza de cache"""
    response = jsonify({
        'success': True,
        'message': 'Cache limpo! Recarregue a página.',
        'timestamp': datetime.now().isoformat()
    })
    
    # Headers anti-cache extremos
    response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
    
    return response

@app.route('/ambiente')
def ambiente():
    """Rota para verificar configuração do ambiente"""
    return jsonify({
        'is_render': is_render,
        'host_url': os.environ.get('HOST_URL', 'Não definido'),
        'flask_env': os.environ.get('FLASK_ENV', 'development'),
        'server_name': app.config.get('SERVER_NAME'),
        'preferred_url_scheme': app.config.get('PREFERRED_URL_SCHEME'),
        'session_cookie_secure': app.config.get('SESSION_COOKIE_SECURE'),
        'request_host': request.host,
        'request_url': request.url,
        'database_path': db_path
    })
 
# Initialize database and create admin user
def initialize_app():
    with app.app_context():
        try:
            print(f"🗄️  Usando banco de dados: {db_path}")
            print(f"📁 Pasta instance: {instance_path}")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create admin user if it doesn't exist
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    nome='Administrador',
                    email='admin@espetinho.com',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuário admin criado!")
            else:
                print("✅ Usuário admin já existe!")
            
            # Criar dados de exemplo se não existirem produtos
            if Produto.query.count() == 0:
                print("📦 Criando produtos de exemplo...")
                
                # Produtos de exemplo
                produtos_exemplo = [
                    {
                        'nome': 'Espetinho de Carne',
                        'tipo': 'espetinho',
                        'preco_padrao': 8.50,
                        'preco_custo': 5.00,
                        'margem_lucro': 30.0,
                        'descricao': 'Espetinho de carne bovina grelhada'
                    },
                    {
                        'nome': 'Espetinho de Frango',
                        'tipo': 'espetinho',
                        'preco_padrao': 7.50,
                        'preco_custo': 4.50,
                        'margem_lucro': 30.0,
                        'descricao': 'Espetinho de frango grelhado'
                    },
                    {
                        'nome': 'Refrigerante Coca-Cola',
                        'tipo': 'bebida',
                        'preco_padrao': 5.00,
                        'preco_custo': 2.50,
                        'margem_lucro': 50.0,
                        'descricao': 'Refrigerante Coca-Cola 350ml'
                    },
                    {
                        'nome': 'Água Mineral',
                        'tipo': 'bebida',
                        'preco_padrao': 3.00,
                        'preco_custo': 1.50,
                        'margem_lucro': 50.0,
                        'descricao': 'Água mineral 500ml'
                    }
                ]
                
                for dados_produto in produtos_exemplo:
                    produto = Produto(**dados_produto)
                    produto.preco_sugerido = produto.calcular_preco_sugerido()
                    db.session.add(produto)
                
                db.session.commit()
                print("✅ Produtos de exemplo criados!")
                
                # Adicionar estoque inicial
                print("📦 Adicionando estoque inicial...")
                produtos = Produto.query.all()
                for produto in produtos:
                    estoque = Estoque(
                        produto_id=produto.id,
                        quantidade=50,
                        custo_unitario=produto.preco_custo
                    )
                    db.session.add(estoque)
                
                db.session.commit()
                print("✅ Estoque inicial adicionado!")
                
                # Criar algumas vendas de exemplo
                print("💰 Criando vendas de exemplo...")
                vendas_exemplo = [
                    {
                        'valor_total': 25.50,
                        'desconto': 0,
                        'forma_pagamento': 'dinheiro',
                        'observacoes': 'Venda de exemplo',
                        'user_id': admin_user.id,
                        'itens': [
                            {'produto_id': 1, 'quantidade': 2, 'preco_unitario': 8.50, 'preco_total': 17.00},
                            {'produto_id': 3, 'quantidade': 1, 'preco_unitario': 5.00, 'preco_total': 5.00},
                            {'produto_id': 4, 'quantidade': 1, 'preco_unitario': 3.00, 'preco_total': 3.00}
                        ]
                    },
                    {
                        'valor_total': 16.00,
                        'desconto': 2.00,
                        'forma_pagamento': 'pix',
                        'observacoes': 'Venda com desconto',
                        'user_id': admin_user.id,
                        'itens': [
                            {'produto_id': 2, 'quantidade': 2, 'preco_unitario': 7.50, 'preco_total': 15.00},
                            {'produto_id': 4, 'quantidade': 1, 'preco_unitario': 3.00, 'preco_total': 3.00}
                        ]
                    }
                ]
                
                for dados_venda in vendas_exemplo:
                    venda = Venda(
                        valor_total=dados_venda['valor_total'],
                        desconto=dados_venda['desconto'],
                        forma_pagamento=dados_venda['forma_pagamento'],
                        observacoes=dados_venda['observacoes'],
                        user_id=dados_venda['user_id']
                    )
                    db.session.add(venda)
                    db.session.flush()  # Para obter o ID da venda
                    
                    # Adicionar itens da venda
                    for item_data in dados_venda['itens']:
                        item = ItemVenda(
                            venda_id=venda.id,
                            produto_id=item_data['produto_id'],
                            quantidade=item_data['quantidade'],
                            preco_unitario=item_data['preco_unitario'],
                            preco_total=item_data['preco_total']
                        )
                        db.session.add(item)
                        
                        # Atualizar estoque
                        estoque_items = Estoque.query.filter_by(produto_id=item_data['produto_id']).all()
                        qtd_restante = item_data['quantidade']
                        
                        for estoque_item in estoque_items:
                            if qtd_restante <= 0:
                                break
                            if estoque_item.quantidade >= qtd_restante:
                                estoque_item.quantidade -= qtd_restante
                                qtd_restante = 0
                            else:
                                qtd_restante -= estoque_item.quantidade
                                estoque_item.quantidade = 0
                
                db.session.commit()
                print("✅ Vendas de exemplo criadas!")
            else:
                print("✅ Produtos já existem no sistema!")
                
        except Exception as e:
            print(f"❌ Error initializing database: {e}")

# Executar inicialização apenas uma vez
initialize_app()

if __name__ == '__main__':
    print("🚀 Sistema Espetinho iniciado!")
    print("👤 Login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000) 