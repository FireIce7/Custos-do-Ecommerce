import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# --- Configurações de Página e CSS ---
st.set_page_config(page_title="Custos & Lucro", layout="wide")
st.markdown(
    '''<style>
    body { background-color: #0e1117; color: #f0f0f5; }
    .title { text-align: center; margin: 30px 0; font-size: 2.5rem; }
    .center-btn { display: flex; justify-content: center; margin: 20px 0; }
    .stButton>button { padding: 12px 24px; font-size: 1rem; }
    .card { background: #1e1e28; padding: 20px; border-radius: 8px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.5); margin-bottom: 20px; }
    .input-bar > div { background: transparent; margin-bottom: 10px; }
    </style>''',
    unsafe_allow_html=True
)

# --- Banco de Dados SQLite ---
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

# --- Funções CRUD & Cálculo ---


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
        var.nome, var.valor = nome, valor
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
        prod.nome, prod.formula = nome, formula
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


# --- Estado de Navegação e Edição ---
if 'page' not in st.session_state:
    st.session_state.page = 'menu'
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- Função para trocar de página ---


def go(page, edit_id=None):
    st.session_state.page = page
    st.session_state.edit_id = edit_id
    st.experimental_rerun()


# --- MENU INICIAL ---
if st.session_state.page == 'menu':
    st.markdown('<div class="title">📋 Menu Inicial</div>',
                unsafe_allow_html=True)
    # Botão centralizado
    if st.button('💰 Ir para Custos de Produção', key='btn_menu_custos'):
        go('custos')

# --- CUSTOS DE PRODUÇÃO ---
elif st.session_state.page == 'custos':
    st.markdown('<div class="title">🧮 Custos de Produção</div>',
                unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:  # Ações lateral
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if st.button('➕ Novo Produto', key='btn_new_prod'):
            go('produto')
        st.markdown('---')
        if st.button('🔙 Voltar ao Menu', key='btn_back_menu'):
            go('menu')
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:  # Lista de produtos
        st.markdown('<div class="card">', unsafe_allow_html=True)
        prods = get_produtos()
        if prods:
            for p in prods:
                colp = st.columns([4, 1, 1])
                colp[0].write(
                    f"**{p.nome}** → `{p.formula}` = **{evaluate_formula(p.formula)}`")
                if colp[1].button('✏️', key=f'prod_edit_{p.id}'):
                    go('produto', p.id)
                if colp[2].button('🗑️', key=f'prod_del_{p.id}'):
                    delete_produto(p.id)
                    go('custos')
        else:
            st.info('Nenhum produto cadastrado.')
        st.markdown('</div>', unsafe_allow_html=True)

# --- PRODUTO (Adicionar/Editar) ---
elif st.session_state.page == 'produto':
    edit = st.session_state.edit_id
    if edit:
        prod = next((x for x in get_produtos() if x.id == edit), None)
        default_name, default_form = prod.nome, prod.formula
    else:
        default_name, default_form = '', ''
    st.markdown(
        f'<div class="title">{"✏️ Editar Produto" if edit else "➕ Novo Produto"}</div>', unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        name = st.text_input('Nome', value=default_name, key='prod_name')
        form = st.text_input('Fórmula', value=default_form, key='prod_formula')
        if st.button('💾 Salvar', key='btn_save_prod'):
            if name and form:
                if edit:
                    update_produto(edit, name, form)
                else:
                    add_produto(name, form)
                go('custos')
        if st.button('🔙 Cancelar', key='btn_cancel_prod'):
            go('custos')
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="card">Variáveis disponíveis</div>',
                    unsafe_allow_html=True)
        for v in get_variaveis():
            st.write(f"- **{v.nome}** = {v.valor}")

# --- VARIÁVEIS DE PRODUÇÃO ---
elif st.session_state.page == 'variaveis':
    st.markdown('<div class="title">📦 Variáveis de Produção</div>',
                unsafe_allow_html=True)
    cols = st.columns([1, 3])
    edit = st.session_state.edit_id
    if edit:
        var = next((x for x in get_variaveis() if x.id == edit), None)
        dname, dval = var.nome, var.valor
    else:
        dname, dval = '', 0.0
    with cols[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        name = st.text_input('Nome', value=dname, key='var_name')
        val = st.number_input('Valor', value=dval,
                              format='%.2f', key='var_value')
        if st.button('💾 Salvar', key='btn_save_var'):
            if name:
                if edit:
                    update_variavel(edit, name, val)
                else:
                    add_variavel(name, val)
                go('custos')
        if st.button('🔙 Voltar', key='btn_cancel_var'):
            go('custos')
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="card">Lista de Variáveis</div>',
                    unsafe_allow_html=True)
        vars_ = get_variaveis()
        if vars_:
            for v in vars_:
                colv = st.columns([4, 1, 1])
                colv[0].write(f"**{v.nome}** → {v.valor}")
                if colv[1].button('✏️', key=f'var_edit_{v.id}'):
                    go('variaveis', v.id)
                if colv[2].button('🗑️', key=f'var_del_{v.id}'):
                    delete_variavel(v.id)
                    go('variaveis')
        else:
            st.info('Nenhuma variável cadastrada.')
