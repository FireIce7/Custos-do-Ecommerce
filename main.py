import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# --- Configurações iniciais ---
st.set_page_config(page_title="Custos & Lucro", layout="wide")
st.markdown(
    '''<style>
    /* Sidebar styling */
    .sidebar .sidebar-content { background-color: #f0f2f6; }
    /* Card styling */
    .card { background: #fff; padding: 20px; border-radius: 8px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
    /* Button styling */
    .btn-full { width: 100%; padding: 12px 0; font-size: 16px; margin-bottom: 10px; }
    /* Title styling */
    .title { text-align: center; margin: 25px 0; }
    </style>''',
    unsafe_allow_html=True
)

# --- Banco de dados SQLite (dev) ---
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

# --- CRUD & cálculo ---


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


def evaluate_formula(formula):
    for v in get_variaveis():
        ae.symtable[v.nome] = v.valor
    try:
        return ae(formula)
    except:
        return None


# --- Inicializa página ---
if 'page' not in st.session_state:
    st.session_state.page = 'menu'

# --- Menu Inicial ---
if st.session_state.page == 'menu':
    st.markdown('<h1 class="title">📋 Menu Inicial</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button('💰 Ir para Custos de Produção', key='menu_custos', args=None):
        st.session_state.page = 'custos'
    st.markdown('</div>', unsafe_allow_html=True)

# --- Página: Custos de Produção ---
elif st.session_state.page == 'custos':
    st.markdown('<h2 class="title">🧮 Custos de Produção</h2>',
                unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:  # Navegação lateral
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.button('➕ Criar Novo Produto', key='goto_add_prod',
                  on_click=lambda: st.session_state.update(page='add_produto'), args=None)
        st.button('📦 Ver Variáveis de Produção', key='goto_vars',
                  on_click=lambda: st.session_state.update(page='variaveis'), args=None)
        st.button('🔙 Voltar ao Menu', key='back_menu',
                  on_click=lambda: st.session_state.update(page='menu'), args=None)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:  # Conteúdo principal
        st.markdown('<div class="card">', unsafe_allow_html=True)
        produtos = get_produtos()
        if produtos:
            for p in produtos:
                val = evaluate_formula(p.formula)
                st.write(f"**{p.nome}** → `{p.formula}` = **{val}**")
        else:
            st.info("Nenhum produto cadastrado.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Página: Adicionar Produto ---
elif st.session_state.page == 'add_produto':
    st.markdown('<h2 class="title">➕ Novo Produto</h2>',
                unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        nome = st.text_input('Nome do Produto', key='new_prod_name')
        formula = st.text_input(
            'Fórmula (Var1*(Var2+Var3))', key='new_prod_formula')
        if st.button('💾 Salvar Produto', key='save_prod'):
            if nome and formula:
                add_produto(nome, formula)
                st.success('Produto salvo com sucesso!')
                st.session_state.page = 'custos'
            else:
                st.error('Preencha nome e fórmula.')
        st.button('🔙 Voltar a Custos', key='back_to_custos',
                  on_click=lambda: st.session_state.update(page='custos'), args=None)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader('Variáveis Disponíveis')
        for v in get_variaveis():
            st.write(f"- **{v.nome}** = {v.valor}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Página: Variáveis de Produção ---
elif st.session_state.page == 'variaveis':
    st.markdown('<h2 class="title">📦 Variáveis de Produção</h2>',
                unsafe_allow_html=True)
    cols = st.columns([1, 3])
    with cols[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        nome = st.text_input('Nome da Variável', key='new_var_name')
        valor = st.number_input('Valor', format='%.2f', key='new_var_value')
        if st.button('💾 Salvar Variável', key='save_var'):
            if nome:
                add_variavel(nome, valor)
                st.success('Variável salva com sucesso!')
                st.session_state.page = 'custos'
            else:
                st.error('Informe um nome.')
        st.button('🔙 Voltar a Custos', key='back_to_custos2',
                  on_click=lambda: st.session_state.update(page='custos'), args=None)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader('Lista de Variáveis')
        vars_list = get_variaveis()
        if vars_list:
            for v in vars_list:
                st.write(f"**{v.nome}** → {v.valor}")
        else:
            st.info('Nenhuma variável cadastrada.')
        st.markdown('</div>', unsafe_allow_html=True)
