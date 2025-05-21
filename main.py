from asteval import Interpreter
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float
import streamlit as st
# main.py
# Streamlit App Profissional para Custos & Lucro


# --- Configurações Iniciais ---
st.set_page_config(page_title="Custos & Lucro", layout="wide",
                   initial_sidebar_state="expanded")

# --- CSS Customizado ---
st.markdown(
    '''<style>
    .sidebar .sidebar-content {background-color: #f0f2f6;}
    .stButton>button {width:100%; padding: 10px 0; font-size:16px;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;}
    .title {text-align: center; margin-top: 20px; margin-bottom: 20px;}
    </style>''',
    unsafe_allow_html=True
)

# --- Banco de dados SQLite ---
engine = create_engine('sqlite:///database.db', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

ae = Interpreter()  # Parser de expressões matemáticas

# --- Modelos ORM ---


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

# --- Funções de CRUD / Cálculo ---


def get_variaveis():
    with Session() as session:
        return session.query(Variavel).all()


def add_variavel(nome, valor):
    with Session() as session:
        session.add(Variavel(nome=nome, valor=valor))
        session.commit()


def get_produtos():
    with Session() as session:
        return session.query(Produto).all()


def add_produto(nome, formula):
    with Session() as session:
        session.add(Produto(nome=nome, formula=formula))
        session.commit()


def evaluate_formula(formula_text):
    vars_list = get_variaveis()
    for v in vars_list:
        ae.symtable[v.nome] = v.valor
    try:
        return ae(formula_text)
    except Exception:
        return None


# --- Navegação via Sidebar ---
st.sidebar.title("🔎 Navegação")
page = st.sidebar.radio("Escolha uma página", (
    'Menu Inicial',
    'Custos de Produção',
    'Variáveis de Produção'
))

# --- Menu Inicial ---
if page == 'Menu Inicial':
    st.markdown('<h1 class="title">📋 Menu Inicial</h1>',
                unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button('💰 Abrir Custos de Produção'):
            page = 'Custos de Produção'
    with col2:
        if st.button('📦 Abrir Variáveis de Produção'):
            page = 'Variáveis de Produção'

# Redireciona se botões forem clicados
if page == 'Custos de Produção':
    st.markdown('<h2 class="title">🧮 Custos de Produção</h2>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        st.subheader('Ações')
        if st.button('➕ Novo Produto'):
            nome = st.text_input('Nome do Produto', key='prod_name')
            formula = st.text_input(
                'Fórmula (ex: Variavel1*(Variavel2+Variavel3))', key='prod_formula')
            if st.button('💾 Salvar', key='save_prod') and nome and formula:
                add_produto(nome, formula)
                st.success('Produto salvo com sucesso!')
        if st.button('🔙 Voltar ao Menu'):
            page = 'Menu Inicial'
    with cols[1]:
        st.subheader('Lista de Produtos')
        produtos = get_produtos()
        if produtos:
            for p in produtos:
                valor = evaluate_formula(p.formula)
                st.write(
                    f"**{p.nome}** → Fórmula: `{p.formula}` = **{valor}**")
        else:
            st.info('Nenhum produto cadastrado.')
    st.markdown('</div>', unsafe_allow_html=True)

if page == 'Variáveis de Produção':
    st.markdown('<h2 class="title">📦 Variáveis de Produção</h2>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        st.subheader('Ações')
        nome = st.text_input('Nome da Variável', key='var_name')
        valor = st.number_input('Valor', format='%.2f', key='var_value')
        if st.button('💾 Salvar Variável') and nome:
            add_variavel(nome, valor)
            st.success('Variável salva com sucesso!')
        if st.button('🔙 Voltar ao Menu'):
            page = 'Menu Inicial'
    with cols[1]:
        st.subheader('Lista de Variáveis')
        variaveis = get_variaveis()
        if variaveis:
            for v in variaveis:
                st.write(f"**{v.nome}** → Valor: {v.valor}")
        else:
            st.info('Nenhuma variável cadastrada.')
    st.markdown('</div>', unsafe_allow_html=True)
