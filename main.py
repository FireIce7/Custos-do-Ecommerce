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
        font-size: 26px !important;
        font-weight: bold;
        margin-bottom: 10px;
    }

    /* Itens do menu na Sidebar */
    .st-emotion-cache-16idsys p, .st-emotion-cache-16idsys span {
        font-size: 20px !important;
    }

    /* Título do Expander do Produto/Variável */
    .st-emotion-cache-1avcm0n span {
        font-size: 26px !important;
        font-weight: bold;
    }

    /* Nome da Categoria na listagem */
    .category-list-item {
        font-size: 20px !important;
        margin-left: 5px;
    }

    /* Valor da Métrica (Custo Atual) */
    .st-emotion-cache-1g6goon div {
        font-size: 26px !important;
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
    error_message = None
    try:
        c.execute("SELECT type FROM categories WHERE id = ?", (category_id,))
        result = c.fetchone()
        if not result:
            error_message = "Categoria não encontrada."
        else:
            category_type = result[0]
            # Verificar se já existe outra categoria com o mesmo nome e tipo
            c.execute("SELECT id FROM categories WHERE name = ? AND type = ? AND id != ?",
                      (new_name, category_type, category_id))
            existing = c.fetchone()
            if existing:
                error_message = f"Já existe uma categoria com o nome \'{new_name}\' para o tipo \'{category_type}\'."
            else:
                c.execute("UPDATE categories SET name = ? WHERE id = ?",
                          (new_name, category_id))
                conn.commit()
                success = True
    except sqlite3.IntegrityError:
        error_message = f"Erro de integridade ao tentar atualizar para o nome \'{new_name}\'."
    except Exception as e:
        error_message = f"Erro inesperado ao atualizar categoria: {e}"
    finally:
        conn.close()
    return success, error_message  # Retorna status e mensagem de erro


def delete_category(category_id):
    conn = get_connection()
    c = conn.cursor()
    success = False
    error_message = None
    try:
        # Verificar se a categoria existe antes de deletar
        c.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        category = c.fetchone()
        if not category:
            error_message = "Categoria não encontrada para exclusão."
        else:
            category_name = category[0]
            c.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()
            # Verificar se a exclusão foi bem-sucedida (opcional, commit lança exceção em caso de erro grave)
            c.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
            if c.fetchone() is None:
                success = True
            else:
                error_message = "Falha ao deletar a categoria do banco de dados."

    except sqlite3.Error as e:  # Captura erros específicos do SQLite
        error_message = f"Erro no banco de dados ao deletar categoria: {e}"
        conn.rollback()  # Desfaz a transação em caso de erro
    except Exception as e:
        error_message = f"Erro inesperado ao deletar categoria: {e}"
        conn.rollback()
    finally:
        conn.close()
    return success, error_message  # Retorna status e mensagem de erro

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


# --- Variáveis pré-definidas da calculadora (Pesos em gramas) ---
CALC_VARS = {
    "Placa 50x50cm (g)": 137.0,  # Peso da placa 50x50 em gramas
    "Placa 30x30cm (g)": 44.0,  # Peso da placa 30x30 em gramas
    "Placa 29x29cm (g)": 40.0,  # Peso da placa 29x29 em gramas (valor exemplo)
    # Custo adicional por KG se Limpeza/Granulação for Sim
    # Custo adicional por KG se Laminação for Sim
}


def get_calc_var(name):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute(
        "SELECT value FROM production_variables WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row[0] if row else None


def show_calculator_variables():
    st.subheader("Gerenciar Pesos e Perdas por Tipo de Placa")

    default_vals = {
        "peso_50x50": 137.0, "perda_50x50": 10.0,
        "peso_30x30": 44.0,  "perda_30x30": 8.0,
        "peso_29x29": 40.0,  "perda_29x29": 7.0,
    }

    with st.expander("Resetar para valores padrão"):
        if st.button("Resetar Variáveis", type="primary"):
            conn = get_connection()
            c = conn.cursor()
            for var, val in default_vals.items():
                c.execute(
                    "SELECT id FROM production_variables WHERE name = ?", (var,))
                if c.fetchone():
                    c.execute(
                        "UPDATE production_variables SET value = ? WHERE name = ?", (val, var))
                else:
                    c.execute(
                        "INSERT INTO production_variables (name, value) VALUES (?, ?) ", (var, val))
            conn.commit()
            conn.close()
            st.success("Variáveis redefinidas para os valores padrão.")
            st.rerun()

    placas = [
        ("50x50cm", "peso_50x50", "perda_50x50"),
        ("30x30cm", "peso_30x30", "perda_30x30"),
        ("29x29cm", "peso_29x29", "perda_29x29"),
    ]

    aba_labels = [f"Placa {p[0]}" for p in placas]
    st.markdown(
        "<h4 style='font-size:24px; margin-bottom:-70px;'>Selecionar Placa</h4>",
        unsafe_allow_html=True
    )
    aba = st.radio("", aba_labels, horizontal=True)
    index = aba_labels.index(aba)
    label, peso_key, perda_key = placas[index]

    peso_atual = get_calc_var(peso_key) or 0.0
    perda_atual = get_calc_var(perda_key) or 0.0

    with st.form(key=f"form_{label}"):
        col1, col2 = st.columns(2)
        with col1:
            novo_peso = st.number_input(
                "Peso (g)", min_value=0.0, value=peso_atual, format="%.2f", key=f"peso_{label}")
        with col2:
            nova_perda = st.number_input(
                "% de Perda", min_value=0.0, max_value=100.0, value=perda_atual, format="%.2f", key=f"perda_{label}")
        salvar = st.form_submit_button("Salvar")
        if salvar:
            conn = get_connection()
            c = conn.cursor()
            for key, val in [(peso_key, novo_peso), (perda_key, nova_perda)]:
                c.execute(
                    "SELECT id FROM production_variables WHERE name = ?", (key,))
                if c.fetchone():
                    c.execute(
                        "UPDATE production_variables SET value = ? WHERE name = ?", (val, key))
                else:
                    c.execute(
                        "INSERT INTO production_variables (name, value) VALUES (?, ?)", (key, val))
            conn.commit()
            conn.close()
            st.success(f"Valores da placa {label} atualizados.")
            st.rerun()


def show_price_calculator():
    # Estilo global para deixar os botões do radio maiores
    st.markdown("""
    <style>
        .big-radio .st-emotion-cache-1wmy9hl {
            font-size: 26px !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Título estilizado
    st.markdown(
        "<h6 style='font-size:28px; margin-bottom:-80px;'>Menu da Calculadora</h6>",
        unsafe_allow_html=True
    )

    # Radio com classe customizada
    with st.container():
        submenu = st.radio(
            label="",
            options=["Calcular Preço", "Variáveis"],
            horizontal=True,
            key="menu_radio"
        )

    if submenu == "Variáveis":
        show_calculator_variables()
        return

    st.header("Calculadora de Preços")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Dados Base")
            quantidade_kg = st.number_input(
                "Quantidade (KG)", min_value=0.1, format="%.2f", key="quantidade_kg", value=1.0)
            preco_ps = st.number_input(
                "Preço do PS (por KG)", min_value=0.0, format="%.2f", key="preco_ps")
            valor_frete_kg = st.number_input(
                "Valor do Frete (por KG)", min_value=0.0, format="%.2f", key="valor_frete_kg")
        with col2:
            st.subheader("Custos Adicionais")
            tem_limpeza = st.radio(
                "Limpeza/Granulação?", ["Não", "Sim"], key="tem_limpeza", horizontal=True)
            valor_limpeza = st.number_input("Valor Limpeza/Gran. (por KG)", min_value=0.0,
                                            format="%.2f", key="valor_limpeza") if tem_limpeza == "Sim" else 0.0
            tem_laminacao = st.radio(
                "Laminação?", ["Não", "Sim"], key="tem_laminacao", horizontal=True)
            valor_laminacao = st.number_input("Valor Laminação (por KG)", min_value=0.0,
                                              format="%.2f", key="valor_laminacao") if tem_laminacao == "Sim" else 0.0
            tem_ipi = st.radio(
                "IPI?", ["Não", "Sim"], key="tem_ipi", horizontal=True)
            percent_ipi = st.number_input(
                "% IPI", min_value=0.0, max_value=100.0, format="%.1f", key="percent_ipi") if tem_ipi == "Sim" else 0.0

    st.divider()

    if st.button("Calcular Preços", key="calcular_preco_final", use_container_width=True):
        try:
            peso_50x50 = get_calc_var("peso_50x50") / 1000.0
            peso_30x30 = get_calc_var("peso_30x30") / 1000.0
            peso_29x29 = get_calc_var("peso_29x29") / 1000.0
            perda_50 = get_calc_var("perda_50x50") / 100.0
            perda_30 = get_calc_var("perda_30x30") / 100.0
            perda_29 = get_calc_var("perda_29x29") / 100.0
        except Exception as e:
            st.error(
                "Erro ao buscar variáveis de peso ou perda. Verifique se foram definidas.")
            return

        if quantidade_kg <= 0:
            st.error("Erro: Quantidade (KG) deve ser maior que zero.")
            return

        preco1 = preco_ps + valor_frete_kg
        preco1_com_ipi = preco1 * (1 + percent_ipi / 100.0)
        preco2 = preco1_com_ipi + (valor_limpeza if tem_limpeza == "Sim" else 0) + (
            valor_laminacao if tem_laminacao == "Sim" else 0)

        # custo médio por tipo de placa
        custo_efetivo_50 = (
            (1 - perda_50) * preco1_com_ipi) + (perda_50 * preco2)
        custo_efetivo_30 = (
            (1 - perda_30) * preco1_com_ipi) + (perda_30 * preco2)
        custo_efetivo_29 = (
            (1 - perda_29) * preco1_com_ipi) + (perda_29 * preco2)

        custo_total_processado = quantidade_kg * \
            ((1 - perda_50) * preco1_com_ipi + perda_50 * preco2)  # base: 50x50

        preco_por_kg_efetivo = custo_total_processado / quantidade_kg

        custo_placa_50 = peso_50x50 * custo_efetivo_50
        custo_placa_30 = peso_30x30 * custo_efetivo_30
        custo_placa_29 = peso_29x29 * custo_efetivo_29

        st.subheader("Resultado do Cálculo")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.metric("Custo Total Processado",
                      f"R$ {custo_total_processado:.2f}")
            st.metric("Preço Efetivo por KG", f"R$ {preco_por_kg_efetivo:.2f}")
        with res_col2:
            st.metric("Custo Placa 50x50", f"R$ {custo_placa_50:.4f}")
            st.metric("Custo Placa 30x30", f"R$ {custo_placa_30:.4f}")
            st.metric("Custo Placa 29x29", f"R$ {custo_placa_29:.4f}")
    else:
        st.subheader("Resultado do Cálculo")
        st.info("Preencha os campos acima e clique em calcular.")


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
                    # ✅ CORRIGIDO VISUAL VARIÁVEIS
                    btn_col1, btn_col2 = st.columns([1, 1], gap="small")
                    with btn_col1:
                        if not st.session_state.get(f"confirm_delete_var_{var_id}"):
                            # ✅ CORRIGIDO TEXTO QUEBRADO
                            if st.button("Editar", key=f"edit_var_{var_id}", use_container_width=True):
                                st.session_state.editing_var = var_id
                                st.session_state.confirm_delete_var = None
                                st.rerun()
                    with btn_col2:
                        if not st.session_state.get(f"editing_var_{var_id}"):
                            # ✅ CORRIGIDO
                            if st.button("Deletar", key=f"del_var_{var_id}", use_container_width=True):
                                st.session_state.confirm_delete_var = var_id
                                st.session_state.editing_var = None
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.get("confirm_delete_var") == var_id:
                        st.warning(
                            f"Tem certeza que deseja deletar a variável \'{name}\'?")
                        # ✅ CONFIRMAR/CANCELAR MAIS PRÓXIMOS
                        confirm_cols = st.columns([1, 1], gap='small')
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

                        # ✅ SALVAR/CANCELAR MAIS PRÓXIMOS
                        edit_cols = st.columns([1, 1], gap='small')
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
                    btn_col1, btn_col2, _ = st.columns(
                        [1, 1, 6], gap='small')  # ✅ EDITAR/DELETAR PRODUTOS
                    with btn_col1:
                        if not st.session_state.get(f"confirm_delete_prod_{prod_id}"):
                            if st.button("Editar", key=f"edit_prod_{prod_id}"):
                                st.session_state.editing_prod = prod_id
                                st.session_state.confirm_delete_prod = None
                                st.rerun()
                    with btn_col2:
                        if not st.session_state.get(f"editing_prod_{prod_id}"):
                            # ✅ LARGURA AJUSTADA
                            if st.button("Deletar", key=f"del_prod_{prod_id}", use_container_width=True):
                                st.session_state.confirm_delete_prod = prod_id
                                st.session_state.editing_prod = None
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.get("confirm_delete_prod") == prod_id:
                        st.warning(
                            f"Tem certeza que deseja deletar o produto \'{name}\'?")
                        # ✅ CONFIRMAR/CANCELAR MAIS PRÓXIMOS
                        confirm_cols = st.columns([1, 1], gap='small')
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
                        toggle_key = f"show_vars_popup_edit_{prod_id}"
                        st.session_state[toggle_key] = not st.session_state.get(
                            toggle_key, False)
                        st.rerun()
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
                    st.session_state["show_vars_popup_new"] = not st.session_state.get(
                        "show_vars_popup_new", False)
                    st.rerun()
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

# test1
