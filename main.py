# main.py
# Streamlit App: Custos de Produção e Lucro Líquido (SQLite local para desenvolvimento)

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# Configuração inicial do Streamlit
st.set_page_config(page_title="Custos & Lucro", layout="wide")

# Título do app
st.title("💰 Calculadora de Custos e Lucro Líquido")

# --- Banco de dados SQLite ---
engine = create_engine('sqlite:///database.db', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

ae = Interpreter()

# Modelos


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


# Cria tabelas se não existirem
Base.metadata.create_all(engine)

# Funções de CRUD e cálculo


def get_variaveis():
    session = Session()
    vars = session.query(Variavel).all()
    session.close()
    return vars


def add_variavel(nome: str, valor: float):
    session = Session()
    var = Variavel(nome=nome, valor=valor)
    session.add(var)
    session.commit()
    session.close()


def get_produtos():
    session = Session()
    prods = session.query(Produto).all()
    session.close()
    return prods


def add_produto(nome: str, formula: str):
    session = Session()
    prod = Produto(nome=nome, formula=formula)
    session.add(prod)
    session.commit()
    session.close()


def evaluate_formula(formula_text: str):
    # Carrega variáveis no ambiente do parser
    session = Session()
    for v in session.query(Variavel).all():
        ae.symtable[v.nome] = v.valor
    session.close()
    try:
        return ae(formula_text)
    except Exception as e:
        return f"Erro na fórmula: {e}"


# --- Interface do App ---
menu = st.sidebar.selectbox(
    'Menu Principal',
    ['Variáveis de Produção', 'Custos de Produção']
)

if menu == 'Variáveis de Produção':
    st.header('📦 Variáveis de Produção')
    # Lista vorhand das variáveis
    variaveis = get_variaveis()
    if variaveis:
        for v in variaveis:
            st.write(f"- **{v.nome}**: {v.valor}")
    else:
        st.write("Nenhuma variável cadastrada.")

    st.subheader('➕ Criar Nova Variável')
    novo_nome = st.text_input('Nome da variável', key='var_nome')
    novo_valor = st.number_input('Valor', format='%.2f', key='var_valor')
    if st.button('Salvar Variável'):
        if novo_nome:
            add_variavel(novo_nome, novo_valor)
            st.success('Variável salva! Atualize a página para ver a lista.')
        else:
            st.error('Informe um nome para a variável.')

elif menu == 'Custos de Produção':
    st.header('🧮 Custos de Produção')
    # Lista produtos e calcula valores
    produtos = get_produtos()
    if produtos:
        for p in produtos:
            resultado = evaluate_formula(p.formula)
            st.write(f"- **{p.nome}**: {resultado}")
    else:
        st.write("Nenhum produto cadastrado.")

    st.subheader('➕ Criar Novo Produto')
    prod_nome = st.text_input('Nome do produto', key='prod_nome')
    prod_formula = st.text_input(
        'Fórmula (ex: Variavel1*(Variavel2+Variavel3))',
        key='prod_formula'
    )
    if st.button('Salvar Produto'):
        if prod_nome and prod_formula:
            add_produto(prod_nome, prod_formula)
            st.success('Produto salvo! Atualize a página para ver a lista.')
        else:
            st.error('Informe nome e fórmula válidos.')
