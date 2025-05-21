# main.py
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# --- Configuração de página e CSS ---
st.set_page_config(page_title="Custos & Lucro", layout="wide")
st.markdown("""
<style>
    .sidebar .sidebar-content {background-color: #f0f2f6;}
    .stButton>button {width:100%; padding:12px 0; font-size:16px; margin-bottom:8px;}
    .card {background:#fff; padding:20px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); margin-bottom:20px;}
    .title {text-align:center; margin:20px 0;}
</style>
""", unsafe_allow_html=True)

# --- Banco de dados SQLite ---
engine = create_engine('sqlite:///database.db', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()
ae = Interpreter()

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

# --- Funções CRUD e cálculo ---


def get_variaveis():
    with Session() as s:
        return s.query(Variavel).all()


def add_variavel(nome, valor):
    with Session() as s:
        s.add(Variavel(nome=nome, valor=valor))
        s.commit()


def get_produtos():
    with Session() as s:
        return s.query(Produto).all()


def add_produto(nome, formula):
    with Session() as s:
        s.add(Produto(nome=nome, formula=formula))
        s.commit()


def evaluate_formula(formula_text):
    for v in get_variaveis():
        ae.symtable[v.nome] = v.valor
    try:
        return ae(formula_text)
    except:
        return None


# --- Navegação via sidebar ---
page = st.sidebar.radio(
    "🔎 Menu",
    ["Menu Inicial", "Custos de Produção", "Variáveis de Produção"]
)

# --- Menu Inicial ---
if page == "Menu Inicial":
    st.markdown('<h1 class="title">📋 Menu Inicial</h1>',
                unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💰 Custos de Produção"):
            page = "Custos de Produção"
    with col2:
        if st.button("📦 Variáveis de Produção"):
            page = "Variáveis de Produção"

# --- Custos de Produção ---
if page == "Custos de Produção":
    st.markdown('<h2 class="title">🧮 Custos de Produção</h2>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    with left:
        st.subheader("Ações")
        st.markdown("---")
        nome = st.text_input("🔹 Nome do Produto", key="p_name")
        formula = st.text_input(
            "🔹 Fórmula (Ex: Var1*(Var2+Var3))", key="p_formula")
        if st.button("💾 Salvar Produto"):
            if nome and formula:
                add_produto(nome, formula)
                st.success("Produto salvo!")
            else:
                st.error("Preencha nome e fórmula.")
    with right:
        st.subheader("Lista de Produtos")
        prods = get_produtos()
        if prods:
            for p in prods:
                val = evaluate_formula(p.formula)
                st.write(f"**{p.nome}** → `{p.formula}` = **{val}**")
        else:
            st.info("Nenhum produto cadastrado.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Variáveis de Produção ---
if page == "Variáveis de Produção":
    st.markdown('<h2 class="title">📦 Variáveis de Produção</h2>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    with left:
        st.subheader("Ações")
        st.markdown("---")
        nome = st.text_input("🔹 Nome da Variável", key="v_name")
        valor = st.number_input("🔹 Valor", format="%.2f", key="v_value")
        if st.button("💾 Salvar Variável"):
            if nome:
                add_variavel(nome, valor)
                st.success("Variável salva!")
            else:
                st.error("Preencha o nome.")
    with right:
        st.subheader("Lista de Variáveis")
        vars_ = get_variaveis()
        if vars_:
            for v in vars_:
                st.write(f"**{v.nome}** → {v.valor}")
        else:
            st.info("Nenhuma variável cadastrada.")
    st.markdown('</div>', unsafe_allow_html=True)
