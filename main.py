import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from asteval import Interpreter

# ─── Configurações iniciais ────────────────────────────────────────────────────
st.set_page_config(page_title="Custos & Lucro", layout="wide")
st.markdown("""
<style>
  /* Remove gap abaixo do header */
  .reportview-container .main .block-container {padding-top: 1rem;}
  /* Centraliza títulos e botões */
  .title {text-align: center; margin-bottom: 2rem;}
  .center {display: flex; justify-content: center; align-items: center;}
  .big-button > button {padding: 1rem 2rem; font-size: 1.25rem;}
  /* Card para seções */
  .card {background: #1f1f23; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;}
  /* Botões pequenos */
  .small-btn > button {padding: 0.5rem 1rem; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

# ─── Banco de dados SQLite ────────────────────────────────────────────────────
engine = create_engine("sqlite:///database.db", echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()
ae = Interpreter()

# ─── Modelos ORM ───────────────────────────────────────────────────────────────


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

# ─── Funções CRUD & Cálculo ───────────────────────────────────────────────────


def get_variaveis():
    with Session() as s:
        return s.query(Variavel).all()


def add_variavel(nome, valor):
    with Session() as s:
        s.add(Variavel(nome=nome, valor=valor))
        s.commit()


def update_variavel(var_id, novo_val):
    with Session() as s:
        v = s.get(Variavel, var_id)
        v.valor = novo_val
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
    # popula o ambiente com as variáveis
    for v in get_variaveis():
        ae.symtable[v.nome] = v.valor
    try:
        return ae(formula_text)
    except:
        return None


# ─── Controle de páginas ──────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "menu"
if "edit_var_id" not in st.session_state:
    st.session_state.edit_var_id = None


def go(page_name):
    st.session_state.page = page_name
    st.session_state.edit_var_id = None


# ─── PÁGINA: Menu Inicial ─────────────────────────────────────────────────────
if st.session_state.page == "menu":
    st.markdown('<h1 class="title">📋 Menu Inicial</h1>',
                unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="center big-button">', unsafe_allow_html=True)
        if st.button("💰 Ir para Custos de Produção"):
            go("custos")
        st.markdown('</div>', unsafe_allow_html=True)

# ─── PÁGINA: Custos de Produção ────────────────────────────────────────────────
elif st.session_state.page == "custos":
    st.markdown('<h1 class="title">🧮 Custos de Produção</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_acoes, col_lista = st.columns([1, 3], gap="large")

    # ── Coluna de Ações ───────────────────────────────────────────
    with col_acoes:
        st.subheader("Ações")
        st.markdown("---")
        if st.button("⬅️ Voltar ao Menu", **{"class": "small-btn"}):
            go("menu")
        if st.button("📦 Ir para Variáveis", **{"class": "small-btn"}):
            go("variaveis")
        st.markdown("---")
        st.text_input("🔹 Nome do Produto", key="novo_prod_nome")
        st.text_input("🔹 Fórmula (ex: Var1*(Var2+Var3))", key="nova_prod_form")
        if st.button("➕ Novo Produto", **{"class": "small-btn"}):
            nome = st.session_state.novo_prod_nome.strip()
            form = st.session_state.nova_prod_form.strip()
            if nome and form:
                add_produto(nome, form)
                st.success("Produto criado!")
            else:
                st.error("Preencha nome e fórmula.")

    # ── Coluna de Lista de Produtos ──────────────────────────────
    with col_lista:
        st.subheader("Produtos Cadastrados")
        prods = get_produtos()
        if not prods:
            st.info("Nenhum produto cadastrado.")
        for p in prods:
            cols = st.columns([4, 1], gap="small")
            val = evaluate_formula(p.formula)
            cols[0].write(f"**{p.nome}** → `{p.formula}` = **{val}**")
            if cols[1].button("🗑️", key=f"delp_{p.id}", **{"class": "small-btn"}):
                delete_produto(p.id)
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─── PÁGINA: Variáveis de Produção ─────────────────────────────────────────────
elif st.session_state.page == "variaveis":
    st.markdown('<h1 class="title">📦 Variáveis de Produção</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_acoes, col_lista = st.columns([1, 3], gap="large")

    # ── Coluna de Ações ───────────────────────────────────────────
    with col_acoes:
        st.subheader("Ações")
        st.markdown("---")
        if st.button("⬅️ Voltar aos Custos", **{"class": "small-btn"}):
            go("custos")
        st.text_input("🔹 Nome da Variável", key="novo_var_nome")
        st.number_input("🔹 Valor", key="novo_var_val", format="%.2f")
        if st.button("➕ Nova Variável", **{"class": "small-btn"}):
            n = st.session_state.novo_var_nome.strip()
            v = st.session_state.novo_var_val
            if n:
                add_variavel(n, v)
                st.success("Variável criada!")
            else:
                st.error("Insira um nome.")

        # edição inline (se selecionado)
        if st.session_state.edit_var_id:
            vobj = next(x for x in get_variaveis() if x.id ==
                        st.session_state.edit_var_id)
            novo = st.number_input(
                "✏️ Novo valor", value=vobj.valor, key="edit_val")
            if st.button("💾 Salvar Alteração", **{"class": "small-btn"}):
                update_variavel(vobj.id, novo)
                st.success("Variável atualizada!")
                go("variaveis")

    # ── Coluna de Lista de Variáveis ─────────────────────────────
    with col_lista:
        st.subheader("Variáveis Cadastradas")
        vars_ = get_variaveis()
        if not vars_:
            st.info("Nenhuma variável cadastrada.")
        for v in vars_:
            cols = st.columns([4, 1, 1], gap="small")
            cols[0].write(f"**{v.nome}** → {v.valor}")
            if cols[1].button("✏️", key=f"editv_{v.id}", **{"class": "small-btn"}):
                st.session_state.edit_var_id = v.id
                st.experimental_rerun()
            if cols[2].button("🗑️", key=f"delv_{v.id}", **{"class": "small-btn"}):
                delete_variavel(v.id)
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)
