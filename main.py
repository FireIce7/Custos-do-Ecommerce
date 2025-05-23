import streamlit as st
import sqlite3
import re  # Importar regex para a fórmula
import math  # Para paginação

# ——— PRIMEIRO COMANDO STREAMLIT NO ARQUIVO ———
try:
    st.set_page_config(page_title="Calculadora de Custos", layout="wide")
except st.errors.StreamlitAPIException:
    pass

# --- CSS Personalizado (v7 - Correções Botões/Espaçamento) ---
st.markdown("""
<style>
    /* Título da Navegação na Sidebar */
    .st-emotion-cache-10oheav p {
        font-size: 22px !important;
        font-weight: bold;
        margin-bottom: 10px;
    }

    /* Itens do menu na Sidebar */
    .st-emotion-cache-16idsys p, .st-emotion-cache-16idsys span {
        font-size: 18px !important;
    }

    /* Título do Expander do Produto/Variável */
    .st-emotion-cache-1avcm0n span {
        font-size: 22px !important;
        font-weight: bold;
    }

    /* Nome da Categoria na listagem */
    .category-list-item {
        font-size: 18px !important;
        margin-left: 5px;
    }

    /* Valor da Métrica (Custo Atual) */
    .st-emotion-cache-1g6goon div {
        font-size: 22px !important;
        line-height: 1.3;
    }
    /* Rótulo da Métrica (Custo Atual) */
    .st-emotion-cache-1g6goon label {
        font-size: 16px !important;
    }

    /* Botões Editar/Deletar lado a lado (v7 - Largura ajustada) */
    .action-buttons-container .stButton>button {
        margin-right: 5px !important;
        padding: 0.25rem 0.75rem !important; /* Aumentar padding horizontal */
        font-size: 14px !important; /* Aumentar fonte ligeiramente */
        min-width: 80px; /* Garantir largura mínima */
        text-align: center;
    }

    /* Container para botões de ação (Variáveis/Produtos/Categorias) - Espaçamento reduzido */
    .action-buttons-container div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important; /* Aumentar um pouco o gap para acomodar botões maiores */
        align-items: center; /* Alinhar verticalmente */
    }

    /* Botões dentro de formulários (Add/Cancel) - Tamanho ajustado */
    div[data-testid="stFormSubmitButton"] button {
         font-size: 14px !important;
         padding: 0.5rem 1rem !important;
         min-width: 100px; /* Largura mínima */
    }

    /* Paginação */
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    .pagination-container .stButton button {
        margin: 0 5px !important;
    }

    /* Espaçamento Fórmula/Valores (v7) */
    .formula-section p {
        margin-bottom: 0.1rem !important; /* Reduzir margem inferior dos parágrafos */
    }

    /* Outros ajustes gerais de fonte */
    .st-emotion-cache-1qg05tj p, .st-emotion-cache-1qg05tj span { /* Menus de rádio */
        font-size: 16px !important;
    }
    .st-emotion-cache-183lzff p { /* Submenus */
        font-size: 16px !important;
    }

</style>
""", unsafe_allow_html=True)

# --- Constantes --- #
ITEMS_PER_PAGE = 10

# --- Funções de Banco (SEM usar Streamlit) ---


