# main.py
# Streamlit App: Custos & Lucro com Menu Inicial e Layout Profissional

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter
import os

# --- Configuração do Streamlit ---
st.set_page_config(page_title="Custos & Lucro", layout="wide")

# --- Banco de dados SQLite para desenvolvimento ---
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

# --- Funções de CRUD e Cálculo ---


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
    except Exception as e:
        return f"Erro na fórmula: {e}"


# --- Controle de páginas via Session State ---
if 'page' not in st.session_state:
    st.session_state.page = 'menu'


def go_to(page_name: str):
    st.session_state.page = page_name


# --- UI ---
if st.session_state.page == 'menu':
    st.title('📋 Menu Inicial')
    st.markdown('Selecione uma opção para começar:')
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button('💰 Custos de Produção'):
            go_to('custos')
        st.write('')
        if st.button('📦 Variáveis de Produção'):
            go_to('variaveis')
    with col2:
        st.write('')

# --- Página de Custos de Produção ---
elif st.session_state.page == 'custos':
    st.header('🧮 Custos de Produção')
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button('➕ Criar Novo Produto'):
            go_to('add_produto')
        if st.button('📦 Ir para Variáveis de Produção'):
            go_to('variaveis')
        if st.button('🔙 Voltar ao Menu Inicial'):
            go_to('menu')
    with col2:
        produtos = get_produtos()
        if produtos:
            for p in produtos:
                st.write(f"- **{p.nome}**: {evaluate_formula(p.formula)}")
        else:
            st.info('Nenhum produto cadastrado.')

# --- Tela de Criação de Produto ---
elif st.session_state.page == 'add_produto':
    st.header('➕ Criar Novo Produto')
    col1, col2 = st.columns([1, 2])
    with col1:
        nome = st.text_input('Nome do produto', key='new_prod_nome')
        formula = st.text_input(
            'Fórmula (ex: Variavel1*(Variavel2+Variavel3))', key='new_prod_formula')
        if st.button('Salvar Produto'):
            if nome and formula:
                add_produto(nome, formula)
                st.success('Produto salvo!')
            else:
                st.error('Preencha nome e fórmula.')
        if st.button('🔙 Voltar a Custos'):
            go_to('custos')
    with col2:
        st.write('Use as variáveis pré-cadastradas nas fórmulas:')
        vars = get_variaveis()
        for v in vars:
            st.write(f"- {v.nome} = {v.valor}")

# --- Página de Variáveis de Produção ---
elif st.session_state.page == 'variaveis':
    st.header('📦 Variáveis de Produção')
    col1, col2 = st.columns([1, 2])
    with col1:
        nome = st.text_input('Nome da variável', key='new_var_nome')
        valor = st.number_input('Valor', format='%.2f', key='new_var_valor')
        if st.button('Salvar Variável'):
            if nome:
                add_variavel(nome, valor)
                st.success('Variável salva!')
            else:
                st.error('Informe um nome.')
        if st.button('🔙 Voltar ao Menu Inicial'):
            go_to('menu')
    with col2:
        variaveis = get_variaveis()
        if variaveis:
            for v in variaveis:
                st.write(f"- **{v.nome}**: {v.valor}")
        else:
            st.info('Nenhuma variável cadastrada.')
