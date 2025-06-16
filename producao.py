import streamlit as st
import re
import math
from textos import TEXTOS
from supabase_db import get_supabase_client
from calculadora import calculate_cost

# --- Funções de Exibição de Mensagens ---


def display_error(message, e=None):
    error_text = f"Erro: {message}"
    if e:
        error_text += f" Detalhes: {e}"
    st.error(error_text)


def display_success(message):
    st.success(message)


ITEMS_PER_PAGE = 10

# --- Funções para Categorias de Produtos ---


def add_category_product(name):
    if not name:
        display_error("O nome da categoria de produto não pode ser vazio.")
        return None
    sb = get_supabase_client()
    try:
        res = sb.table("categorias_produtos").insert({"nome": name}).execute()
        display_success(
            f"Categoria de produto '{name}' adicionada com sucesso.")
        return res.data[0]["id"]
    except Exception as e:
        display_error(f"Erro ao adicionar categoria de produto: {e}", e)
        return None


def get_categories_product(search_term: str = "", page: int = 1):
    sb = get_supabase_client()
    offset = (page - 1) * ITEMS_PER_PAGE
    try:
        # seleciona só os campos que precisamos
        q = sb.table("categorias_produtos").select("id", "nome")
        if search_term:
            q = q.ilike("nome", f"%{search_term}%")
        raw = q.execute().data or []
        total = len(raw)
        pages = math.ceil(total / ITEMS_PER_PAGE) if total else 1

        # faz o slicing da página
        page_items = raw[offset: offset + ITEMS_PER_PAGE]
        # converte para lista de tuplas (id, nome)
        data = [(item["id"], item["nome"]) for item in page_items]

        return data, pages, total
    except Exception as e:
        display_error(f"Erro ao buscar categorias de produto: {e}", e)
        return [], 1, 0


def update_category_product(cat_id, new_name):
    if not new_name:
        display_error("O nome da categoria de produto não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("categorias_produtos").update(
            {"nome": new_name}).eq("id", cat_id).execute()
        display_success("Categoria de produto atualizada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao atualizar categoria de produto: {e}", e)
        return False


def delete_category_product(cat_id):
    sb = get_supabase_client()
    try:
        in_prod = sb.table("produtos_custos").select("id").eq(
            "categoria_id", cat_id).limit(1).execute().data
        if in_prod:
            display_error("Não pode deletar, categoria de produto em uso.")
            return False
        sb.table("categorias_produtos").delete().eq("id", cat_id).execute()
        display_success("Categoria de produto deletada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao deletar categoria de produto: {e}", e)
        return False

# --- Funções para Categorias de Variáveis ---


def add_category_variable(name):
    if not name:
        display_error("O nome da categoria de variável não pode ser vazio.")
        return None
    sb = get_supabase_client()
    try:
        res = sb.table("categorias_variaveis").insert({"nome": name}).execute()
        display_success(
            f"Categoria de variável '{name}' adicionada com sucesso.")
        return res.data[0]["id"]
    except Exception as e:
        display_error(f"Erro ao adicionar categoria de variável: {e}", e)
        return None


def get_categories_variable(search_term: str = "", page: int = 1):
    sb = get_supabase_client()
    offset = (page - 1) * ITEMS_PER_PAGE
    try:
        # seleciona só os campos que precisamos
        q = sb.table("categorias_variaveis").select("id", "nome")
        if search_term:
            q = q.ilike("nome", f"%{search_term}%")
        raw = q.execute().data or []
        total = len(raw)
        pages = math.ceil(total / ITEMS_PER_PAGE) if total else 1

        # faz o slicing da página
        page_items = raw[offset: offset + ITEMS_PER_PAGE]
        # converte para lista de tuplas (id, nome)
        data = [(item["id"], item["nome"]) for item in page_items]

        return data, pages, total
    except Exception as e:
        display_error(f"Erro ao buscar categorias de variável: {e}", e)
        return [], 1, 0


def update_category_variable(cat_id, new_name):
    if not new_name:
        display_error("O nome da categoria de variável não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("categorias_variaveis").update(
            {"nome": new_name}).eq("id", cat_id).execute()
        display_success("Categoria de variável atualizada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao atualizar categoria de variável: {e}", e)
        return False


def delete_category_variable(cat_id):
    sb = get_supabase_client()
    try:
        in_var = sb.table("variaveis_custos").select("id").eq(
            "categoria_id", cat_id).limit(1).execute().data
        if in_var:
            display_error("Não pode deletar, categoria de variável em uso.")
            return False
        sb.table("categorias_variaveis").delete().eq("id", cat_id).execute()
        display_success("Categoria de variável deletada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao deletar categoria de variável: {e}", e)
        return False

