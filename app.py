from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///espetinho.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações para funcionar em todas as interfaces
app.config['SERVER_NAME'] = None  # Permite acesso por qualquer hostname
app.config['PREFERRED_URL_SCHEME'] = 'http'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Middleware para adicionar headers CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
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
            login_user(user)
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

# Rotas para código de barras
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
    print("DEBUG: Acessando página de estoque")
    
    # Mostrar TODOS os produtos (ativos e inativos) para debug
    todos_produtos = Produto.query.all()
    print(f"DEBUG: Total de produtos no banco: {len(todos_produtos)}")
    for p in todos_produtos:
        print(f"DEBUG: Produto '{p.nome}' - Ativo: {p.ativo} - ID: {p.id}")
    
    produtos = Produto.query.filter_by(ativo=True).all()
    estoque_data = []
    
    for produto in produtos:
        # Debug detalhado para cada produto
        print(f"DEBUG: Produto '{produto.nome}' (ID: {produto.id})")
        
        # Buscar estoque diretamente
        estoque_items = Estoque.query.filter_by(produto_id=produto.id).all()
        print(f"DEBUG: - Quantidade de estoque_items encontrados: {len(estoque_items)}")
        
        for item in estoque_items:
            print(f"DEBUG: - Item estoque ID: {item.id}, Qtd: {item.quantidade}, Custo: {item.custo_unitario}")
        
        estoque_atual = sum(e.quantidade for e in estoque_items)
        print(f"DEBUG: - Estoque total calculado: {estoque_atual}")
        
        estoque_data.append({
            'produto': produto,
            'quantidade': estoque_atual
        })
        print(f"DEBUG: {produto.nome} - Estoque final: {estoque_atual}")
        print("---")
    
    print(f"DEBUG: Total de produtos processados: {len(estoque_data)}")
    
    return render_template('estoque.html', estoque_data=estoque_data)