def get_connection():
    conn = sqlite3.connect("data.db", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ("variable", "product")),
            UNIQUE(name, type)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS production_variables (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            value REAL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            formula TEXT,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
        )
        """
    )
    try:
        c.execute(
            "ALTER TABLE production_variables ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute(
            "ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

# --- Funções CRUD para Categorias (v6 - Paginação/Filtro) ---


def add_category(name, type):
    conn = get_connection()
    c = conn.cursor()
    category_id = None
    try:
        c.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type))
        conn.commit()
        category_id = c.lastrowid
        st.success(f"Categoria \'{name}\' adicionada.")
    except sqlite3.IntegrityError:
        st.error(f"Categoria \'{name}\' já existe para o tipo \'{type}\'.")
    except Exception as e:
        st.error(f"Erro ao adicionar categoria: {e}")
    finally:
        conn.close()
    return category_id


def get_categories(type, search_term="", page=1):
    conn = get_connection()
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE
    base_query = "FROM categories WHERE type = ?"
    params = [type]

    if search_term:
        base_query += " AND name LIKE ?"
        params.append(f"%{search_term}%")

    count_query = f"SELECT COUNT(*) {base_query}"
    total_items = c.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    data_query = f"SELECT id, name {base_query} ORDER BY name LIMIT ? OFFSET ?"
    params.extend([ITEMS_PER_PAGE, offset])
    rows = c.execute(data_query, params).fetchall()

    conn.close()
    return rows, total_pages, total_items


def update_category(category_id, new_name):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("UPDATE categories SET name = ? WHERE id = ?",
                  (new_name, category_id))
        conn.commit()
        st.success("Categoria atualizada.")
        success = True
    except sqlite3.IntegrityError:
        st.error(f"Já existe uma categoria com o nome \'{new_name}\'.")
    except Exception as e:
        st.error(f"Erro ao atualizar categoria: {e}")
    finally:
        conn.close()
    return success


def delete_category(category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        st.success("Categoria deletada.")
        success = True
    except Exception as e:
        st.error(f"Erro ao deletar categoria: {e}")
    finally:
        conn.close()
    return success

# --- Funções CRUD para Variáveis (v6 - Paginação/Filtro) ---


def get_variables(category_id=None, search_term="", page=1):
    conn = get_connection()
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE

    base_query = "FROM production_variables v LEFT JOIN categories c ON v.category_id = c.id"
    where_clauses = []
    params = []

    if category_id == "all":
        pass
    elif category_id == "none":
        where_clauses.append("v.category_id IS NULL")
    elif category_id is not None:
        where_clauses.append("v.category_id = ?")
        params.append(category_id)

    if search_term:
        where_clauses.append("v.name LIKE ?")
        params.append(f"%{search_term}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(v.id) {base_query}"
    total_items = c.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    data_query = f"SELECT v.id, v.name, v.value, v.category_id, c.name as category_name {base_query} ORDER BY v.name LIMIT ? OFFSET ?"
    params.extend([ITEMS_PER_PAGE, offset])
    rows = c.execute(data_query, params).fetchall()

    conn.close()
    return rows, total_pages, total_items


def add_variable(name, value, category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute(
            "INSERT INTO production_variables (name, value, category_id) VALUES (?, ?, ?)", (name, value, category_id))
        conn.commit()
        st.success(f"Variável \'{name}\' adicionada.")
        success = True
    except sqlite3.IntegrityError:
        st.error(f"Variável com nome \'{name}\' já existe.")
    except Exception as e:
        st.error(f"Erro ao adicionar variável: {e}")
    finally:
        conn.close()
    return success


def update_variable(var_id, name, value, category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("UPDATE production_variables SET name = ?, value = ?, category_id = ? WHERE id = ?",
                  (name, value, category_id, var_id))
        conn.commit()
        st.success("Variável atualizada.")
        success = True
    except sqlite3.IntegrityError:
        st.error(f"Nome de variável \'{name}\' já está em uso.")
    except Exception as e:
        st.error(f"Erro ao atualizar variável: {e}")
    finally:
        conn.close()
    return success


def delete_variable(var_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("DELETE FROM production_variables WHERE id = ?", (var_id,))
        conn.commit()
        st.success("Variável deletada.")
        success = True
    except Exception as e:
        st.error(f"Erro ao deletar variável: {e}")
    finally:
        conn.close()
    return success

# --- Funções CRUD para Produtos (v6 - Paginação/Filtro) ---


def get_products(category_id=None, search_term="", page=1):
    conn = get_connection()
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE

    base_query = "FROM products p LEFT JOIN categories c ON p.category_id = c.id"
    where_clauses = []
    params = []

    if category_id == "all":
        pass
    elif category_id == "none":
        where_clauses.append("p.category_id IS NULL")
    elif category_id is not None:
        where_clauses.append("p.category_id = ?")
        params.append(category_id)

    if search_term:
        where_clauses.append("p.name LIKE ?")
        params.append(f"%{search_term}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(p.id) {base_query}"
    total_items = c.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    data_query = f"SELECT p.id, p.name, p.formula, p.category_id, c.name as category_name {base_query} ORDER BY p.name LIMIT ? OFFSET ?"
    params.extend([ITEMS_PER_PAGE, offset])
    rows = c.execute(data_query, params).fetchall()

    conn.close()
    return rows, total_pages, total_items


def add_product(name, formula, category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute(
            "INSERT INTO products (name, formula, category_id) VALUES (?, ?, ?)", (name, formula, category_id))
        conn.commit()
        st.success(f"Produto \'{name}\' adicionado.")
        success = True
    except sqlite3.IntegrityError:
        st.error(f"Produto com nome \'{name}\' já existe.")
    except Exception as e:
        st.error(f"Erro ao adicionar produto: {e}")
    finally:
        conn.close()
    return success


def update_product(prod_id, name, formula, category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("UPDATE products SET name = ?, formula = ?, category_id = ? WHERE id = ?",
                  (name, formula, category_id, prod_id))
        conn.commit()
        st.success("Produto atualizado.")
        success = True
    except sqlite3.IntegrityError:
        st.error(f"Nome de produto \'{name}\' já está em uso.")
    except Exception as e:
        st.error(f"Erro ao atualizar produto: {e}")
    finally:
        conn.close()
    return success


def delete_product(prod_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("DELETE FROM products WHERE id = ?", (prod_id,))
        conn.commit()
        st.success("Produto deletado.")
        success = True
    except Exception as e:
        st.error(f"Erro ao deletar produto: {e}")
    finally:
        conn.close()
    return success

# --- Cálculo de custo ---


def get_variable_values():
    conn = get_connection()
    c = conn.cursor()  # <<< CORREÇÃO: Adicionar cursor
    rows = c.execute("SELECT name, value FROM production_variables").fetchall()
    conn.close()
    return {name: val for name, val in rows}


def calculate_cost(formula):
    var_values = get_variable_values()
    try:
        variable_names_in_formula = set(
            re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", formula))
        missing_vars = [
            name for name in variable_names_in_formula if name not in var_values]
        if missing_vars:
            return None

        cost = eval(formula, {"__builtins__": {}}, var_values)
        return cost
    except Exception as e:
        return None

# --- Função de Formatação de Fórmula ---


def format_formula_values_string(formula):
    var_values = get_variable_values()
    value_formula = formula
    for name in sorted(var_values.keys(), key=len, reverse=True):
        value = var_values.get(name)
        if value is None:
            continue

        if isinstance(value, (int, float)):
            if value == int(value):
                value_str = str(int(value))
            else:
                value_str = f"{value:.2f}"
        else:
            value_str = str(value)

        value_formula = re.sub(
            r"(?<![a-zA-Z0-9_])" + re.escape(name) + r"(?![a-zA-Z0-9_])", value_str, value_formula)

    value_formula_compact = re.sub(r"\s*([+\-*/()])\s*", r"\1", value_formula)
    return value_formula_compact

# --- Componente de Paginação ---


def pagination_component(total_pages, current_page, key_suffix):
    if total_pages <= 1:
        return current_page

    st.markdown("<div class=\"pagination-container\">", unsafe_allow_html=True)
    cols = st.columns([1, 1, 3, 1, 1])

    with cols[0]:
        if st.button("◀️◀️", key=f"first_{key_suffix}", disabled=(current_page == 1)):
            return 1
    with cols[1]:
        if st.button("◀️", key=f"prev_{key_suffix}", disabled=(current_page == 1)):
            return current_page - 1
    with cols[2]:
        st.write(f"Página {current_page} de {total_pages}")
    with cols[3]:
        if st.button("▶️", key=f"next_{key_suffix}", disabled=(current_page == total_pages)):
            return current_page + 1
    with cols[4]:
        if st.button("▶️▶️", key=f"last_{key_suffix}", disabled=(current_page == total_pages)):
            return total_pages

    st.markdown("</div>", unsafe_allow_html=True)
    return current_page

# --- Cálculo de preço (v6 - Layout Aprimorado) ---


def show_price_calculator():
    st.header("Calculadora de Preços")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Dados Base")
            quantidade_kg = st.number_input(
                "Quantidade (KG)", min_value=0.1, format="%.2f", key="quantidade_kg", value=1.0)
            preco_ps = st.number_input(
                "Preço do PS (por KG)", min_value=0.0, format="%.2f", key="preco_ps")
            valor_frete = st.number_input(
                "Valor do Frete (total)", min_value=0.0, format="%.2f", key="valor_frete")
            percent_perdas = st.number_input(
                "% de Perdas", min_value=0.0, max_value=100.0, format="%.1f", key="percent_perdas", value=5.0)

        with col2:
            st.subheader("Custos Adicionais")
            tem_limpeza = st.radio(
                "Limpeza/Granulação?", ["Não", "Sim"], key="tem_limpeza", horizontal=True)
            valor_limpeza = 0.0
            if tem_limpeza == "Sim":
                valor_limpeza = st.number_input(
                    "Valor Limpeza/Gran. (por KG)", min_value=0.0, format="%.2f", key="valor_limpeza")

            tem_laminacao = st.radio(
                "Laminação?", ["Não", "Sim"], key="tem_laminacao", horizontal=True)
            valor_laminacao = 0.0
            if tem_laminacao == "Sim":
                valor_laminacao = st.number_input(
                    "Valor Laminação (por KG)", min_value=0.0, format="%.2f", key="valor_laminacao")

            tem_ipi = st.radio(
                "IPI?", ["Não", "Sim"], key="tem_ipi", horizontal=True)
            percent_ipi = 0.0
            if tem_ipi == "Sim":
                percent_ipi = st.number_input(
                    "% IPI", min_value=0.0, max_value=100.0, format="%.1f", key="percent_ipi")

    st.divider()

    if st.button("Calcular Preço Final (Lógica Pendente)", key="calcular_preco_final", use_container_width=True):
        custo_material = preco_ps * quantidade_kg
        custo_processamento = (valor_limpeza + valor_laminacao) * quantidade_kg
        custo_total_base = custo_material + valor_frete + custo_processamento
        custo_com_perdas = custo_total_base / \
            (1 - percent_perdas / 100) if percent_perdas < 100 else float("inf")
        valor_ipi = custo_com_perdas * \
            (percent_ipi / 100) if tem_ipi == "Sim" else 0
        preco_final_calculado = custo_com_perdas + valor_ipi

        st.subheader("Resultado do Cálculo")
        if preco_final_calculado == float("inf"):
            st.error("Erro: Percentual de perdas não pode ser 100% ou maior.")
        else:
            st.metric("Preço Final Sugerido",
                      f"R$ {preco_final_calculado:.2f}")
            st.info(
                "Nota: A lógica exata do cálculo final ainda precisa ser implementada conforme sua necessidade.")

    else:
        st.subheader("Resultado do Cálculo")
        st.info("Preencha os campos acima e clique em calcular.")


# --- Funções de interface (v7 - Correções Forms/Layout) --- #

def manage_categories(item_type):
    st.subheader(f"Gerenciar Categorias de {item_type.capitalize()}s")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Categorias Existentes**")
        search_term = st.text_input(
            "Filtrar por nome", key=f"search_cat_{item_type}")

        if f"page_cat_{item_type}" not in st.session_state:
            st.session_state[f"page_cat_{item_type}"] = 1

        current_page = st.session_state[f"page_cat_{item_type}"]
        categories, total_pages, total_items = get_categories(
            item_type, search_term, current_page)

        if categories:
            st.write(
                f"Mostrando {len(categories)} de {total_items} categorias.")
            for cat_id, cat_name in categories:
                if st.session_state.get(f"editing_cat_{cat_id}"):
                    st.session_state[f"confirm_delete_cat_{cat_id}"] = False

                cat_cols = st.columns([4, 1, 1])
                with cat_cols[0]:
                    if st.session_state.get(f"editing_cat_{cat_id}"):
                        # Formulário de Edição de Categoria (v7 - Correção)
                        with st.form(key=f"edit_cat_form_{cat_id}"):
                            new_name = st.text_input(
                                "Novo nome", value=cat_name, key=f"edit_cat_name_{cat_id}")
                            edit_btn_cols = st.columns(2)
                            with edit_btn_cols[0]:
                                submitted_save = st.form_submit_button(
                                    "Salvar")
                            with edit_btn_cols[1]:
                                submitted_cancel = st.form_submit_button(
                                    "Cancelar", type="secondary")

                            if submitted_save:
                                if update_category(cat_id, new_name):
                                    st.session_state[f"editing_cat_{cat_id}"] = False
                                    st.rerun()
                            if submitted_cancel:
                                st.session_state[f"editing_cat_{cat_id}"] = False
                                st.rerun()
                    else:
                        st.markdown(
                            f"<span class=\"category-list-item\">- {cat_name}</span>", unsafe_allow_html=True)

                # Botões fora do form de edição
                st.markdown("<div class=\"action-buttons-container\">",
                            unsafe_allow_html=True)
                with cat_cols[1]:
                    if not st.session_state.get(f"editing_cat_{cat_id}") and not st.session_state.get(f"confirm_delete_cat_{cat_id}"):
                        if st.button("Editar", key=f"edit_cat_{cat_id}", help="Editar Categoria"):
                            st.session_state[f"editing_cat_{cat_id}"] = True
                            st.rerun()
                with cat_cols[2]:
                    if not st.session_state.get(f"editing_cat_{cat_id}") and not st.session_state.get(f"confirm_delete_cat_{cat_id}"):
                        if st.button("Deletar", key=f"delete_cat_{cat_id}", help="Deletar Categoria"):
                            st.session_state[f"confirm_delete_cat_{cat_id}"] = True
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

                if st.session_state.get(f"confirm_delete_cat_{cat_id}"):
                    st.warning(
                        f"Tem certeza que deseja deletar a categoria \'{cat_name}\'? Itens nesta categoria ficarão sem categoria.")
                    confirm_cols = st.columns(2)
                    with confirm_cols[0]:
                        if st.button("Confirmar Exclusão", key=f"confirm_del_btn_{cat_id}"):
                            if delete_category(cat_id):
                                st.session_state[f"confirm_delete_cat_{cat_id}"] = False
                                st.rerun()
                    with confirm_cols[1]:
                        if st.button("Cancelar Exclusão", key=f"cancel_del_btn_{cat_id}", type="secondary"):
                            st.session_state[f"confirm_delete_cat_{cat_id}"] = False
                            st.rerun()
            st.divider()
            new_page = pagination_component(
                total_pages, current_page, f"cat_{item_type}")
            if new_page != current_page:
                st.session_state[f"page_cat_{item_type}"] = new_page
                st.rerun()

        else:
            st.info(f"Nenhuma categoria de {item_type} encontrada" + (
                f" com o termo \'{search_term}\'" if search_term else "."))

    with col2:
        with st.form(key=f"add_{item_type}_category_form"):
            st.subheader("Adicionar Nova")
            new_cat_name = st.text_input(
                "Nome da Categoria", label_visibility="collapsed", placeholder="Nome da Categoria")
            submitted = st.form_submit_button("Adicionar Categoria")
            if submitted:
                if new_cat_name:
                    category_id = add_category(new_cat_name, item_type)
                    if category_id is not None:
                        st.rerun()
                else:
                    st.warning("Digite um nome para a categoria.")


def select_category(item_type, current_category_id=None, key_prefix="", allow_none=True):
    conn = get_connection()
    c = conn.cursor()
    categories_list = c.execute(
        "SELECT id, name FROM categories WHERE type = ? ORDER BY name", (item_type,)).fetchall()
    conn.close()

    category_options = {name: id for id, name in categories_list}
    category_names = list(category_options.keys())

    options_list = []
    if allow_none:
        options_list.append("Sem Categoria")
    options_list.extend(category_names)

    default_index = 0
    selected_cat_name = None
    if current_category_id:
        for name, id_ in category_options.items():
            if id_ == current_category_id:
                selected_cat_name = name
                break

    if selected_cat_name and selected_cat_name in options_list:
        default_index = options_list.index(selected_cat_name)
    elif not current_category_id and allow_none and "Sem Categoria" in options_list:
        default_index = options_list.index("Sem Categoria")

    selected_option = st.selectbox(
        "Categoria",
        options=options_list,
        index=default_index,
        key=f"{key_prefix}_select_cat_{item_type}"
    )

    if selected_option == "Sem Categoria":
        return None
    else:
        return category_options.get(selected_option)


def show_production_costs():
    st.header("Custos de Produção")

    submenu_options = ["Produtos",
                       "Variáveis de Custos", "Gerenciar Categorias"]
    submenu = st.radio("Menu", submenu_options,
                       horizontal=True, key="prod_cost_submenu")

    if submenu == "Variáveis de Custos":
        show_variables()
    elif submenu == "Produtos":
        show_products()
    elif submenu == "Gerenciar Categorias":
        type_options = ["Produtos", "Variáveis"]
        type_to_manage = st.radio(
            "Gerenciar categorias de:", type_options, horizontal=True, key="cat_type_manage")
        item_type_db = "product" if type_to_manage == "Produtos" else "variable"
        manage_categories(item_type_db)


def show_variables():
    st.subheader("Variáveis de Produção")

    if "page_var" not in st.session_state:
        st.session_state.page_var = 1
    if "search_var" not in st.session_state:
        st.session_state.search_var = ""
    if "cat_filter_var" not in st.session_state:
        st.session_state.cat_filter_var = "Todas"

    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        categories = get_categories("variable")[0]
        category_options = {name: id for id, name in categories}
        filter_cat_display_options = {"Todas": "all", "Sem Categoria": "none"}
        filter_cat_display_options.update(category_options)
        filter_display_names = list(filter_cat_display_options.keys())
        st.session_state.cat_filter_var = st.selectbox(
            "Filtrar por Categoria",
            filter_display_names,
            key="var_cat_filter_select",
            index=filter_display_names.index(st.session_state.cat_filter_var)
        )
        selected_category_id_filter = filter_cat_display_options.get(
            st.session_state.cat_filter_var)
    with filter_col2:
        st.session_state.search_var = st.text_input(
            "Filtrar por Nome", value=st.session_state.search_var, key="var_search_input")

    col1, col2 = st.columns([3, 1])

    current_page = st.session_state.page_var
    vars_list, total_pages, total_items = get_variables(
        category_id=selected_category_id_filter,
        search_term=st.session_state.search_var,
        page=current_page
    )

    with col1:
        st.write(f"Mostrando {len(vars_list)} de {total_items} variáveis.")
        if vars_list:
            for var_id, name, value, category_id, category_name in vars_list:
                if st.session_state.get("editing_var") != var_id:
                    st.session_state[f"confirm_delete_var_{var_id}"] = False
                if st.session_state.get("confirm_delete_var") != var_id:
                    st.session_state[f"editing_var_{var_id}"] = False

                exp_label = f"{name} (Valor: {value:.2f})"
                with st.expander(exp_label):
                    st.markdown(f"**Nome:** {name}")
                    st.markdown(f"**Valor:** {value:.2f}")
                    cat_display = f"Categoria: {category_name}" if category_name else "Sem Categoria"
                    st.caption(cat_display)

                    # Botões fora do form de edição
                    st.markdown(
                        "<div class=\"action-buttons-container\">", unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns([1, 10])
                    with btn_col1:
                        if not st.session_state.get(f"confirm_delete_var_{var_id}"):
                            if st.button("Editar", key=f"edit_var_{var_id}", help="Editar Variável"):
                                st.session_state.editing_var = var_id
                                st.session_state.confirm_delete_var = None
                                st.rerun()
                    with btn_col2:
                        if not st.session_state.get(f"editing_var_{var_id}"):
                            if st.button("Deletar", key=f"del_var_{var_id}", help="Deletar Variável"):
                                st.session_state.confirm_delete_var = var_id
                                st.session_state.editing_var = None
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.get("confirm_delete_var") == var_id:
                        st.warning(
                            f"Tem certeza que deseja deletar a variável \'{name}\'?")
                        confirm_cols = st.columns(2)
                        with confirm_cols[0]:
                            if st.button("Confirmar Exclusão", key=f"confirm_del_var_btn_{var_id}"):
                                if delete_variable(var_id):
                                    st.session_state.confirm_delete_var = None
                                    st.rerun()
                        with confirm_cols[1]:
                            if st.button("Cancelar Exclusão", key=f"cancel_del_var_btn_{var_id}", type="secondary"):
                                st.session_state.confirm_delete_var = None
                                st.rerun()

                # Formulário de Edição (v7 - Correção)
                if st.session_state.get("editing_var") == var_id:
                    with st.form(key=f"edit_var_form_{var_id}"):
                        st.markdown("**Editar Variável**")
                        new_name = st.text_input(
                            "Nome", value=name, key=f"name_var_{var_id}")
                        new_value = st.number_input(
                            "Valor", value=value, key=f"value_var_{var_id}", format="%.2f")
                        new_category_id = select_category(
                            "variable", category_id, key_prefix=f"edit_var_{var_id}")

                        edit_cols = st.columns(2)
                        with edit_cols[0]:
                            submitted_save = st.form_submit_button("Salvar")
                        with edit_cols[1]:
                            submitted_cancel = st.form_submit_button(
                                "Cancelar", type="secondary")

                        if submitted_save:
                            if update_variable(var_id, new_name, new_value, new_category_id):
                                st.session_state.editing_var = None
                                st.rerun()
                        if submitted_cancel:
                            st.session_state.editing_var = None
                            st.rerun()
            st.divider()
            new_page = pagination_component(total_pages, current_page, "var")
            if new_page != current_page:
                st.session_state.page_var = new_page
                st.rerun()

        else:
            st.info("Nenhuma variável encontrada com os filtros aplicados.")

    with col2:
        if "show_add_variable_form" not in st.session_state:
            st.session_state.show_add_variable_form = False

        button_label = "➖ Fechar Formulário" if st.session_state.show_add_variable_form else "➕ Criar Nova Variável"
        if st.button(button_label, use_container_width=True):
            st.session_state.show_add_variable_form = not st.session_state.show_add_variable_form
            st.session_state.editing_var = None
            st.session_state.confirm_delete_var = None
            st.rerun()

        if st.session_state.show_add_variable_form:
            with st.expander("Formulário Nova Variável", expanded=True):
                with st.form(key="new_variable_form"):
                    nv_name = st.text_input("Nome da Variável")
                    nv_value = st.number_input(
                        "Valor", format="%.2f", step=0.01)
                    nv_category_id = select_category(
                        "variable", key_prefix="new_var")

                    add_cols = st.columns([1, 1])
                    with add_cols[0]:
                        submitted_add = st.form_submit_button("Adicionar")
                    with add_cols[1]:
                        submitted_cancel_add = st.form_submit_button(
                            "Cancelar", type="secondary")

                    if submitted_add:
                        if nv_name and nv_value is not None:
                            if add_variable(nv_name, nv_value, nv_category_id):
                                st.session_state.show_add_variable_form = False
                                st.rerun()
                        else:
                            st.error("Informe nome e valor válidos.")
                    if submitted_cancel_add:
                        st.session_state.show_add_variable_form = False
                        st.rerun()


def show_products():
    st.subheader("Produtos e Fórmulas")

    if "page_prod" not in st.session_state:
        st.session_state.page_prod = 1
    if "search_prod" not in st.session_state:
        st.session_state.search_prod = ""
    if "cat_filter_prod" not in st.session_state:
        st.session_state.cat_filter_prod = "Todas"

    filter_col1, filter_col2 = st.columns([1, 2])
    with filter_col1:
        categories = get_categories("product")[0]
        category_options = {name: id for id, name in categories}
        filter_cat_display_options = {"Todas": "all", "Sem Categoria": "none"}
        filter_cat_display_options.update(category_options)
        filter_display_names = list(filter_cat_display_options.keys())
        st.session_state.cat_filter_prod = st.selectbox(
            "Filtrar por Categoria",
            filter_display_names,
            key="prod_cat_filter_select",
            index=filter_display_names.index(st.session_state.cat_filter_prod)
        )
        selected_category_id_filter = filter_cat_display_options.get(
            st.session_state.cat_filter_prod)
    with filter_col2:
        st.session_state.search_prod = st.text_input(
            "Filtrar por Nome", value=st.session_state.search_prod, key="prod_search_input")

    col1, col2 = st.columns([3, 1])

    current_page = st.session_state.page_prod
    prod_list, total_pages, total_items = get_products(
        category_id=selected_category_id_filter,
        search_term=st.session_state.search_prod,
        page=current_page
    )

    all_vars_list = get_variables(category_id="all", page=1)[0]
    var_names_values = {v[1]: v[2] for v in all_vars_list}

    with col1:
        st.write(f"Mostrando {len(prod_list)} de {total_items} produtos.")
        if prod_list:
            for prod_id, name, formula, category_id, category_name in prod_list:
                if st.session_state.get("editing_prod") != prod_id:
                    st.session_state[f"confirm_delete_prod_{prod_id}"] = False
                if st.session_state.get("confirm_delete_prod") != prod_id:
                    st.session_state[f"editing_prod_{prod_id}"] = False

                cost = calculate_cost(formula)
                label = f"{name} - R$ {cost:.2f}" if cost is not None else f"{name} - (Erro na fórmula)"
                with st.expander(label):
                    if cost is not None:
                        st.metric("Custo Atual", f"R$ {cost:.2f}")
                    else:
                        st.error(
                            "Erro ao calcular custo. Verifique a fórmula e se todas as variáveis existem e têm valor.")

                    # Fórmula/Valores com espaçamento reduzido (v7)
                    st.markdown("<div class=\"formula-section\">",
                                unsafe_allow_html=True)
                    st.markdown(f"**Fórmula:** `{formula}`")
                    formula_values_str = format_formula_values_string(formula)
                    st.markdown(f"**Valores:** `{formula_values_str}`")
                    st.markdown("</div>", unsafe_allow_html=True)

                    cat_display = f"Categoria: {category_name}" if category_name else "Sem Categoria"
                    st.caption(cat_display)

                    # Botões fora do form de edição
                    st.markdown(
                        "<div class=\"action-buttons-container\">", unsafe_allow_html=True)
                    btn_col1, btn_col2, _ = st.columns([1, 1, 8])
                    with btn_col1:
                        if not st.session_state.get(f"confirm_delete_prod_{prod_id}"):
                            if st.button("Editar", key=f"edit_prod_{prod_id}"):
                                st.session_state.editing_prod = prod_id
                                st.session_state.confirm_delete_prod = None
                                st.rerun()
                    with btn_col2:
                        if not st.session_state.get(f"editing_prod_{prod_id}"):
                            if st.button("Deletar", key=f"del_prod_{prod_id}"):
                                st.session_state.confirm_delete_prod = prod_id
                                st.session_state.editing_prod = None
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.get("confirm_delete_prod") == prod_id:
                        st.warning(
                            f"Tem certeza que deseja deletar o produto \'{name}\'?")
                        confirm_cols = st.columns(2)
                        with confirm_cols[0]:
                            if st.button("Confirmar Exclusão", key=f"confirm_del_prod_btn_{prod_id}"):
                                if delete_product(prod_id):
                                    st.session_state.confirm_delete_prod = None
                                    st.rerun()
                        with confirm_cols[1]:
                            if st.button("Cancelar Exclusão", key=f"cancel_del_prod_btn_{prod_id}", type="secondary"):
                                st.session_state.confirm_delete_prod = None
                                st.rerun()

                # Formulário de Edição (v7 - Correção botão)
                if st.session_state.get("editing_prod") == prod_id:
                    # Botão 'Ver Variáveis' fora do form
                    if st.button("Ver Variáveis Disponíveis", key=f"show_vars_edit_{prod_id}"):
                        # Toggle visibility
                        st.session_state[f"show_vars_popup_edit_{prod_id}"] = not st.session_state.get(
                            f"show_vars_popup_edit_{prod_id}", False)
                        st.rerun()

                    # Expander das variáveis (se visível)
                    if st.session_state.get(f"show_vars_popup_edit_{prod_id}"):
                        with st.expander("Variáveis Disponíveis", expanded=True):
                            if var_names_values:
                                st.table(var_names_values)
                            else:
                                st.info("Nenhuma variável cadastrada.")
                            # Não precisa de botão fechar, clicar no botão principal de novo fecha

                    # Formulário de edição em si
                    with st.form(key=f"edit_prod_form_{prod_id}"):
                        st.markdown("**Editar Produto**")
                        new_name = st.text_input(
                            "Nome", value=name, key=f"name_prod_{prod_id}")
                        new_category_id = select_category(
                            "product", category_id, key_prefix=f"edit_prod_{prod_id}")
                        new_formula = st.text_area(
                            "Fórmula", value=formula, key=f"formula_prod_{prod_id}", help="Use os nomes das variáveis cadastradas. Ex: var1 * 2 + var2")

                        edit_cols = st.columns([1, 1])
                        with edit_cols[0]:
                            submitted_save = st.form_submit_button("Salvar")
                        with edit_cols[1]:
                            submitted_cancel = st.form_submit_button(
                                "Cancelar", type="secondary")

                        if submitted_save:
                            if update_product(prod_id, new_name, new_formula, new_category_id):
                                st.session_state.editing_prod = None
                                # Fechar popup ao salvar
                                st.session_state[f"show_vars_popup_edit_{prod_id}"] = False
                                st.rerun()
                        if submitted_cancel:
                            st.session_state.editing_prod = None
                            # Fechar popup ao cancelar
                            st.session_state[f"show_vars_popup_edit_{prod_id}"] = False
                            st.rerun()
            st.divider()
            new_page = pagination_component(total_pages, current_page, "prod")
            if new_page != current_page:
                st.session_state.page_prod = new_page
                st.rerun()
        else:
            st.info("Nenhum produto encontrado com os filtros aplicados.")

    with col2:
        if "show_add_product_form" not in st.session_state:
            st.session_state.show_add_product_form = False

        button_label = "➖ Fechar Formulário" if st.session_state.show_add_product_form else "➕ Criar Novo Produto"
        if st.button(button_label, use_container_width=True):
            st.session_state.show_add_product_form = not st.session_state.show_add_product_form
            st.session_state.editing_prod = None
            st.session_state.confirm_delete_prod = None
            st.session_state.show_vars_popup_new = False  # Garantir que popup feche
            st.rerun()

        if st.session_state.show_add_product_form:
            with st.expander("Formulário Novo Produto", expanded=True):
                # Botão 'Ver Variáveis' fora do form
                if st.button("Ver Variáveis Disponíveis", key="show_vars_new"):
                    st.session_state.show_vars_popup_new = not st.session_state.get(
                        "show_vars_popup_new", False)
                    st.rerun()

                # Expander das variáveis (se visível)
                if st.session_state.get("show_vars_popup_new"):
                    with st.expander("Variáveis Disponíveis", expanded=True):
                        if var_names_values:
                            st.table(var_names_values)
                        else:
                            st.info("Nenhuma variável cadastrada.")

                # Formulário de adição
                with st.form(key="new_product_form"):
                    np_name = st.text_input("Nome do Produto")
                    np_category_id = select_category(
                        "product", key_prefix="new_prod")
                    np_formula = st.text_area(
                        "Fórmula", help="Use os nomes das variáveis cadastradas. Ex: var1 * 2 + var2")

                    add_cols = st.columns([1, 1])
                    with add_cols[0]:
                        submitted_add = st.form_submit_button("Adicionar")
                    with add_cols[1]:
                        submitted_cancel_add = st.form_submit_button(
                            "Cancelar", type="secondary")

                    if submitted_add:
                        if np_name and np_formula:
                            if add_product(np_name, np_formula, np_category_id):
                                st.session_state.show_add_product_form = False
                                st.session_state.show_vars_popup_new = False
                                st.rerun()
                        else:
                            st.error("Informe nome e fórmula válidos.")
                    if submitted_cancel_add:
                        st.session_state.show_add_product_form = False
                        st.session_state.show_vars_popup_new = False
                        st.rerun()


def main():
    init_db()

    if "show_add_product_form" not in st.session_state:
        st.session_state.show_add_product_form = False
    if "show_add_variable_form" not in st.session_state:
        st.session_state.show_add_variable_form = False
    if "editing_var" not in st.session_state:
        st.session_state.editing_var = None
    if "editing_prod" not in st.session_state:
        st.session_state.editing_prod = None
    if "confirm_delete_var" not in st.session_state:
        st.session_state.confirm_delete_var = None
    if "confirm_delete_prod" not in st.session_state:
        st.session_state.confirm_delete_prod = None

    keys_to_clear_cat = [k for k in st.session_state if k.startswith(
        "editing_cat_") or k.startswith("confirm_delete_cat_")]
    for key in keys_to_clear_cat:
        if key in st.session_state:
            del st.session_state[key]

    keys_to_clear_vars_popup = [
        k for k in st.session_state if k.startswith("show_vars_popup_")]
    for key in keys_to_clear_vars_popup:
        if key in st.session_state:
            del st.session_state[key]

    st.sidebar.markdown(
        "<p class=\"st-emotion-cache-10oheav\">Navegação</p>", unsafe_allow_html=True)

    menu_options = ["Custos de Produção", "Calculadora de Preços"]
    menu = st.sidebar.radio(
        "",
        menu_options,
        key="main_menu"
    )

    if menu == "Custos de Produção":
        show_production_costs()
    elif menu == "Calculadora de Preços":
        show_price_calculator()


if __name__ == "__main__":
    main()

# test
