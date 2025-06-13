import streamlit as st
import re
import math
from textos import TEXTOS
from supabase_db import get_supabase_client
from calculadora import calculate_cost

ITEMS_PER_PAGE = 10


def add_category(name):
    if not name:
        st.error("O nome da categoria não pode ser vazio.")
        return None
    sb = get_supabase_client()
    try:
        res = sb.table("categorias_custos").insert({"nome": name}).execute()
        return res.data[0]["id"]
    except Exception as e:
        st.error(f"Erro ao adicionar categoria: {e}")
        return None


def get_categories(search_term="", page=1):
    sb = get_supabase_client()
    offset = (page-1)*ITEMS_PER_PAGE
    try:
        q = sb.table("categorias_custos").select("*")
        if search_term:
            q = q.ilike("nome", f"%{search_term}%")
        data = q.execute().data or []
        total = len(data)
        pages = math.ceil(total/ITEMS_PER_PAGE) if total else 1
        return data[offset:offset+ITEMS_PER_PAGE], pages, total
    except Exception as e:
        # st.error(f"Erro ao buscar categorias: {e}")
        return [], 1, 0


def update_category(cat_id, new_name):
    if not new_name:
        st.error("O nome da categoria não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("categorias_custos").update(
            {"nome": new_name}).eq("id", cat_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar categoria: {e}")
        return False


def delete_category(cat_id):
    sb = get_supabase_client()
    try:
        in_var = sb.table("variaveis_custos").select("id").eq(
            "categoria_id", cat_id).limit(1).execute().data
        in_prod = sb.table("produtos_custos").select("id").eq(
            "categoria_id", cat_id).limit(1).execute().data
        if in_var or in_prod:
            st.error("Não pode deletar, categoria em uso.")
            return False
        sb.table("categorias_custos").delete().eq("id", cat_id).execute()
        # st.success("Categoria deletada.")
        return True
    except Exception as e:
        # st.error(f"Erro ao deletar categoria: {e}")
        return False


def get_variables(category_id=None, search_term="", page=1):
    sb = get_supabase_client()
    offset = (page-1)*ITEMS_PER_PAGE
    try:
        q = sb.table("variaveis_custos").select("*, categorias_custos(nome)")
        if category_id == "none":
            q = q.is_("categoria_id", None)
        elif category_id not in (None, "all"):
            q = q.eq("categoria_id", category_id)
        if search_term:
            q = q.ilike("nome", f"%{search_term}%")
        data = q.execute().data or []
        total = len(data)
        pages = math.ceil(total/ITEMS_PER_PAGE) if total else 1
        rows = data[offset:offset+ITEMS_PER_PAGE]
        formatted = [(r["id"], r["nome"], r["valor"], r["categoria_id"],
                      (r.get("categorias") or {}).get("nome")) for r in rows]
        return formatted, pages, total
    except Exception as e:
        # st.error(f"Erro ao buscar variáveis: {e}")
        return [], 1, 0


def add_variable(name, value, category_id):
    if not name:
        st.error("O nome da variável não pode ser vazio.")
        return False
    if value is None:
        st.error("O valor da variável não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").insert(
            {"nome": name, "valor": value, "categoria_id": category_id}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar variável: {e}")
        return False


def update_variable(var_id, name, value, category_id):
    if not name:
        st.error("O nome da variável não pode ser vazio.")
        return False
    if value is None:
        st.error("O valor da variável não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").update(
            {"nome": name, "valor": value, "categoria_id": category_id}).eq("id", var_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar variável: {e}")
        return False


def delete_variable(var_id):
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").delete().eq("id", var_id).execute()
        # st.success("Variável deletada.")
        return True
    except Exception as e:
        # st.error(f"Erro ao deletar variável: {e}")
        return False


def get_products(category_id=None, search_term="", page=1):
    sb = get_supabase_client()
    offset = (page-1)*ITEMS_PER_PAGE
    try:
        q = sb.table("produtos_custos").select("*, categorias_custos(nome)")
        if category_id == "none":
            q = q.is_("categoria_id", None)
        elif category_id not in (None, "all"):
            q = q.eq("categoria_id", category_id)
        if search_term:
            q = q.ilike("nome", f"%{search_term}%")
        data = q.execute().data or []
        total = len(data)
        pages = math.ceil(total/ITEMS_PER_PAGE) if total else 1
        rows = data[offset:offset+ITEMS_PER_PAGE]
        formatted = [(r["id"], r["nome"], r.get("formula"), r["categoria_id"], (r.get(
            "categorias") or {}).get("nome")) for r in rows]
        return formatted, pages, total
    except Exception as e:
        # st.error(f"Erro ao buscar produtos: {e}")
        return [], 1, 0


def add_product(name, formula, category_id):
    if not name:
        st.error("O nome do produto não pode ser vazio.")
        return False
    if not formula:
        st.error("A fórmula do produto não pode ser vazia.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").insert(
            {"nome": name, "formula": formula, "categoria_id": category_id}).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar produto: {e}")
        return False


def update_product(prod_id, name, formula, category_id):
    if not name:
        st.error("O nome do produto não pode ser vazio.")
        return False
    if not formula:
        st.error("A fórmula do produto não pode ser vazia.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").update(
            {"nome": name, "formula": formula, "categoria_id": category_id}).eq("id", prod_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar produto: {e}")
        return False


def delete_product(prod_id):
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").delete().eq("id", prod_id).execute()
        # st.success("Produto deletado.")
        return True
    except Exception as e:
        # st.error(f"Erro ao deletar produto: {e}")
        return False


def show_products():
    st.subheader(TEXTOS["prod_produtos"])
    if 'prod_page' not in st.session_state:
        st.session_state.prod_page = 1
    if 'editing_prod_id' not in st.session_state:
        st.session_state.editing_prod_id = None
    if 'show_prod_form' not in st.session_state:
        st.session_state.show_prod_form = False
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search = st.text_input("Buscar Produto", key="prod_search")
    with col2:
        cats, _, _ = get_categories()    # Note: get_categories defined above
        opts = {c["nome"]: c["id"] for c in cats}
        disp = {"Todos": "all", "Sem Categoria": "none", **opts}
        selected = st.selectbox("Filtrar por Categoria", list(
            disp.keys()), key="prod_cat_filter")
        cat_id = disp[selected]
    with col3:
        label = "➕ Adicionar Produto" if not st.session_state.show_prod_form else "❌ Fechar Formulário"
        if st.button(label, key="add_prod_btn"):
            st.session_state.show_prod_form = not st.session_state.show_prod_form
            st.session_state.editing_prod_id = 'new' if st.session_state.show_prod_form else None
            st.rerun()
    if st.session_state.editing_prod_id:
        with st.container():
            is_new = st.session_state.editing_prod_id == 'new'
            data = {}  # Initialize data as an empty dictionary
            sb = get_supabase_client()
            if not is_new:
                prod_result = sb.table("produtos_custos").select(
                    "*").eq("id", st.session_state.editing_prod_id).single().execute()
                if prod_result and prod_result.data:
                    data = prod_result.data
                else:
                    data = {}
            name = data.get("nome", "")
            formula = data.get("formula", "")
            cat_sel = data.get("categoria_id", None)
            form = st.form(key="prod_form")
            new_name = form.text_input("Nome do Produto", value=name)
            new_formula = form.text_area("Fórmula", value=formula)
            new_cat = form.selectbox("Categoria", ["(Nenhuma)"]+list(
                opts.keys()), index=0 if not cat_sel else list(opts.values()).index(cat_sel))
            if form.form_submit_button("Salvar"):
                cid = None if new_cat == "(Nenhuma)" else opts[new_cat]
                if is_new:
                    if add_product(new_name, new_formula, cid):
                        st.success(f"Produto \'{new_name}\' adicionado.")
                    # else: # Erro já é exibido dentro de add_product
                        # st.error(f"Erro ao adicionar produto \'{new_name}\'")
                else:
                    if update_product(st.session_state.editing_prod_id,
                                      new_name, new_formula, cid):
                        st.success("Produto atualizado.")
                    # else: # Erro já é exibido dentro de update_product
                        # st.error("Erro ao atualizar produto.")
                st.session_state.show_prod_form = False
                st.session_state.editing_prod_id = None
                st.rerun()
    data, pages, total = get_products(
        category_id=cat_id, search_term=search, page=st.session_state.prod_page)
    st.write(f"Total de Produtos: {total}")
    for pid, name, formula, cid, cname in data:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
                if cname:
                    st.caption(f"Categoria: {cname}")
                cost = calculate_cost(formula)
                st.metric("Custo Calculado",
                          f"R$ {cost:.2f}" if cost else "Erro")
                with st.expander("Ver Fórmula"):
                    st.code(formula or "(vazio)")
            with col2:
                if st.button("✏️", key=f"edit_{pid}"):
                    st.session_state.editing_prod_id = pid
                    st.session_state.show_prod_form = True
                    st.rerun()
                if st.button("🗑️", key=f"del_{pid}", type="primary"):
                    if delete_product(pid):
                        st.success("Produto deletado.")
                    else:
                        st.error("Erro ao deletar produto.")
                    st.rerun()


def show_production_costs():
    st.subheader(TEXTOS["prod_titulo"])
    choice = st.radio("", TEXTOS["prod_menu_opcoes"], horizontal=True,
                      key="prod_menu_radio", label_visibility="collapsed")
    if choice == "Produtos":
        show_products()
    elif choice == "Variáveis de Custos":
        show_variables()
    elif choice == "Gerenciar Categorias":
        show_categories()


def show_variables():
    st.subheader(TEXTOS["prod_variaveis"])
    if 'var_page' not in st.session_state:
        st.session_state.var_page = 1
    if 'editing_var_id' not in st.session_state:
        st.session_state.editing_var_id = None
    if 'show_var_form' not in st.session_state:
        st.session_state.show_var_form = False

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search = st.text_input("Buscar Variável", key="var_search")
    with col2:
        cats, _, _ = get_categories()
        opts = {c["nome"]: c["id"] for c in cats}
        disp = {"Todos": "all", "Sem Categoria": "none", **opts}
        selected = st.selectbox("Filtrar por Categoria", list(
            disp.keys()), key="var_cat_filter")
        cat_id = disp[selected]
    with col3:
        label = "➕ Adicionar Variável" if not st.session_state.show_var_form else "❌ Fechar Formulário"
        if st.button(label, key="add_var_btn"):
            st.session_state.show_var_form = not st.session_state.show_var_form
            st.session_state.editing_var_id = 'new' if st.session_state.show_var_form else None
            st.rerun()

    if st.session_state.editing_var_id:
        with st.container():
            is_new = st.session_state.editing_var_id == 'new'
            data = {}  # Initialize data as an empty dictionary
            sb = get_supabase_client()
            if not is_new:
                var_result = sb.table("variaveis_custos").select(
                    "*").eq("id", st.session_state.editing_var_id).single().execute()
                if var_result and var_result.data:
                    data = var_result.data
                else:
                    data = {}
            name = data.get("nome", "")
            value = data.get("valor", 0.0)
            cat_sel = data.get("categoria_id", None)

            form = st.form(key="var_form")
            new_name = form.text_input("Nome da Variável", value=name)
            new_value = form.number_input("Valor", value=value, format="%.2f")
            new_cat = form.selectbox("Categoria", ["(Nenhuma)"]+list(
                opts.keys()), index=0 if not cat_sel else list(opts.values()).index(cat_sel))

            if form.form_submit_button("Salvar"):
                cid = None if new_cat == "(Nenhuma)" else opts[new_cat]
                if is_new:
                    if add_variable(new_name, new_value, cid):
                        st.success(f"Variável \'{new_name}\' adicionada.")
                    # else: # Erro já é exibido dentro de add_variable
                        # st.error(f"Erro ao adicionar variável \'{new_name}\'")
                else:
                    if update_variable(
                            st.session_state.editing_var_id, new_name, new_value, cid):
                        st.success("Variável atualizada.")
                    # else: # Erro já é exibido dentro de update_variable
                        # st.error("Erro ao atualizar variável.")
                st.session_state.show_var_form = False
                st.session_state.editing_var_id = None
                st.rerun()

    data, pages, total = get_variables(
        category_id=cat_id, search_term=search, page=st.session_state.var_page)
    st.write(f"Total de Variáveis: {total}")

    for vid, name, value, cid, cname in data:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
                if cname:
                    st.caption(f"Categoria: {cname}")
                st.metric("Valor", f"R$ {value:.2f}")
            with col2:
                if st.button("✏️", key=f"edit_var_{vid}"):
                    st.session_state.editing_var_id = vid
                    st.session_state.show_var_form = True
                    st.rerun()
                if st.button("🗑️", key=f"del_var_{vid}", type="primary"):
                    if delete_variable(vid):
                        st.success("Variável deletada.")
                    else:
                        st.error("Erro ao deletar variável.")
                    st.rerun()


def show_categories():
    st.subheader("Gerenciar Categorias")
    if 'cat_page' not in st.session_state:
        st.session_state.cat_page = 1
    if 'editing_cat_id' not in st.session_state:
        st.session_state.editing_cat_id = None
    if 'show_cat_form' not in st.session_state:
        st.session_state.show_cat_form = False

    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Buscar Categoria", key="cat_search")
    with col2:
        label = "➕ Adicionar Categoria" if not st.session_state.show_cat_form else "❌ Fechar Formulário"
        if st.button(label, key="add_cat_btn"):
            st.session_state.show_cat_form = not st.session_state.show_cat_form
            st.session_state.editing_cat_id = 'new' if st.session_state.show_cat_form else None
            st.rerun()

    if st.session_state.editing_cat_id:
        with st.container():
            is_new = st.session_state.editing_cat_id == 'new'
            data = {}  # Initialize data as an empty dictionary
            sb = get_supabase_client()
            if not is_new:
                cat_result = sb.table("categorias_custos").select(
                    "*").eq("id", st.session_state.editing_cat_id).single().execute()
                if cat_result and cat_result.data:
                    data = cat_result.data
            name = data.get("nome", "")

            form = st.form(key="cat_form")
            new_name = form.text_input("Nome da Categoria", value=name)

            if form.form_submit_button("Salvar"):
                if is_new:
                    if add_category(new_name):
                        st.success(f"Categoria \'{new_name}\' adicionada.")
                    else:
                        st.error(f"Erro ao adicionar categoria \'{new_name}\'")
                else:
                    if update_category(st.session_state.editing_cat_id, new_name):
                        st.success("Categoria atualizada.")
                    else:
                        st.error("Erro ao atualizar categoria.")
                st.session_state.show_cat_form = False
                st.session_state.editing_cat_id = None
                st.rerun()

    data, pages, total = get_categories(
        search_term=search, page=st.session_state.cat_page)
    st.write(f"Total de Categorias: {total}")

    for category in data:
        cid = category["id"]
        name = category["nome"]
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key=f"edit_cat_{cid}"):
                    st.session_state.editing_cat_id = cid
                    st.session_state.show_cat_form = True
                    st.rerun()
                if st.button("🗑️", key=f"del_cat_{cid}", type="primary"):
                    delete_category(cid)
                    st.rerun()