# --- Funções de Variáveis de Custo ---


def get_variables(category_id=None, search_term="", page=1):
    sb = get_supabase_client()
    offset = (page-1)*ITEMS_PER_PAGE
    try:
        q = sb.table("variaveis_custos").select(
            "*, categorias_variaveis(nome)")
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
                      (r.get("categorias_variaveis") or {}).get("nome")) for r in rows]
        return formatted, pages, total
    except Exception as e:
        display_error(f"Erro ao buscar variáveis: {e}", e)
        return [], 1, 0


def add_variable(name, value, category_id):
    if not name:
        display_error("O nome da variável não pode ser vazio.")
        return False
    if value is None:
        display_error("O valor da variável não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").insert(
            {"nome": name, "valor": value, "categoria_id": category_id}).execute()
        display_success(f"Variável '{name}' adicionada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao adicionar variável: {e}", e)
        return False


def update_variable(var_id, name, value, category_id):
    if not name:
        display_error("O nome da variável não pode ser vazio.")
        return False
    if value is None:
        display_error("O valor da variável não pode ser vazio.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").update(
            {"nome": name, "valor": value, "categoria_id": category_id}).eq("id", var_id).execute()
        display_success("Variável atualizada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao atualizar variável: {e}", e)
        return False


def delete_variable(var_id):
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").delete().eq("id", var_id).execute()
        display_success("Variável deletada com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao deletar variável: {e}", e)
        return False

# --- Funções de Produtos de Custo ---


def get_products(category_id=None, search_term="", page=1):
    sb = get_supabase_client()
    offset = (page-1)*ITEMS_PER_PAGE
    try:
        q = sb.table("produtos_custos").select("*, categorias_produtos(nome)")
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
            "categorias_produtos") or {}).get("nome")) for r in rows]
        return formatted, pages, total
    except Exception as e:
        display_error(f"Erro ao buscar produtos: {e}", e)
        return [], 1, 0


def add_product(name, formula, category_id):
    if not name:
        display_error("O nome do produto não pode ser vazio.")
        return False
    if not formula:
        display_error("A fórmula do produto não pode ser vazia.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").insert(
            {"nome": name, "formula": formula, "categoria_id": category_id}).execute()
        display_success(f"Produto '{name}' adicionado com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao adicionar produto: {e}", e)
        return False


def update_product(prod_id, name, formula, category_id):
    if not name:
        display_error("O nome do produto não pode ser vazio.")
        return False
    if not formula:
        display_error("A fórmula do produto não pode ser vazia.")
        return False
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").update(
            {"nome": name, "formula": formula, "categoria_id": category_id}).eq("id", prod_id).execute()
        display_success("Produto atualizado com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao atualizar produto: {e}", e)
        return False


def delete_product(prod_id):
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").delete().eq("id", prod_id).execute()
        display_success("Produto deletado com sucesso.")
        return True
    except Exception as e:
        display_error(f"Erro ao deletar produto: {e}", e)
        return False

