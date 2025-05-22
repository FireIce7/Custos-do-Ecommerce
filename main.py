import streamlit as st
import sqlite3

# ——— PRIMEIRO COMANDO STREAMLIT NO ARQUIVO ———
try:
    st.set_page_config(page_title="Calculadora de Custos", layout="wide")
except st.errors.StreamlitAPIException:
    pass

# --- Funções de Banco (SEM usar Streamlit) ---


def get_connection():
    return sqlite3.connect('data.db', check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS production_variables (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            value REAL
        )
        '''
    )
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            formula TEXT
        )
        '''
    )
    conn.commit()
    conn.close()


def get_variables():
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute(
        'SELECT id, name, value FROM production_variables').fetchall()
    conn.close()
    return rows


def add_variable(name, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        'INSERT OR REPLACE INTO production_variables (name, value) VALUES (?, ?)', (name, value))
    conn.commit()
    conn.close()


def update_variable(var_id, name, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE production_variables SET name = ?, value = ? WHERE id = ?',
              (name, value, var_id))
    conn.commit()
    conn.close()


def delete_variable(var_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM production_variables WHERE id = ?', (var_id,))
    conn.commit()
    conn.close()


def get_products():
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute('SELECT id, name, formula FROM products').fetchall()
    conn.close()
    return rows


def add_product(name, formula):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        'INSERT OR REPLACE INTO products (name, formula) VALUES (?, ?)', (name, formula))
    conn.commit()
    conn.close()


def update_product(prod_id, name, formula):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE products SET name = ?, formula = ? WHERE id = ?',
              (name, formula, prod_id))
    conn.commit()
    conn.close()


def delete_product(prod_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (prod_id,))
    conn.commit()
    conn.close()

# --- Cálculo de custo ---


def calculate_cost(formula):
    vars = get_variables()
    env = {name: val for _, name, val in vars}
    try:
        return eval(formula, {}, env)
    except Exception:
        return None

# --- Função Principal (TODO ST.* DENTRO) ---


def main():
    init_db()

    # Navegação por abas
    tabs = st.tabs(["Variáveis de Produção", "Custos de Produção"])

    # Aba 1: Variáveis de Produção
    with tabs[0]:
        st.header("Variáveis de Produção")
        col1, col2 = st.columns([3, 1])
        vars_list = get_variables()

        with col1:
            if vars_list:
                for var_id, name, value in vars_list:
                    with st.container():
                        st.markdown(f"## {name}")
                        st.markdown(f"**Valor:** {value}")
                        btn_edit, btn_del = st.columns(2)
                        if btn_edit.button("✏️ Editar", key=f"edit_var_{var_id}"):
                            st.session_state.editing_var = var_id
                        if btn_del.button("🗑️ Deletar", key=f"del_var_{var_id}"):
                            delete_variable(var_id)
                            st.rerun()
                    if st.session_state.get('editing_var') == var_id:
                        new_name = st.text_input(
                            "Nome", value=name, key=f"name_var_{var_id}")
                        new_value = st.number_input(
                            "Valor", value=value, key=f"value_var_{var_id}")
                        if st.button("Salvar", key=f"save_var_{var_id}"):
                            update_variable(var_id, new_name, new_value)
                            del st.session_state['editing_var']
                            st.rerun()
            else:
                st.info("Nenhuma variável cadastrada.")

        with col2:
            st.subheader("Criar Nova Variável")
            nv_name = st.text_input("Nome da Variável", key="new_var_name")
            nv_value = st.number_input("Valor", key="new_var_value")
            if st.button("Adicionar Variável"):
                if nv_name:
                    add_variable(nv_name, nv_value)
                    st.rerun()
                else:
                    st.error("Informe um nome válido.")

    # Aba 2: Custos de Produção
    with tabs[1]:
        st.header("Custos de Produção")
        col1, col2 = st.columns([3, 1])
        prod_list = get_products()

        with col1:
            if prod_list:
                for prod_id, name, formula in prod_list:
                    cost = calculate_cost(formula)
                    label = f"{name} - R$ {cost:.2f}" if cost is not None else name
                    with st.expander(label):
                        if cost is not None:
                            st.metric("Custo Atual", f"R$ {cost:.2f}")
                        else:
                            st.error("Erro ao calcular custo.")
                        st.markdown(f"**Fórmula:** `{formula}`")
                        btn_edit, btn_del = st.columns(2)
                        if btn_edit.button("✏️ Editar", key=f"edit_prod_{prod_id}"):
                            st.session_state.editing_prod = prod_id
                        if btn_del.button("🗑️ Deletar", key=f"del_prod_{prod_id}"):
                            delete_product(prod_id)
                            st.rerun()
                    if st.session_state.get('editing_prod') == prod_id:
                        new_name = st.text_input(
                            "Nome", value=name, key=f"name_prod_{prod_id}")
                        new_formula = st.text_input(
                            "Fórmula", value=formula, key=f"formula_prod_{prod_id}")
                        if st.button("Salvar", key=f"save_prod_{prod_id}"):
                            update_product(prod_id, new_name, new_formula)
                            del st.session_state['editing_prod']
                            st.rerun()
            else:
                st.info("Nenhum produto cadastrado.")

        with col2:
            st.subheader("Criar Novo Produto")
            np_name = st.text_input("Nome do Produto", key="new_prod_name")
            np_formula = st.text_input("Fórmula", key="new_prod_formula")
            if st.button("Adicionar Produto"):
                if np_name and np_formula:
                    add_product(np_name, np_formula)
                    st.rerun()
                else:
                    st.error("Informe nome e fórmula válidos.")


if __name__ == "__main__":
    main()
