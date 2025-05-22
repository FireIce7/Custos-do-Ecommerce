import streamlit as st
import sqlite3

# ——— PRIMEIRO COMANDO STREAMLIT NO ARQUIVO ———
try:
    st.set_page_config(page_title="Calculadora de Custos", layout="wide")
except st.errors.StreamlitAPIException:
    pass

# --- CSS para aumentar o tamanho das fontes na sidebar e menus ---
st.markdown("""
<style>
    /* Aumentar fonte na barra lateral */
    .st-emotion-cache-16idsys p, .st-emotion-cache-16idsys span {
        font-size: 18px !important;
    }
    
    /* Aumentar fonte nos menus de rádio */
    .st-emotion-cache-1qg05tj p, .st-emotion-cache-1qg05tj span {
        font-size: 18px !important;
    }
    
    /* Aumentar fonte nos botões */
    .stButton button {
        font-size: 16px !important;
    }
    
    /* Aumentar fonte nos submenus */
    .st-emotion-cache-183lzff p {
        font-size: 18px !important;
    }
    
    /* Aumentar fonte nos expanders */
    .st-emotion-cache-1avcm0n {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

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
        # Melhorada a lógica para garantir que as variáveis sejam reconhecidas
        # Adicionando verificação de variáveis antes da avaliação
        for var_name in env:
            if var_name not in formula:
                continue
        return eval(formula, {"__builtins__": {}}, env)
    except Exception as e:
        st.error(f"Erro ao calcular: {str(e)}")
        return None


# --- Cálculo de preço para nova seção (exemplo simples) ---
def calculate_price(cost, margin_percent):
    try:
        price = cost * (1 + margin_percent / 100)
        return price
    except:
        return None


# --- Funções de interface para os menus e submenu ---

def show_production_costs():
    st.header("Custos de Produção")

    # Opção para submenu - escolher entre "Custos" e "Variáveis de Custos"
    submenu = st.radio("Menu Variantes", [
                       "Custos", "Variáveis de Custos"], horizontal=True)

    if submenu == "Variáveis de Custos":
        show_variables()
    else:
        show_products()


def show_variables():
    st.subheader("Variáveis de Produção")
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


def show_products():
    st.subheader("Produtos e Fórmulas")
    prod_list = get_products()
    col1, col2 = st.columns([3, 1])

    # Obter todas as variáveis disponíveis para exibir como ajuda
    vars_list = get_variables()
    var_names = [name for _, name, _ in vars_list]

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

                    # Mostrar variáveis disponíveis como ajuda
                    if var_names:
                        st.markdown("**Variáveis disponíveis:** " +
                                    ", ".join(var_names))

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

        # Mostrar variáveis disponíveis como ajuda
        if var_names:
            st.markdown("**Variáveis disponíveis:** " + ", ".join(var_names))

        np_formula = st.text_input("Fórmula", key="new_prod_formula")
        if st.button("Adicionar Produto"):
            if np_name and np_formula:
                add_product(np_name, np_formula)
                st.rerun()
            else:
                st.error("Informe nome e fórmula válidos.")


def show_price_calculator():
    st.header("Calculadora de Preços")
    cost = st.number_input("Custo do Produto", min_value=0.0, format="%.2f")
    margin = st.number_input(
        "Margem de Lucro (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    if st.button("Calcular Preço"):
        price = calculate_price(cost, margin)
        if price is not None:
            st.success(f"Preço sugerido: R$ {price:.2f}")
        else:
            st.error("Erro ao calcular preço")


def main():
    init_db()

    # Menu principal lateral com os dois menus desejados
    menu = st.sidebar.radio(
        "Navegação", ["Custos de Produção", "Calculadora de Preços"])

    if menu == "Custos de Produção":
        show_production_costs()
    elif menu == "Calculadora de Preços":
        show_price_calculator()


if __name__ == "__main__":
    main()

# test
