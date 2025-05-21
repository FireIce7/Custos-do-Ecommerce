# main.py
# Streamlit App: Custos & Lucro com Layout Profissional e Interativo

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter
import os

# --- Configurações Iniciais ---
st.set_page_config(page_title="Custos & Lucro", layout="wide")

# --- CSS Customizado para Estilização ---
st.markdown(
    """
    <style>
    .big-button div.row-widget.stButton > button {
        width: 100%;
        height: 60px;
        font-size: 18px;
        margin-bottom: 10px;
    }
    .center-title {
        text-align: center;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .section {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Banco de Dados SQLite (Desenvolvimento) ---
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

# --- Funções de CRUD e Avaliação de Fórmulas ---


def get_variaveis():
    session = Session()
    items = session.query(Variavel).all()
    session.close()
    return items


def add_variavel(nome: str, valor: float):
    session = Session()
    session.add(Variavel(nome=nome, valor=valor))
    session.commit()
    session.close()


def get_produtos():
    session = Session()
    items = session.query(Produto).all()
    session.close()
    return items


def add_produto(nome: str, formula: str):
    session = Session()
    session.add(Produto(nome=nome, formula=formula))
    session.commit()
    session.close()


def evaluate_formula(formula_text: str):
    session = Session()
    for v in session.query(Variavel).all():
        ae.symtable[v.nome] = v.valor
    session.close()
    try:
        return ae(formula_text)
    except:
        return "Erro na fórmula"


# --- Gerenciamento de Páginas (Session State) ---
if 'page' not in st.session_state:
    st.session_state.page = 'menu'


def go_to(page_name: str):
    st.session_state.page = page_name
    st.experimental_rerun()


# --- Menu Inicial ---
if st.session_state.page == 'menu':
    st.markdown("<h1 class='center-title'>📋 Menu Inicial</h1>",
                unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button('💰 Custos de Produção', key='m_custos'):
            go_to('custos')
    with col2:
        if st.button('📦 Variáveis de Produção', key='m_variaveis'):
            go_to('variaveis')
    with col3:
        st.write("")

# --- Página de Custos de Produção ---
elif st.session_state.page == 'custos':
    st.markdown("<h2 class='center-title'>🧮 Custos de Produção</h2>",
                unsafe_allow_html=True)
    container = st.container()
    cols = container.columns([1, 3])
    with cols[0]:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        if st.button('➕ Novo Produto', key='p_add'):
            go_to('add_produto')
        if st.button('📦 Variáveis', key='p_vars'):
            go_to('variaveis')
        if st.button('🔙 Voltar', key='p_back'):
            go_to('menu')
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        produtos = get_produtos()
        if produtos:
            for p in produtos:
                valor = evaluate_formula(p.formula)
                st.markdown(f"**{p.nome}**: `{p.formula}` = **{valor}**")
        else:
            st.info('Nenhum produto cadastrado.')

# --- Tela de Adição de Produto ---
elif st.session_state.page == 'add_produto':
    st.markdown("<h2 class='center-title'>➕ Criar Produto</h2>",
                unsafe_allow_html=True)
    container = st.container()
    cols = container.columns([1, 3])
    with cols[0]:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        nome = st.text_input('Nome do Produto', key='new_p_name')
        formula = st.text_input(
            'Fórmula (ex: Variavel1*(Variavel2+Variavel3))', key='new_p_formula')
        if st.button('💾 Salvar', key='save_p'):
            if nome and formula:
                add_produto(nome, formula)
                st.success('Produto salvo com sucesso!')
            else:
                st.error('Preencha todos os campos.')
        if st.button('🔙 Voltar', key='back_from_add'):
            go_to('custos')
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.write('### Variáveis Disponíveis')
        for v in get_variaveis():
            st.write(f"- **{v.nome}** = {v.valor}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Página de Variáveis de Produção ---
elif st.session_state.page == 'variaveis':
    st.markdown("<h2 class='center-title'>📦 Variáveis de Produção</h2>",
                unsafe_allow_html=True)
    container = st.container()
    cols = container.columns([1, 3])
    with cols[0]:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        nome = st.text_input('Nome da Variável', key='new_v_name')
        valor = st.number_input('Valor', format='%.2f', key='new_v_value')
        if st.button('💾 Salvar', key='save_v'):
            if nome:
                add_variavel(nome, valor)
                st.success('Variável salva com sucesso!')
            else:
                st.error('Informe um nome válido.')
        if st.button('🔙 Voltar', key='v_back'):
            go_to('menu')
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.write('### Variáveis Cadastradas')
        for v in get_variaveis():
            st.write(f"- **{v.nome}**: {v.valor}")
        st.markdown('</div>', unsafe_allow_html=True)