# --- Funções de UI ---


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
        cats, _, _ = get_categories_product()
        opts = {c[1]: c[0] for c in cats}
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
            data = {}
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
            product_categories, _, _ = get_categories_product()
            product_opts = {c[1]: c[0] for c in product_categories}
            new_cat = form.selectbox("Categoria", ["(Nenhuma)"] + list(
                product_opts.keys()), index=0 if not cat_sel else (list(product_opts.values()).index(cat_sel) + 1 if cat_sel in product_opts.values() else 0))
            if form.form_submit_button("Salvar"):
                cid = None if new_cat == "(Nenhuma)" else product_opts[new_cat]
                if is_new:
                    add_product(new_name, new_formula, cid)
                else:
                    update_product(st.session_state.editing_prod_id,
                                   new_name, new_formula, cid)
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
                          f"R$ {cost:.2f}" if cost is not None else "Erro")
                with st.expander("Ver Fórmula"):
                    st.code(formula or "(vazio)")
            with col2:
                if st.button("✏️", key=f"edit_{pid}"):
                    st.session_state.editing_prod_id = pid
                    st.session_state.show_prod_form = True
                    st.rerun()
                if st.button("🗑️", key=f"del_{pid}", type="primary"):
                    delete_product(pid)
                    st.rerun()

    if pages > 1:
        st.markdown("<div class='pagination-container'>",
                    unsafe_allow_html=True)
        cols = st.columns(pages)
        for i in range(pages):
            with cols[i]:
                if st.button(str(i+1), key=f"prod_page_{i+1}"):
                    st.session_state.prod_page = i+1
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


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
        cats, _, _ = get_categories_variable()
        opts = {c[1]: c[0] for c in cats}
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
            data = {}
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
            variable_categories, _, _ = get_categories_variable()
            variable_opts = {c[1]: c[0] for c in variable_categories}
            new_cat = form.selectbox("Categoria", ["(Nenhuma)"] + list(
                variable_opts.keys()), index=0 if not cat_sel else (list(variable_opts.values()).index(cat_sel) + 1 if cat_sel in variable_opts.values() else 0))

            if form.form_submit_button("Salvar"):
                cid = None if new_cat == "(Nenhuma)" else variable_opts[new_cat]
                if is_new:
                    add_variable(new_name, new_value, cid)
                else:
                    update_variable(
                        st.session_state.editing_var_id, new_name, new_value, cid)
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
                    delete_variable(vid)
                    st.rerun()

    if pages > 1:
        st.markdown("<div class='pagination-container'>",
                    unsafe_allow_html=True)
        cols = st.columns(pages)
        for i in range(pages):
            with cols[i]:
                if st.button(str(i+1), key=f"var_page_{i+1}"):
                    st.session_state.var_page = i+1
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def show_categories():
    st.subheader("Gerenciar Categorias")
    if 'cat_page' not in st.session_state:
        st.session_state.cat_page = 1
    if 'editing_cat_id' not in st.session_state:
        st.session_state.editing_cat_id = None
    if 'show_cat_form' not in st.session_state:
        st.session_state.show_cat_form = False
    if 'category_type' not in st.session_state:
        st.session_state.category_type = "Produtos"

    category_type_choice = st.radio("Tipo de Categoria", [
                                    "Produtos", "Variáveis"], horizontal=True, key="category_type_radio")
    st.session_state.category_type = category_type_choice

    if st.session_state.category_type == "Produtos":
        add_func = add_category_product
        get_func = get_categories_product
        update_func = update_category_product
        delete_func = delete_category_product
        table_name = "categorias_produtos"
    else:
        add_func = add_category_variable
        get_func = get_categories_variable
        update_func = update_category_variable
        delete_func = delete_category_variable
        table_name = "categorias_variaveis"

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            f"Buscar Categoria de {st.session_state.category_type}", key=f"cat_search_{st.session_state.category_type}")
    with col2:
        label = "➕ Adicionar Categoria" if not st.session_state.show_cat_form else "❌ Fechar Formulário"
        if st.button(label, key=f"add_cat_btn_{st.session_state.category_type}"):
            st.session_state.show_cat_form = not st.session_state.show_cat_form
            st.session_state.editing_cat_id = 'new' if st.session_state.show_cat_form else None
            st.rerun()

    if st.session_state.editing_cat_id:
        with st.container():
            is_new = st.session_state.editing_cat_id == 'new'
            data = {}
            if not is_new:
                sb = get_supabase_client()
                cat_result = sb.table(table_name).select(
                    "*").eq("id", st.session_state.editing_cat_id).single().execute()
                if cat_result and cat_result.data:
                    data = cat_result.data
                else:
                    data = {}
            name = data.get("nome", "")
            form = st.form(key=f"cat_form_{st.session_state.category_type}")
            new_name = form.text_input("Nome da Categoria", value=name)
            if form.form_submit_button("Salvar"):
                if is_new:
                    add_func(new_name)
                else:
                    update_func(st.session_state.editing_cat_id, new_name)
                st.session_state.show_cat_form = False
                st.session_state.editing_cat_id = None
                st.rerun()

    data, pages, total = get_func(
        search_term=search, page=st.session_state.cat_page)
    st.write(
        f"Total de Categorias de {st.session_state.category_type}: {total}")

    for cid, name in data:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key=f"edit_cat_{cid}_{st.session_state.category_type}"):
                    st.session_state.editing_cat_id = cid
                    st.session_state.show_cat_form = True
                    st.rerun()
                if st.button("🗑️", key=f"del_cat_{cid}_{st.session_state.category_type}", type="primary"):
                    delete_func(cid)
                    st.rerun()

    if pages > 1:
        st.markdown("<div class='pagination-container'>",
                    unsafe_allow_html=True)
        cols = st.columns(pages)
        for i in range(pages):
            with cols[i]:
                if st.button(str(i+1), key=f"cat_page_{i+1}_{st.session_state.category_type}"):
                    st.session_state.cat_page = i+1
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
