import streamlit as st
import re
import math
from textos import TEXTOS
from supabase_db import get_supabase_client

ITEMS_PER_PAGE = 10


def add_category(name):
    sb = get_supabase_client()
    try:
        res = sb.table("categorias_custos").insert({"nome": name}).execute()
        st.success(f"Categoria '{name}' adicionada.")
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
        st.error(f"Erro ao buscar categorias: {e}")
        return [], 1, 0


def update_category(cat_id, new_name):
    sb = get_supabase_client()
    try:
        sb.table("categorias_custos").update(
            {"nome": new_name}).eq("id", cat_id).execute()
        st.success("Categoria atualizada.")
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
        st.success("Categoria deletada.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar categoria: {e}")
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
        st.error(f"Erro ao buscar variáveis: {e}")
        return [], 1, 0


def add_variable(name, value, category_id):
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").insert(
            {"nome": name, "valor": value, "categoria_id": category_id}).execute()
        st.success(f"Variável '{name}' adicionada.")
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar variável: {e}")
        return False


def update_variable(var_id, name, value, category_id):
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").update(
            {"nome": name, "valor": value, "categoria_id": category_id}).eq("id", var_id).execute()
        st.success("Variável atualizada.")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar variável: {e}")
        return False


def delete_variable(var_id):
    sb = get_supabase_client()
    try:
        sb.table("variaveis_custos").delete().eq("id", var_id).execute()
        st.success("Variável deletada.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar variável: {e}")
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
        st.error(f"Erro ao buscar produtos: {e}")
        return [], 1, 0


def add_product(name, formula, category_id):
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").insert(
            {"nome": name, "formula": formula, "categoria_id": category_id}).execute()
        st.success(f"Produto '{name}' adicionado.")
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar produto: {e}")
        return False


def update_product(prod_id, name, formula, category_id):
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").update(
            {"nome": name, "formula": formula, "categoria_id": category_id}).eq("id", prod_id).execute()
        st.success("Produto atualizado.")
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar produto: {e}")
        return False


def delete_product(prod_id):
    sb = get_supabase_client()
    try:
        sb.table("produtos_custos").delete().eq("id", prod_id).execute()
        st.success("Produto deletado.")
        return True
    except Exception as e:
        st.error(f"Erro ao deletar produto: {e}")
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
                          f"R$ {cost:.2f}" if cost else "Erro")
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


def get_all_variables_as_dict():
    sb = get_supabase_client()
    try:
        data = sb.table("variaveis_custos").select(
            "nome, valor").execute().data
        return {item["nome"]: item["valor"] for item in data}
    except Exception as e:
        st.error(f"Erro ao buscar todas as variáveis: {e}")
        return {}


def calculate_cost(formula):
    try:
        variables = get_all_variables_as_dict()
        # Substituir nomes de variáveis na fórmula pelos seus valores
        # A regex procura por palavras que não são operadores ou números
        # e que não estão entre aspas
        # Isso é uma simplificação e pode precisar ser mais robusto
        # dependendo da complexidade das fórmulas esperadas.

        def replace_var(match):
            var_name = match.group(0)
            if var_name in variables:
                return str(variables[var_name])
            else:
                st.warning(
                    f"Variável '{var_name}' não encontrada no banco de dados.")
                return "0.0"  # Retorna 0.0 para variáveis não encontradas

        # Usar re.sub para substituir todas as ocorrências de variáveis
        # A regex r'\b[a-zA-Z_][a-zA-Z0-9_]*\b' corresponde a nomes de variáveis válidos em Python
        processed_formula = re.sub(
            r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', replace_var, formula)

        # Avaliar a fórmula processada
        return eval(processed_formula)
    except NameError as ne:
        st.error(f"Erro na fórmula: Variável não definida - {ne}")
        return None
    except Exception as e:
        st.error(f"Erro ao calcular custo: {e}")
        return None


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
                    add_category(new_name)
                else:
                    update_category(st.session_state.editing_cat_id, new_name)
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
