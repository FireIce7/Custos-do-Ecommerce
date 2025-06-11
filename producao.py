import streamlit as st
import sqlite3
import re
import math
from textos import TEXTOS
from banco import get_connection

ITEMS_PER_PAGE = 10

# --- Funções CRUD para Categorias (Adaptadas de mainANTIGO.py) ---


def add_category(name):
    conn = get_connection()
    c = conn.cursor()
    category_id = None
    try:
        # Nota: A tabela 'categorias' em banco.py não tem 'type'. Assumindo categorias genéricas.
        c.execute("INSERT INTO categorias (nome) VALUES (?)", (name,))
        conn.commit()
        category_id = c.lastrowid
        st.success(f"Categoria '{name}' adicionada.")
    except sqlite3.IntegrityError:
        st.error(f"Categoria '{name}' já existe.")
    except Exception as e:
        st.error(f"Erro ao adicionar categoria: {e}")
    finally:
        conn.close()
    return category_id


def get_categories(search_term="", page=1):
    conn = get_connection()
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE
    # Nota: Adaptado para tabela 'categorias' sem 'type'.
    base_query = "FROM categorias"
    params = []
    where_clauses = []

    if search_term:
        where_clauses.append("nome LIKE ?")
        params.append(f"%{search_term}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(*) {base_query}"
    total_items = c.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    data_query = f"SELECT id, nome {base_query} ORDER BY nome LIMIT ? OFFSET ?"
    params.extend([ITEMS_PER_PAGE, offset])
    rows = c.execute(data_query, params).fetchall()

    conn.close()
    return rows, total_pages, total_items


def update_category(category_id, new_name):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        c.execute("UPDATE categorias SET nome = ? WHERE id = ?",
                  (new_name, category_id))
        conn.commit()
        st.success("Categoria atualizada.")
        success = True
    except sqlite3.IntegrityError:
        st.error(f"Já existe uma categoria com o nome '{new_name}'.")
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
        # Verificar se a categoria está em uso antes de deletar
        in_use_var = c.execute(
            "SELECT 1 FROM variaveis_custos WHERE categoria_id = ? LIMIT 1", (category_id,)).fetchone()
        in_use_prod = c.execute(
            "SELECT 1 FROM produtos WHERE categoria_id = ? LIMIT 1", (category_id,)).fetchone()
        if in_use_var or in_use_prod:
            st.error(
                "Erro: Categoria está associada a variáveis ou produtos e não pode ser deletada.")
            return False

        c.execute("DELETE FROM categorias WHERE id = ?", (category_id,))
        conn.commit()
        st.success("Categoria deletada.")
        success = True
    except Exception as e:
        st.error(f"Erro ao deletar categoria: {e}")
    finally:
        conn.close()
    return success

# --- Funções CRUD para Variáveis de Custos (Adaptadas de mainANTIGO.py) ---


def get_variables(category_id=None, search_term="", page=1):
    conn = get_connection()
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE

    # Nota: Adaptado para tabela 'variaveis_custos' e 'categorias'.
    base_query = "FROM variaveis_custos v LEFT JOIN categorias c ON v.categoria_id = c.id"
    where_clauses = []
    params = []

    if category_id == "all":
        pass  # Sem filtro de categoria
    elif category_id == "none":
        where_clauses.append("v.categoria_id IS NULL")
    elif category_id is not None:
        where_clauses.append("v.categoria_id = ?")
        params.append(category_id)

    if search_term:
        where_clauses.append("v.nome LIKE ?")  # Corrigido para 'nome'
        params.append(f"%{search_term}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(v.id) {base_query}"
    total_items = c.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    # Corrigido para 'nome', 'valor', 'categoria_id'
    data_query = f"SELECT v.id, v.nome, v.valor, v.categoria_id, c.nome as category_name {base_query} ORDER BY v.nome LIMIT ? OFFSET ?"
    params.extend([ITEMS_PER_PAGE, offset])
    rows = c.execute(data_query, params).fetchall()

    conn.close()
    return rows, total_pages, total_items


def add_variable(name, value, category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        # Nota: Adaptado para tabela 'variaveis_custos'.
        c.execute("INSERT INTO variaveis_custos (nome, valor, categoria_id) VALUES (?, ?, ?)",
                  (name, value, category_id))
        conn.commit()
        st.success(f"Variável '{name}' adicionada.")
        success = True
    except sqlite3.IntegrityError as e:
        # A tabela permite nomes duplicados, verificar erro específico se necessário
        st.error(f"Erro de integridade ao adicionar variável: {e}")
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
        # Nota: Adaptado para tabela 'variaveis_custos'.
        c.execute("UPDATE variaveis_custos SET nome = ?, valor = ?, categoria_id = ? WHERE id = ?",
                  (name, value, category_id, var_id))
        conn.commit()
        st.success("Variável atualizada.")
        success = True
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
        # Nota: Adaptado para tabela 'variaveis_custos'.
        c.execute("DELETE FROM variaveis_custos WHERE id = ?", (var_id,))
        conn.commit()
        st.success("Variável deletada.")
        success = True
    except Exception as e:
        st.error(f"Erro ao deletar variável: {e}")
    finally:
        conn.close()
    return success

# --- Funções CRUD para Produtos (Adaptadas de mainANTIGO.py) ---


def get_products(category_id=None, search_term="", page=1):
    conn = get_connection()
    c = conn.cursor()
    offset = (page - 1) * ITEMS_PER_PAGE

    # Nota: Adaptado para tabela 'produtos' e 'categorias'.
    base_query = "FROM produtos p LEFT JOIN categorias c ON p.categoria_id = c.id"
    where_clauses = []
    params = []

    if category_id == "all":
        pass  # Sem filtro
    elif category_id == "none":
        where_clauses.append("p.categoria_id IS NULL")
    elif category_id is not None:
        where_clauses.append("p.categoria_id = ?")
        params.append(category_id)

    if search_term:
        where_clauses.append("p.nome LIKE ?")  # Corrigido para 'nome'
        params.append(f"%{search_term}%")

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    count_query = f"SELECT COUNT(p.id) {base_query}"
    total_items = c.execute(count_query, params).fetchone()[0]
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)

    # Corrigido para 'nome', 'formula', 'categoria_id'
    data_query = f"SELECT p.id, p.nome, p.formula, p.categoria_id, c.nome as category_name {base_query} ORDER BY p.nome LIMIT ? OFFSET ?"
    params.extend([ITEMS_PER_PAGE, offset])
    rows = c.execute(data_query, params).fetchall()

    conn.close()
    return rows, total_pages, total_items


def add_product(name, formula, category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    try:
        # Nota: Adaptado para tabela 'produtos'.
        c.execute("INSERT INTO produtos (nome, formula, categoria_id) VALUES (?, ?, ?)",
                  (name, formula, category_id))
        conn.commit()
        st.success(f"Produto '{name}' adicionado.")
        success = True
    except sqlite3.IntegrityError as e:
        # A tabela permite nomes duplicados, verificar erro específico se necessário
        st.error(f"Erro de integridade ao adicionar produto: {e}")
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
        # Nota: Adaptado para tabela 'produtos'.
        c.execute("UPDATE produtos SET nome = ?, formula = ?, categoria_id = ? WHERE id = ?",
                  (name, formula, category_id, prod_id))
        conn.commit()
        st.success("Produto atualizado.")
        success = True
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
        # Nota: Adaptado para tabela 'produtos'.
        c.execute("DELETE FROM produtos WHERE id = ?", (prod_id,))
        conn.commit()
        st.success("Produto deletado.")
        success = True
    except Exception as e:
        st.error(f"Erro ao deletar produto: {e}")
    finally:
        conn.close()
    return success

# --- Cálculo de custo (Adaptado de mainANTIGO.py) ---


def get_variable_values():
    conn = get_connection()
    c = conn.cursor()
    # Nota: Adaptado para buscar da tabela 'variaveis_custos'.
    rows = c.execute("SELECT nome, valor FROM variaveis_custos").fetchall()
    conn.close()
    # Considerar variáveis da calculadora também? Por ora, apenas custos.
    # Se necessário, buscar de 'production_variables' e mesclar.
    return {name: val for name, val in rows}


def calculate_cost(formula):
    if not formula:
        return 0.0  # Retorna 0 se a fórmula for vazia
    var_values = get_variable_values()
    try:
        # Validar nomes de variáveis na fórmula
        variable_names_in_formula = set(
            re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", formula))
        defined_vars = set(var_values.keys())
        missing_vars = variable_names_in_formula - defined_vars

        if missing_vars:
            st.warning(
                f"Variáveis não definidas na fórmula: {', '.join(missing_vars)}")
            # Tentar calcular mesmo assim pode dar erro ou resultado incorreto.
            # Poderia retornar None ou um erro mais explícito.
            # Por segurança, vamos tentar avaliar, mas pode falhar.
            pass  # Continua para eval, que provavelmente falhará

        # Usar um ambiente seguro para eval
        safe_globals = {"__builtins__": {"min": min,
                                         "max": max, "abs": abs, "pow": pow, "round": round}}
        cost = eval(formula, safe_globals, var_values)
        # Retorna 0 se o resultado não for numérico
        return cost if isinstance(cost, (int, float)) else 0.0
    except NameError as e:
        st.error(
            f"Erro ao calcular custo: Variável não definida na fórmula ou nas variáveis de custo ({e}). Verifique a fórmula e as variáveis cadastradas.")
        return None  # Indica erro
    except SyntaxError:
        st.error(
            f"Erro de sintaxe na fórmula: '{formula}'. Verifique a formatação.")
        return None  # Indica erro
    except Exception as e:
        st.error(
            f"Erro inesperado ao calcular custo para fórmula '{formula}': {e}")
        return None  # Indica erro

# --- Função de Formatação de Fórmula (Adaptada de mainANTIGO.py) ---


def format_formula_values_string(formula):
    if not formula:
        return ""
    var_values = get_variable_values()
    value_formula = formula
    try:
        # Ordenar por comprimento descendente para evitar substituições parciais (ex: 'var' antes de 'var_longa')
        for name in sorted(var_values.keys(), key=len, reverse=True):
            value = var_values.get(name)
            if value is None:
                continue  # Pula variáveis sem valor

            # Formatar valor numérico
            if isinstance(value, (int, float)):
                # Sempre duas casas decimais para consistência
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)  # Caso não numérico (improvável aqui)

            # Substituir variável pelo valor (garantindo que seja uma palavra completa)
            value_formula = re.sub(
                r"\b" + re.escape(name) + r"\b", value_str, value_formula)

        # Remover espaços extras ao redor de operadores para compactar
        value_formula_compact = re.sub(
            r"\s*([+\-*/()])\s*", r"\1", value_formula)
        return value_formula_compact
    except Exception as e:
        # st.warning(f"Erro ao formatar fórmula '{formula}': {e}") # Log discreto
        return formula  # Retorna a fórmula original em caso de erro

# --- Componente de Paginação (Adaptado de mainANTIGO.py) ---


def pagination_component(total_pages, current_page, key_suffix):
    if total_pages <= 1:
        return current_page

    st.markdown("<div class='pagination-container'>", unsafe_allow_html=True)
    # Usar 5 colunas para centralizar melhor os botões e a informação
    cols = st.columns([1, 1, 3, 1, 1])

    with cols[0]:
        if st.button("◀️◀️", key=f"first_{key_suffix}", disabled=(current_page == 1), use_container_width=True):
            return 1
    with cols[1]:
        if st.button("◀️", key=f"prev_{key_suffix}", disabled=(current_page == 1), use_container_width=True):
            return current_page - 1
    with cols[2]:
        st.write(f"Página {current_page} de {total_pages}")
    with cols[3]:
        if st.button("▶️", key=f"next_{key_suffix}", disabled=(current_page == total_pages), use_container_width=True):
            return current_page + 1
    with cols[4]:
        if st.button("▶️▶️", key=f"last_{key_suffix}", disabled=(current_page == total_pages), use_container_width=True):
            return total_pages

    st.markdown("</div>", unsafe_allow_html=True)
    return current_page

# --- Funções de Interface (Adaptadas de mainANTIGO.py) ---


def show_products():
    st.subheader(TEXTOS["prod_produtos"])

    # Estado da sessão para paginação e edição
    if 'prod_page' not in st.session_state:
        st.session_state.prod_page = 1
    if 'editing_prod_id' not in st.session_state:
        st.session_state.editing_prod_id = None
    if 'show_prod_form' not in st.session_state:
        st.session_state.show_prod_form = False

    # Filtros e Adição
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search_term = st.text_input("Buscar Produto", key="prod_search")
    with col2:
        categorias_list, _, _ = get_categories()  # Buscar todas para o selectbox
        categoria_opts = {cat[1]: cat[0] for cat in categorias_list}
        categoria_opts_display = {"Todos": "all",
                                  "Sem Categoria": "none", **categoria_opts}
        selected_category_name = st.selectbox("Filtrar por Categoria", options=list(
            categoria_opts_display.keys()), key="prod_cat_filter")
        category_id_filter = categoria_opts_display[selected_category_name]
    with col3:
        st.write("&nbsp;")  # Espaçamento
        # Modificado para alternar o estado do formulário
        btn_label = "➕ Adicionar Produto" if not st.session_state.show_prod_form else "❌ Fechar Formulário"
        if st.button(btn_label, key="add_prod_btn", use_container_width=True):
            # Toggle do estado do formulário
            st.session_state.show_prod_form = not st.session_state.show_prod_form
            if st.session_state.show_prod_form:
                st.session_state.editing_prod_id = 'new'
            else:
                st.session_state.editing_prod_id = None
            st.rerun()

    # Formulário de Adição/Edição (dentro de um expander ou modal simulado)
    if st.session_state.editing_prod_id:
        with st.container(border=True):
            st.markdown(
                "<h3 style='text-align: center;'>Adicionar/Editar Produto</h3>", unsafe_allow_html=True)
            is_new = st.session_state.editing_prod_id == 'new'
            prod_data = None
            if not is_new:
                # Buscar dados do produto para edição
                conn = get_connection()
                prod_data = conn.execute("SELECT nome, formula, categoria_id FROM produtos WHERE id = ?", (
                    st.session_state.editing_prod_id,)).fetchone()
                conn.close()
                if not prod_data:
                    st.error("Produto não encontrado.")
                    st.session_state.editing_prod_id = None
                    st.session_state.show_prod_form = False
                    st.rerun()

            default_name = prod_data[0] if prod_data else ""
            default_formula = prod_data[1] if prod_data else ""
            default_cat_id = prod_data[2] if prod_data else None

            # Mapear ID da categoria para nome para o selectbox
            cat_id_to_name = {cat[0]: cat[1] for cat in categorias_list}
            cat_options_list = ["(Nenhuma)"] + list(cat_id_to_name.values())
            default_cat_index = 0
            if default_cat_id and default_cat_id in cat_id_to_name:
                try:
                    default_cat_index = cat_options_list.index(
                        cat_id_to_name[default_cat_id])
                except ValueError:
                    default_cat_index = 0  # Categoria não encontrada na lista atual

            with st.form(key="prod_edit_form"):
                new_name = st.text_input("Nome do Produto", value=default_name)
                new_formula = st.text_area(
                    "Fórmula", value=default_formula, help="Use nomes das variáveis de custo. Ex: var1 * 2 + var2 / (var3 - 5)")
                selected_cat_name_form = st.selectbox(
                    "Categoria", options=cat_options_list, index=default_cat_index)

                # Centralizar botões do formulário
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submitted = st.form_submit_button(
                        "Salvar", use_container_width=True)

                if submitted:
                    # Obter ID da categoria selecionada
                    new_cat_id = None
                    if selected_cat_name_form != "(Nenhuma)":
                        # Inverter o mapeamento para encontrar o ID pelo nome
                        name_to_cat_id = {v: k for k,
                                          v in cat_id_to_name.items()}
                        new_cat_id = name_to_cat_id.get(selected_cat_name_form)

                    if not new_name:
                        st.warning("Nome do produto é obrigatório.")
                    else:
                        success = False
                        if is_new:
                            success = add_product(
                                new_name, new_formula, new_cat_id)
                        else:
                            success = update_product(
                                st.session_state.editing_prod_id, new_name, new_formula, new_cat_id)

                        if success:
                            st.session_state.editing_prod_id = None
                            st.session_state.show_prod_form = False
                            st.rerun()

            # Botão Cancelar fora do formulário mas centralizado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Cancelar", key="cancel_prod_edit", use_container_width=True):
                    st.session_state.editing_prod_id = None
                    st.session_state.show_prod_form = False
                    st.rerun()

    # Listagem de Produtos
    st.markdown("--- ")
    products, total_pages, total_items = get_products(
        category_id=category_id_filter, search_term=search_term, page=st.session_state.prod_page)

    if not products and total_items > 0 and st.session_state.prod_page > 1:
        # Se a página atual ficou vazia (ex: após deletar último item), volte para a página anterior
        st.session_state.prod_page -= 1
        st.rerun()

    if not products and st.session_state.editing_prod_id is None:
        st.info("Nenhum produto encontrado." if not search_term and category_id_filter ==
                'all' else "Nenhum produto encontrado com os filtros aplicados.")
    else:
        st.write(f"Total de Produtos: {total_items}")
        for prod_id, name, formula, cat_id, cat_name in products:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Aumentar tamanho da fonte para o nome do produto
                    st.markdown(
                        f"<h3 style='margin-bottom: 0px;'>{name}</h3>", unsafe_allow_html=True)
                    if cat_name:
                        st.caption(f"Categoria: {cat_name}")
                    else:
                        st.caption("Categoria: Nenhuma")

                    cost = calculate_cost(formula)
                    cost_str = f"R$ {cost:.2f}" if cost is not None else "Erro no cálculo"
                    st.metric("Custo Calculado", cost_str)

                    with st.expander("Ver Fórmula"):
                        st.code(
                            formula if formula else "(Fórmula não definida)", language="")
                        if formula:
                            formatted_formula = format_formula_values_string(
                                formula)
                            st.write("**Fórmula com Valores:**")
                            st.code(formatted_formula, language="")

                with col2:
                    st.write("&nbsp;")  # Espaçamento
                    st.write("&nbsp;")
                    if st.button("✏️ Editar", key=f"edit_prod_{prod_id}", use_container_width=True):
                        st.session_state.editing_prod_id = prod_id
                        st.session_state.show_prod_form = True
                        st.rerun()
                    if st.button("🗑️ Deletar", key=f"del_prod_{prod_id}", type="primary", use_container_width=True):
                        if delete_product(prod_id):
                            # Resetar página se necessário após deleção
                            new_total_items = total_items - 1
                            new_total_pages = math.ceil(
                                new_total_items / ITEMS_PER_PAGE)
                            if st.session_state.prod_page > new_total_pages and new_total_pages > 0:
                                st.session_state.prod_page = new_total_pages
                            st.rerun()

    # Paginação
    if total_pages > 1:
        new_page = pagination_component(
            total_pages, st.session_state.prod_page, "prod")
        if new_page != st.session_state.prod_page:
            st.session_state.prod_page = new_page
            st.rerun()


def show_variables():
    st.subheader(TEXTOS["prod_variaveis"])

    # Estado da sessão
    if 'var_page' not in st.session_state:
        st.session_state.var_page = 1
    if 'editing_var_id' not in st.session_state:
        st.session_state.editing_var_id = None
    if 'show_var_form' not in st.session_state:
        st.session_state.show_var_form = False

    # Filtros e Adição
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        search_term = st.text_input("Buscar Variável", key="var_search")
    with col2:
        categorias_list, _, _ = get_categories()
        categoria_opts = {cat[1]: cat[0] for cat in categorias_list}
        categoria_opts_display = {"Todas": "all",
                                  "Sem Categoria": "none", **categoria_opts}
        selected_category_name = st.selectbox("Filtrar por Categoria", options=list(
            categoria_opts_display.keys()), key="var_cat_filter")
        category_id_filter = categoria_opts_display[selected_category_name]
    with col3:
        st.write("&nbsp;")
        # Modificado para alternar o estado do formulário
        btn_label = "➕ Adicionar Variável" if not st.session_state.show_var_form else "❌ Fechar Formulário"
        if st.button(btn_label, key="add_var_btn", use_container_width=True):
            # Toggle do estado do formulário
            st.session_state.show_var_form = not st.session_state.show_var_form
            if st.session_state.show_var_form:
                st.session_state.editing_var_id = 'new'
            else:
                st.session_state.editing_var_id = None
            st.rerun()

    # Formulário de Adição/Edição
    if st.session_state.editing_var_id:
        with st.container(border=True):
            st.markdown(
                "<h3 style='text-align: center;'>Adicionar/Editar Variável</h3>", unsafe_allow_html=True)
            is_new = st.session_state.editing_var_id == 'new'
            var_data = None
            if not is_new:
                conn = get_connection()
                var_data = conn.execute("SELECT nome, valor, categoria_id FROM variaveis_custos WHERE id = ?", (
                    st.session_state.editing_var_id,)).fetchone()
                conn.close()
                if not var_data:
                    st.error("Variável não encontrada.")
                    st.session_state.editing_var_id = None
                    st.session_state.show_var_form = False
                    st.rerun()

            default_name = var_data[0] if var_data else ""
            default_value = var_data[1] if var_data else 0.0
            default_cat_id = var_data[2] if var_data else None

            cat_id_to_name = {cat[0]: cat[1] for cat in categorias_list}
            cat_options_list = ["(Nenhuma)"] + list(cat_id_to_name.values())
            default_cat_index = 0
            if default_cat_id and default_cat_id in cat_id_to_name:
                try:
                    default_cat_index = cat_options_list.index(
                        cat_id_to_name[default_cat_id])
                except ValueError:
                    default_cat_index = 0

            with st.form(key="var_edit_form"):
                new_name = st.text_input(
                    "Nome da Variável", value=default_name)
                new_value = st.number_input(
                    "Valor", value=default_value, format="%.2f")
                selected_cat_name_form = st.selectbox(
                    "Categoria", options=cat_options_list, index=default_cat_index)

                # Centralizar botões do formulário
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submitted = st.form_submit_button(
                        "Salvar", use_container_width=True)

                if submitted:
                    new_cat_id = None
                    if selected_cat_name_form != "(Nenhuma)":
                        name_to_cat_id = {v: k for k,
                                          v in cat_id_to_name.items()}
                        new_cat_id = name_to_cat_id.get(selected_cat_name_form)

                    if not new_name:
                        st.warning("Nome da variável é obrigatório.")
                    else:
                        success = False
                        if is_new:
                            success = add_variable(
                                new_name, new_value, new_cat_id)
                        else:
                            success = update_variable(
                                st.session_state.editing_var_id, new_name, new_value, new_cat_id)

                        if success:
                            st.session_state.editing_var_id = None
                            st.session_state.show_var_form = False
                            st.rerun()

            # Botão Cancelar fora do formulário mas centralizado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Cancelar", key="cancel_var_edit", use_container_width=True):
                    st.session_state.editing_var_id = None
                    st.session_state.show_var_form = False
                    st.rerun()

    # Listagem de Variáveis
    st.markdown("--- ")
    variables, total_pages, total_items = get_variables(
        category_id=category_id_filter, search_term=search_term, page=st.session_state.var_page)

    if not variables and total_items > 0 and st.session_state.var_page > 1:
        st.session_state.var_page -= 1
        st.rerun()

    if not variables and st.session_state.editing_var_id is None:
        st.info("Nenhuma variável encontrada." if not search_term and category_id_filter ==
                'all' else "Nenhuma variável encontrada com os filtros aplicados.")
    else:
        st.write(f"Total de Variáveis: {total_items}")
        for var_id, name, value, cat_id, cat_name in variables:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    # Aumentar tamanho da fonte para o nome da variável
                    st.markdown(
                        f"<h3 style='margin-bottom: 0px;'>{name}</h3>", unsafe_allow_html=True)
                    if cat_name:
                        st.caption(f"Categoria: {cat_name}")
                    else:
                        st.caption("Categoria: Nenhuma")
                with col2:
                    st.metric("Valor Atual", f"{value:.2f}")
                with col3:
                    st.write("&nbsp;")  # Espaçamento
                    if st.button("✏️ Editar", key=f"edit_var_{var_id}", use_container_width=True):
                        st.session_state.editing_var_id = var_id
                        st.session_state.show_var_form = True
                        st.rerun()
                    if st.button("🗑️ Deletar", key=f"del_var_{var_id}", type="primary", use_container_width=True):
                        if delete_variable(var_id):
                            new_total_items = total_items - 1
                            new_total_pages = math.ceil(
                                new_total_items / ITEMS_PER_PAGE)
                            if st.session_state.var_page > new_total_pages and new_total_pages > 0:
                                st.session_state.var_page = new_total_pages
                            st.rerun()

    # Paginação
    if total_pages > 1:
        new_page = pagination_component(
            total_pages, st.session_state.var_page, "var")
        if new_page != st.session_state.var_page:
            st.session_state.var_page = new_page
            st.rerun()


def show_categories():
    st.subheader("Gerenciar Categorias")

    # Estado da sessão
    if 'cat_page' not in st.session_state:
        st.session_state.cat_page = 1
    if 'editing_cat_id' not in st.session_state:
        st.session_state.editing_cat_id = None
    if 'show_cat_form' not in st.session_state:
        st.session_state.show_cat_form = False

    # Filtro e Adição
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Buscar Categoria", key="cat_search")
    with col2:
        st.write("&nbsp;")
        # Modificado para alternar o estado do formulário
        btn_label = "➕ Adicionar Categoria" if not st.session_state.show_cat_form else "❌ Fechar Formulário"
        if st.button(btn_label, key="add_cat_btn", use_container_width=True):
            # Toggle do estado do formulário
            st.session_state.show_cat_form = not st.session_state.show_cat_form
            if st.session_state.show_cat_form:
                st.session_state.editing_cat_id = 'new'
            else:
                st.session_state.editing_cat_id = None
            st.rerun()

    # Formulário de Adição/Edição
    if st.session_state.editing_cat_id:
        with st.container(border=True):
            st.markdown(
                "<h3 style='text-align: center;'>Adicionar/Editar Categoria</h3>", unsafe_allow_html=True)
            is_new = st.session_state.editing_cat_id == 'new'
            cat_data = None
            if not is_new:
                conn = get_connection()
                cat_data = conn.execute(
                    "SELECT nome FROM categorias WHERE id = ?", (st.session_state.editing_cat_id,)).fetchone()
                conn.close()
                if not cat_data:
                    st.error("Categoria não encontrada.")
                    st.session_state.editing_cat_id = None
                    st.session_state.show_cat_form = False
                    st.rerun()

            default_name = cat_data[0] if cat_data else ""

            with st.form(key="cat_edit_form"):
                new_name = st.text_input(
                    "Nome da Categoria", value=default_name)

                # Centralizar botões do formulário
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submitted = st.form_submit_button(
                        "Salvar", use_container_width=True)

                if submitted:
                    if not new_name:
                        st.warning("Nome da categoria é obrigatório.")
                    else:
                        success = False
                        if is_new:
                            success = bool(add_category(new_name))
                        else:
                            success = update_category(
                                st.session_state.editing_cat_id, new_name)

                        if success:
                            st.session_state.editing_cat_id = None
                            st.session_state.show_cat_form = False
                            st.rerun()

            # Botão Cancelar fora do formulário mas centralizado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Cancelar", key="cancel_cat_edit", use_container_width=True):
                    st.session_state.editing_cat_id = None
                    st.session_state.show_cat_form = False
                    st.rerun()

    # Listagem de Categorias
    st.markdown("--- ")
    categories, total_pages, total_items = get_categories(
        search_term=search_term, page=st.session_state.cat_page)

    if not categories and total_items > 0 and st.session_state.cat_page > 1:
        st.session_state.cat_page -= 1
        st.rerun()

    if not categories and st.session_state.editing_cat_id is None:
        st.info("Nenhuma categoria encontrada." if not search_term else
                "Nenhuma categoria encontrada com o filtro aplicado.")
    else:
        st.write(f"Total de Categorias: {total_items}")
        for cat_id, name in categories:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Aumentar tamanho da fonte para o nome da categoria
                    st.markdown(
                        f"<h3 style='margin-bottom: 0px;'>{name}</h3>", unsafe_allow_html=True)
                with col2:
                    # Agrupar botões de editar e deletar mais próximos
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️", key=f"edit_cat_{cat_id}", use_container_width=True):
                            st.session_state.editing_cat_id = cat_id
                            st.session_state.show_cat_form = True
                            st.rerun()
                    with btn_col2:
                        if st.button("🗑️", key=f"del_cat_{cat_id}", type="primary", use_container_width=True):
                            if delete_category(cat_id):
                                new_total_items = total_items - 1
                                new_total_pages = math.ceil(
                                    new_total_items / ITEMS_PER_PAGE)
                                if st.session_state.cat_page > new_total_pages and new_total_pages > 0:
                                    st.session_state.cat_page = new_total_pages
                                st.rerun()

    # Paginação
    if total_pages > 1:
        new_page = pagination_component(
            total_pages, st.session_state.cat_page, "cat")
        if new_page != st.session_state.cat_page:
            st.session_state.cat_page = new_page
            st.rerun()

# --- Função Principal da Seção --- #


def show_production_costs():
    st.subheader(TEXTOS["prod_titulo"])
    # Usar label explícito e ocultá-lo se necessário para acessibilidade
    menu = st.radio(
        TEXTOS["prod_menu_titulo"],  # Label
        TEXTOS["prod_menu_opcoes"],
        horizontal=True,
        key="prod_menu_radio",
        # Oculta o label visualmente, mas mantém para leitores de tela
        label_visibility="collapsed"
    )

    if menu == "Produtos":
        show_products()
    elif menu == "Variáveis de Custos":
        show_variables()
    elif menu == "Gerenciar Categorias":
        show_categories()

# Adicionar CSS personalizado para melhorar a aparência


def add_custom_css():
    st.markdown("""
    <style>
    /* Melhorar espaçamento e alinhamento dos botões */
    div.stButton > button {
        font-weight: bold;
        border-radius: 4px;
        height: 2.5em;
        margin-top: 0.5em;
    }
    
    /* Centralizar texto nos botões */
    div.stButton > button p {
        text-align: center;
        width: 100%;
        margin: 0;
        padding: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* Melhorar aparência dos containers */
    div[data-testid="stExpander"] {
        border-radius: 4px;
    }
    
    /* Ajustar tamanho de fonte para títulos */
    h3 {
        font-size: 1.5em !important;
    }
    
    /* Melhorar espaçamento da paginação */
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 1em 0;
    }
    </style>
    """, unsafe_allow_html=True)
