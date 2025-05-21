import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# ─── Configuração da página e CSS ─────────────────────────────────────────────
st.set_page_config(page_title="Custos & Lucro", layout="wide")
st.markdown(
    """
    <style>
      /* remove barra branca logo abaixo do header */
      .reportview-container .main .block-container { padding-top: 1rem; }
      /* centraliza títulos */
      .title { text-align: center; margin-bottom: 1rem; }
      /* cards */
      .card { background: #1f1f23; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
      /* botões full-width */
      .stButton>button { width: 100%; padding: 0.75rem; font-size: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Banco de dados SQLite ────────────────────────────────────────────────────
engine = create_engine("sqlite:///database.db", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()
ae = Interpreter()

# ─── Modelos ───────────────────────────────────────────────────────────────────


class Variavel(Base):
    __tablename__ = "variaveis"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    valor = Column(Float, nullable=False)


class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True)
    nome = Column(String, unique=True, nullable=False)
    formula = Column(String, nullable=False)


Base.metadata.create_all(engine)

# ─── CRUD e cálculo ──────────────────────────────────────────────────────────


def get_variaveis():
    with Session() as s:
        return s.query(Variavel).all()


def add_variavel(nome, valor):
    with Session() as s:
        s.add(Variavel(nome=nome, valor=valor))
        s.commit()


def update_variavel(var_id, novo_valor):
    with Session() as s:
        v = s.get(Variavel, var_id)
        v.valor = novo_valor
        s.commit()


def delete_variavel(var_id):
    with Session() as s:
        s.delete(s.get(Variavel, var_id))
        s.commit()


def get_produtos():
    with Session() as s:
        return s.query(Produto).all()


def add_produto(nome, formula):
    with Session() as s:
        s.add(Produto(nome=nome, formula=formula))
        s.commit()


def delete_produto(prod_id):
    with Session() as s:
        s.delete(s.get(Produto, prod_id))
        s.commit()


def evaluate_formula(formula_text):
    for v in get_variaveis():
        ae.symtable[v.nome] = v.valor
    try:
        return ae(formula_text)
    except:
        return None


# ─── Estado da página ─────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "menu"
if "edit_var_id" not in st.session_state:
    st.session_state.edit_var_id = None


def go_to(page_name):
    st.session_state.page = page_name
    st.session_state.edit_var_id = None


# ─── Menu Inicial ─────────────────────────────────────────────────────────────
if st.session_state.page == "menu":
    st.markdown('<h1 class="title">📋 Menu Inicial</h1>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("💰 Custos de Produção"):
            go_to("custos")

# ─── Custos de Produção ───────────────────────────────────────────────────────
elif st.session_state.page == "custos":
    st.markdown('<h1 class="title">🧮 Custos de Produção</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    with left:
        st.subheader("Ações")
        st.text_input("Nome do Produto", key="novo_prod_nome")
        st.text_input("Fórmula (ex: Var1*(Var2+Var3))", key="nova_prod_form")
        if st.button("➕ Novo Produto"):
            nome = st.session_state.novo_prod_nome.strip()
            formula = st.session_state.nova_prod_form.strip()
            if nome and formula:
                add_produto(nome, formula)
                st.success("Produto criado!")
            else:
                st.error("Preencha nome e fórmula.")
        st.button("⬅️ Voltar", on_click=lambda: go_to("menu"))
    with right:
        st.subheader("Lista de Produtos")
        prods = get_produtos()
        if not prods:
            st.info("Nenhum produto cadastrado.")
        for p in prods:
            cols = st.columns([4, 1, 1])
            val = evaluate_formula(p.formula)
            cols[0].write(f"**{p.nome}** → `{p.formula}` = **{val}**")
            if cols[1].button("✏️", key=f"edit_prod_{p.id}"):
                # para simplificar, edição futura
                st.warning("Edição de produto não implementada ainda")
            if cols[2].button("🗑️", key=f"del_prod_{p.id}"):
                delete_produto(p.id)
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─── Variáveis de Produção ────────────────────────────────────────────────────
elif st.session_state.page == "variaveis":
    st.markdown('<h1 class="title">📦 Variáveis de Produção</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    left, right = st.columns([1, 3])
    with left:
        st.subheader("Ações")
        nome = st.text_input("Nome da Variável", key="novo_var_nome")
        valor = st.number_input("Valor", format="%.2f", key="novo_var_val")
        if st.button("➕ Nova Variável"):
            n = st.session_state.novo_var_nome.strip()
            if n:
                add_variavel(n, st.session_state.novo_var_val)
                st.success("Variável criada!")
            else:
                st.error("Insira um nome.")
        # edição inline:
        if st.session_state.edit_var_id:
            v = next(v for v in get_variaveis() if v.id ==
                     st.session_state.edit_var_id)
            novo = st.number_input("Novo valor", value=v.valor, key="edit_val")
            if st.button("💾 Salvar Alteração"):
                update_variavel(v.id, st.session_state.edit_val)
                go_to("variaveis")
    with right:
        st.subheader("Lista de Variáveis")
        vars_ = get_variaveis()
        if not vars_:
            st.info("Nenhuma variável cadastrada.")
        for v in vars_:
            cols = st.columns([4, 1, 1])
            cols[0].write(f"**{v.nome}** → {v.valor}")
            if cols[1].button("✏️", key=f"edit_var_{v.id}"):
                st.session_state.edit_var_id = v.id
                st.experimental_rerun()
            if cols[2].button("🗑️", key=f"del_var_{v.id}"):
                delete_variavel(v.id)
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# habilita a página de variáveis apenas após o usuário criar pelo menos uma variável
if st.session_state.page == "custos":
    # muda o botão de variáveis para aparecer dentro de custos
    if st.sidebar.button("📦 Variáveis de Produção"):
        go_to("variaveis")