@app.route('/estoque/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_estoque():
    if request.method == 'POST':
        try:
            print(f"DEBUG: Recebendo dados do formulário de estoque: {request.form}")
            
            # Verificar se todos os campos estão presentes
            if 'produto_id' not in request.form or 'quantidade' not in request.form or 'custo_unitario' not in request.form:
                print(f"DEBUG: Campos faltando no formulário: {list(request.form.keys())}")
                flash('Todos os campos são obrigatórios!', 'error')
                return redirect(url_for('adicionar_estoque'))
            
            produto_id = int(request.form['produto_id'])
            quantidade = int(request.form['quantidade'])
            custo_unitario = float(request.form['custo_unitario'])
            
            print(f"DEBUG: Dados processados - Produto ID: {produto_id}, Qtd: {quantidade}, Custo: {custo_unitario}")
            
            # Verificar se o produto existe
            produto = Produto.query.get(produto_id)
            if not produto:
                print(f"DEBUG: Produto não encontrado: {produto_id}")
                flash('Produto não encontrado!', 'error')
                return redirect(url_for('adicionar_estoque'))
            
            estoque = Estoque(
                produto_id=produto_id,
                quantidade=quantidade,
                custo_unitario=custo_unitario
            )
            
            print(f"DEBUG: Criando entrada de estoque para: {produto.nome}")
            
            db.session.add(estoque)
            db.session.commit()
            
            print(f"DEBUG: Estoque adicionado com sucesso! ID: {estoque.id}")
            
            # Verificar se o estoque foi realmente salvo
            estoque_salvo = Estoque.query.get(estoque.id)
            if estoque_salvo:
                print(f"DEBUG: Estoque confirmado no banco - ID: {estoque_salvo.id}, Qtd: {estoque_salvo.quantidade}")
            else:
                print("DEBUG: ERRO - Estoque não encontrado no banco após salvar!")
            
            flash('Estoque adicionado com sucesso!', 'success')
            print(f"DEBUG: Redirecionando para: {url_for('estoque')}")
            # Garantir que o redirecionamento seja feito corretamente
            return redirect(url_for('estoque'), code=302)
            
        except Exception as e:
            print(f"DEBUG: Erro ao adicionar estoque: {str(e)}")
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
        return jsonify({'success': True, 'venda_id': venda.id})
    
    produtos = Produto.query.filter_by(ativo=True).all()
    # Converter produtos para dicionários serializáveis
    produtos_data = []
    for produto in produtos:
        estoque_atual = sum(e.quantidade for e in produto.estoque_items)
        produtos_data.append({
            'id': produto.id,
            'nome': produto.nome,
            'tipo': produto.tipo,
            'preco_padrao': produto.preco_padrao,
            'descricao': produto.descricao,
            'estoque': estoque_atual
        })
    
    return render_template('nova_venda.html', produtos=produtos_data)

@app.route('/api/produtos')
@login_required
def api_produtos():
    produtos = Produto.query.filter_by(ativo=True).all()
    return jsonify([{
        'id': p.id,
        'nome': p.nome,
        'tipo': p.tipo,
        'preco_padrao': p.preco_padrao,
        'estoque': sum(e.quantidade for e in p.estoque_items)
    } for p in produtos])

@app.route('/api/produto/<int:id>')
@login_required
def api_produto(id):
    produto = Produto.query.get_or_404(id)
    return jsonify({
        'success': True,
        'produto': {
            'id': produto.id,
            'nome': produto.nome,
            'tipo': produto.tipo,
            'preco_padrao': produto.preco_padrao,
            'preco_custo': produto.preco_custo,
            'margem_lucro': produto.margem_lucro,
            'estoque': sum(e.quantidade for e in produto.estoque_items)
        }
    })

# Rotas de relatórios
@app.route('/relatorios')
@gerente_required
def relatorios():
    return render_template('relatorios.html')

@app.route('/api/relatorio/vendas')
@gerente_required
def api_relatorio_vendas():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Venda.query
    
    if data_inicio:
        query = query.filter(Venda.data_venda >= datetime.strptime(data_inicio, '%Y-%m-%d'))
    if data_fim:
        # Adicionar 23:59:59 para incluir o dia inteiro
        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
        query = query.filter(Venda.data_venda <= data_fim_dt)
    
    vendas = query.all()
    
    total_vendas = sum(v.valor_total for v in vendas)
    total_descontos = sum(v.desconto for v in vendas)
    qtd_vendas = len(vendas)
    
    # Calcular vendas por forma de pagamento
    vendas_por_pagamento = {}
    for venda in vendas:
        forma = venda.forma_pagamento
        if forma not in vendas_por_pagamento:
            vendas_por_pagamento[forma] = {'total': 0, 'quantidade': 0}
        vendas_por_pagamento[forma]['total'] += venda.valor_total
        vendas_por_pagamento[forma]['quantidade'] += 1
    
    # Se não há vendas, criar dados vazios para os gráficos
    if not vendas_por_pagamento:
        vendas_por_pagamento = {
            'dinheiro': {'total': 0, 'quantidade': 0},
            'pix': {'total': 0, 'quantidade': 0},
            'cartão': {'total': 0, 'quantidade': 0}
        }
    
    # Calcular vendas por dia (para gráfico)
    vendas_por_dia = {}
    for venda in vendas:
        data = venda.data_venda.strftime('%Y-%m-%d')
        if data not in vendas_por_dia:
            vendas_por_dia[data] = {'total': 0, 'quantidade': 0}
        vendas_por_dia[data]['total'] += venda.valor_total
        vendas_por_dia[data]['quantidade'] += 1
    
    # Se não há vendas por dia, criar dados vazios
    if not vendas_por_dia:
        # Criar dados para os últimos 7 dias
        from datetime import datetime, timedelta
        hoje = datetime.now()
        for i in range(7):
            data = (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
            vendas_por_dia[data] = {'total': 0, 'quantidade': 0}
    
    # Calcular produtos mais vendidos
    produtos_vendidos = {}
    for venda in vendas:
        for item in venda.itens:
            produto_nome = item.produto.nome
            if produto_nome not in produtos_vendidos:
                produtos_vendidos[produto_nome] = {'quantidade': 0, 'total': 0}
            produtos_vendidos[produto_nome]['quantidade'] += item.quantidade
            produtos_vendidos[produto_nome]['total'] += item.preco_total
    
    # Top 5 produtos mais vendidos
    top_produtos = sorted(produtos_vendidos.items(), key=lambda x: x[1]['quantidade'], reverse=True)[:5]
    
    return jsonify({
        'total_vendas': total_vendas,
        'total_descontos': total_descontos,
        'qtd_vendas': qtd_vendas,
        'lucro_estimado': total_vendas * 0.6,  # Estimativa de 60% de lucro
        'ticket_medio': total_vendas / qtd_vendas if qtd_vendas > 0 else 0,
        'vendas_por_pagamento': vendas_por_pagamento,
        'vendas_por_dia': vendas_por_dia,
        'top_produtos': top_produtos
    })

@app.route('/debug/estoque')
@login_required
def debug_estoque():
    """Rota de debug para verificar o estado do estoque"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Verificar produtos
    produtos = Produto.query.all()
    produtos_data = []
    for produto in produtos:
        estoque_items = Estoque.query.filter_by(produto_id=produto.id).all()
        estoque_total = sum(e.quantidade for e in estoque_items)
        produtos_data.append({
            'id': produto.id,
            'nome': produto.nome,
            'tipo': produto.tipo,
            'ativo': produto.ativo,
            'estoque_total': estoque_total,
            'estoque_items': [{'id': e.id, 'quantidade': e.quantidade, 'custo': e.custo_unitario} for e in estoque_items]
        })
    
    # Verificar todas as entradas de estoque
    estoque_todos = Estoque.query.all()
    estoque_data = [{'id': e.id, 'produto_id': e.produto_id, 'quantidade': e.quantidade, 'custo': e.custo_unitario} for e in estoque_todos]
    
    return jsonify({
        'produtos': produtos_data,
        'estoque_entries': estoque_data,
        'total_produtos': len(produtos),
        'total_estoque_entries': len(estoque_todos)
    })

@app.route('/api/relatorio/lucratividade')
@gerente_required
def api_relatorio_lucratividade():
    """Relatório de lucratividade dos produtos"""
    produtos = Produto.query.filter_by(ativo=True).all()
    
    # Calcular estatísticas de lucratividade
    produtos_com_custo = []
    total_custo = 0
    total_receita_potencial = 0
    total_lucro_potencial = 0
    
    for produto in produtos:
        if produto.preco_custo > 0:
            lucro_unitario = produto.calcular_lucro_atual()
            margem = produto.calcular_margem_atual()
            estoque_atual = sum(e.quantidade for e in produto.estoque_items)
            
            produtos_com_custo.append({
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'preco_custo': produto.preco_custo,
                'preco_venda': produto.preco_padrao,
                'lucro_unitario': lucro_unitario,
                'margem': margem,
                'estoque': estoque_atual,
                'lucro_total_estoque': lucro_unitario * estoque_atual
            })
            
            total_custo += produto.preco_custo * estoque_atual
            total_receita_potencial += produto.preco_padrao * estoque_atual
            total_lucro_potencial += lucro_unitario * estoque_atual
    
    # Ordenar por margem de lucro
    produtos_com_custo.sort(key=lambda x: x['margem'], reverse=True)
    
    # Calcular médias
    margem_media = sum(p['margem'] for p in produtos_com_custo) / len(produtos_com_custo) if produtos_com_custo else 0
    
    return jsonify({
        'resumo': {
            'total_produtos': len(produtos),
            'produtos_com_custo': len(produtos_com_custo),
            'margem_media': round(margem_media, 1),
            'total_custo_estoque': round(total_custo, 2),
            'total_receita_potencial': round(total_receita_potencial, 2),
            'total_lucro_potencial': round(total_lucro_potencial, 2)
        },
        'produtos': produtos_com_custo
    })

# Rota para PWA
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
    return app.send_static_file('sw.js')

@app.route('/teste-camera')
def teste_camera():
    return app.send_static_file('teste_camera_debug.html')

@app.route('/teste-conexao')
def teste_conexao():
    """Rota para testar se a conexão está funcionando"""
    return jsonify({
        'status': 'success',
        'message': 'Conexão funcionando!',
        'timestamp': datetime.now().isoformat(),
        'host': request.host,
        'url': request.url,
        'method': request.method
    })

if __name__ == '__main__':
    # Verificar se existem certificados SSL
    cert_path = 'certs/cert.pem'
    key_path = 'certs/key.pem'
    use_https = os.path.exists(cert_path) and os.path.exists(key_path)
    
    if use_https:
        print("🔐 HTTPS detectado! Sistema será iniciado com SSL")
        print("🚀 Sistema iniciado! Acesse: https://localhost:5000")
        print("🌐 Para acesso externo: https://10.0.0.105:5000")
        print("👤 Login: admin / admin123")
        print("⚠️  Aceite o aviso de certificado não confiável no navegador")
        
        app.run(debug=True, host='0.0.0.0', port=5000, 
               ssl_context=(cert_path, key_path))
    else:
        print("🔓 HTTP detectado! Sistema será iniciado sem SSL")
        print("🚀 Sistema iniciado! Acesse: http://localhost:5000")
        print("🌐 Para acesso externo: http://10.0.0.105:5000")
        print("👤 Login: admin / admin123")
        print("💡 Para câmera em todos os navegadores, execute: python gerar_certificados.py")
        
        # Configurar para funcionar em todas as interfaces
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

# Initialize database and create admin user (after all models are defined)
def initialize_app():
    with app.app_context():
        try:
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