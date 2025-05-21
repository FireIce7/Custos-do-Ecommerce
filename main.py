import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# --- Configuração de página e CSS ---
st.set_page_config(page_title="Custos & Lucro", layout="wide")
st.markdown(
    '''<style>
    body { background-color: #0e1117; color: #e1e1e1; }
    .card { background: #1e1e24; padding: 20px; border-radius: 8px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.5); margin-bottom: 20px; }
    .title { text-align: center; margin: 30px 0; font-size: 2.5rem; }
    .btn { width: 100%; padding: 14px 0; font-size: 1.1rem; margin-bottom: 10px; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input { background: #2e2e36; color: #fff; }
    </style>''',
    unsafe_allow_html=True
)

# --- Banco de dados SQLite (desenvolvimento) ---
engine = create_engine('sqlite:///database.db', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()
ae = Interpreter()

# --- Modelos ---


class Variavel(Base):
    __tablename__ = 'variaveis'
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    valor = Column(Float, nullable=False)


class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    formula = Column(String, nullable=False)


Base.metadata.create_all(engine)

# --- Funções CRUD e cálculo ---


def get_variaveis():
    with Session() as s:
        return s.query(Variavel).all()


def add_variavel(nome, valor):
    with Session() as s:
        s.add(Variavel(nome=nome, valor=valor))
        s.commit()


def update_variavel(var_id, nome, valor):
    with Session() as s:
        var = s.get(Variavel, var_id)
        var.nome = nome
        var.valor = valor
        s.commit()


def delete_variavel(var_id):
    with Session() as s:
        var = s.get(Variavel, var_id)
        if var:
            s.delete(var)
            s.commit()


def get_produtos():
    with Session() as s:
        return s.query(Produto).all()


def add_produto(nome, formula):
    with Session() as s:
        s.add(Produto(nome=nome, formula=formula))
        s.commit()


def update_produto(prod_id, nome, formula):
    with Session() as s:
        prod = s.get(Produto, prod_id)
        prod.nome = nome
        prod.formula = formula
        s.commit()


def delete_produto(prod_id):
    with Session() as s:
        prod = s.get(Produto, prod_id)
        if prod:
            s.delete(prod)
            s.commit()


def evaluate_formula(formula):
    for v in get_variaveis():
        ae.symtable[v.nome] = v.valor
    try:
        return ae(formula)
    except:
        return None


# --- Estado de navegação e edição ---
if 'page' not in st.session_state:
    st.session_state.page = 'menu'
if 'edit_var' not in st.session_state:
    st.session_state.edit_var = None
if 'edit_prod' not in st.session_state:
    st.session_state.edit_prod = None

# --- Função para trocar de página ---


def go(page_name):
    st.session_state.page = page_name
    st.session_state.edit_var = None
    st.session_state.edit_prod = None


# --- Menu Inicial ---
if st.session_state.page == 'menu':
    st.markdown('<div class="title">📋 Menu Inicial</div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button('💰 Ir para Custos de Produção', key='menu_custos', help='Clique para ver custos'):
            go('custos')

# --- Custos de Produção ---
elif st.session_state.page == 'custos':
    st.markdown('<div class="title">🧮 Custos de Produção</div>',
                unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if st.button('➕ Novo Produto', key='btn_new_prod', help='Criar novo produto'):
            go('add_produto')
        st.markdown('---')
        if st.button('🔙 Voltar ao Menu', key='btn_back_menu'):
            go('menu')
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        prods = get_produtos()
        if prods:
            for p in prods:
                cols = st.columns([4, 1, 1])
                with cols[0]:
                    val = evaluate_formula(p.formula)
                    st.write(f"**{p.nome}** → `{p.formula}` = **{val}**")
                with cols[1]:
                    if st.button('✏️', key=f'edit_prod_{p.id}'):
                        st.session_state.edit_prod = p.id
                        go('add_produto')
                with cols[2]:
                    if st.button('🗑️', key=f'del_prod_{p.id}'):
                        delete_produto(p.id)
                        st.experimental_rerun()
        else:
            st.info('Nenhum produto cadastrado.')
        st.markdown('</div>', unsafe_allow_html=True)

# --- Adicionar / Editar Produto ---
elif st.session_state.page == 'add_produto':
    st.markdown('<div class="title">➕ Novo Produto</div>',
                unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    # Preencher campos se editando
    if st.session_state.edit_prod:
        prod = next((x for x in get_produtos() if x.id ==
                    st.session_state.edit_prod), None)
        default_name = prod.nome
        default_formula = prod.formula
    else:
        default_name = ''
        default_formula = ''
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        name = st.text_input(
            'Nome do Produto', value=default_name, key='prod_name')
        formula = st.text_input(
            'Fórmula (Var1*(Var2+Var3))', value=default_formula, key='prod_formula')
        if st.button('💾 Salvar Produto', key='save_prod'):
            if name and formula:
                if st.session_state.edit_prod:
                    update_produto(st.session_state.edit_prod, name, formula)
                else:
                    add_produto(name, formula)
                go('custos')
                st.experimental_rerun()
            else:
                st.error('Preencha nome e fórmula.')
        if st.button('🔙 Cancelar', key='cancel_prod'):
            go('custos')
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader('Variáveis Disponíveis')
        for v in get_variaveis():
            st.write(f"- **{v.nome}** = {v.valor}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Variáveis de Produção ---
elif st.session_state.page == 'variaveis':
    st.markdown('<div class="title">📦 Variáveis de Produção</div>',
                unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    # Preencher campos se editando
    if st.session_state.edit_var:
        var = next((x for x in get_variaveis() if x.id ==
                   st.session_state.edit_var), None)
        default_name = var.nome
        default_val = var.valor
    else:
        default_name = ''
        default_val = 0.0
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        name = st.text_input('Nome da Variável',
                             value=default_name, key='var_name')
        val = st.number_input('Valor', value=default_val,
                              format='%.2f', key='var_value')
        if st.button('💾 Salvar Variável', key='save_var'):
            if name:
                if st.session_state.edit_var:
                    update_variavel(st.session_state.edit_var, name, val)
                else:
                    add_variavel(name, val)
                go('custos')
                st.experimental_rerun()
            else:
                st.error('Informe um nome.')
        if st.button('🔙 Cancelar', key='cancel_var'):
            go('custos')
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        vars_ = get_variaveis()
        if vars_:
            for v in vars_:
                cols = st.columns([4, 1, 1])
                with cols[0]:
                    st.write(f"**{v.nome}** → {v.valor}")
                with cols[1]:
                    if st.button('✏️', key=f'edit_var_{v.id}'):
                        st.session_state.edit_var = v.id
                        go('variaveis')
                with cols[2]:
                    if st.button('🗑️', key=f'del_var_{v.id}'):
                        delete_variavel(v.id)
                        st.experimental_rerun()
        else:
            st.info('Nenhuma variável cadastrada.')
        st.markdown('</div>', unsafe_allow_html=True)
