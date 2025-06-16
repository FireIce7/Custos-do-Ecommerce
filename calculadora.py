import streamlit as st
import re
from textos import TEXTOS
from supabase_db import get_supabase_client

# --- Funções de Exibição de Mensagens ---


def display_error(message, e=None):
    error_text = f"Erro: {message}"
    if e:
        error_text += f" Detalhes: {e}"
    st.error(error_text)


def display_success(message):
    st.success(message)


def get_calc_var(name):
    sb = get_supabase_client()
    try:
        res = sb.table("variaveis_calc").select(
            "valor").eq("nome", name).single().execute()
        if isinstance(res.data, dict):
            try:
                return float(res.data.get("valor", 0.0))
            except (TypeError, ValueError):
                return 0.0
        return 0.0
    except Exception as e:
        display_error(f"Erro ao buscar variável de cálculo: {e}", e)
        return 0.0


def show_calculator_variables():
    st.subheader(TEXTOS["var_titulo"])
    default_vals = {
        "peso_50x50": 137.0, "perda_50x50": 10.0,
        "peso_30x30": 44.0, "perda_30x30": 8.0,
        "peso_25x25": 40.0, "perda_25x25": 7.0,
    }
    sb = get_supabase_client()
    with st.expander(TEXTOS["calc_resetar"]):
        if st.button(TEXTOS["calc_resetar"], type="primary"):
            if reset_calculator_variables_backend():
                display_success(
                    "Variáveis redefinidas para os valores padrão.")
            else:
                display_error(
                    "Erro ao redefinir variáveis para os valores padrão.")
            st.rerun()

    placas = [
        ("50x50cm", "peso_50x50", "perda_50x50"),
        ("30x30cm", "peso_30x30", "perda_30x30"),
        ("25x25cm", "peso_25x25", "perda_25x25"),
    ]
    labels = [TEXTOS["var_placas"][p[0][:2]] for p in placas]
    st.markdown(
        f"<h4 style=\'{TEXTOS['var_selecione_style']}\'>{TEXTOS['var_selecione_texto']}</h4>", unsafe_allow_html=True)
    choice = st.radio("Selecionar Placa para Editar Variáveis",
                      labels, horizontal=True, label_visibility="collapsed")
    idx = labels.index(choice)
    label, peso_key, perda_key = placas[idx]
    peso_val = float(get_calc_var(peso_key))
    perda_val = float(get_calc_var(perda_key))

    with st.form(key=f"form_{label}"):
        col1, col2 = st.columns(2)
        with col1:
            novo_peso = st.number_input(
                "Peso (g)", min_value=0.0, value=peso_val, format="%.2f")
        with col2:
            nova_perda = st.number_input(
                "% de Perda", min_value=0.0, max_value=100.0, value=perda_val, format="%.2f")
        if st.form_submit_button("Salvar"):
            for key, val in [(peso_key, novo_peso), (perda_key, nova_perda)]:
                if update_calc_variable(key, val):
                    display_success(f"Variável \'{key}\' atualizada.")
                else:
                    display_error(f"Erro ao salvar variável \'{key}\'")
            st.rerun()


def get_all_variables_as_dict():
    sb = get_supabase_client()
    try:
        data = sb.table("variaveis_custos").select(
            "nome, valor").execute().data
        return {item["nome"]: item["valor"] for item in data}
    except Exception as e:
        display_error(f"Erro ao buscar todas as variáveis: {e}", e)
        return {}

# Código revisado para cálculo de custo por placa 50×50 cm


# Parâmetros de entrada
preco_ps = 10.0           # R$ por kg de matéria-prima
valor_frete_kg = 5.0      # R$ de frete por kg
perda = 0.1660            # 16,60% de perda
peso_placa = 0.13020      # kg por placa (130,20 g)


def custo_placa(preco_ps, valor_frete_kg, perda, peso_placa, valor_laminacao):
    """
    Calcula o custo de uma placa de 50×50 cm.

    - preco_ps: preço da matéria-prima (R$/kg)
    - valor_frete_kg: frete (R$/kg)
    - perda: fração de perda (ex: 0.166 para 16,6%)
    - peso_placa: peso da placa em kg
    - valor_laminacao: custo de laminação por kg de material perdido
      (colocar 0 se não houver laminação)
    """
    preco1 = preco_ps + valor_frete_kg

    if valor_laminacao > 0:
        # Custo do kg final considerando reaproveitamento com laminação
        preco2 = preco1 + valor_laminacao
        custo_kg_final = (1 - perda) * preco1 + perda * preco2
    else:
        # Custo do kg útil sem laminação (divide pelo rendimento)
        custo_kg_final = preco1 / (1 - perda)

    return peso_placa * custo_kg_final


# Exemplos de uso
custo_sem_laminacao = custo_placa(
    preco_ps, valor_frete_kg, perda, peso_placa, 0.0)
custo_com_laminacao = custo_placa(
    preco_ps, valor_frete_kg, perda, peso_placa, 5.0)

print(f"Custo por placa sem laminação: R$ {custo_sem_laminacao:.4f}")
print(f"Custo por placa com laminação:    R$ {custo_com_laminacao:.4f}")


def show_price_calculator():
    st.markdown(
        "<style>.big-radio .st-emotion-cache-1wmy9hl{font-size:26px!important;font-weight:600!important;}</style>",
        unsafe_allow_html=True)
    st.markdown(
        f"<h4 style='{TEXTOS['calc_menu_titulo_style']}'>{TEXTOS['calc_menu_titulo_texto']}</h4>",
        unsafe_allow_html=True)
    submenu = st.radio("Menu da Calculadora",
                       TEXTOS["calc_menu_opcoes"],
                       horizontal=True,
                       key="menu_radio",
                       label_visibility="collapsed")
    if submenu == "Variáveis":
        show_calculator_variables()
        return

    st.markdown(
        f"<h3 style='{TEXTOS['calc_titulo_style']}'>{TEXTOS['calc_titulo_texto']}</h3>",
        unsafe_allow_html=True)

    # --- Inputs ---
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            preco_ps = st.number_input(
                "Preço do PS (por KG)",
                min_value=0.0,
                format="%.2f",
                key="preco_ps")
            quantidade_kg = st.number_input(
                "Quantidade (KG)",
                min_value=0.1,
                format="%.2f",
                key="quantidade_kg",
                value=1.0)
            valor_frete_kg = st.number_input(
                "Valor do Frete (por KG)",
                min_value=0.0,
                format="%.2f",
                key="valor_frete_kg")
        with col2:
            tem_limpeza = st.radio(
                "Limpeza/Granulação?",
                ["Não", "Sim"],
                key="tem_limpeza",
                horizontal=True)
            valor_limpeza = st.number_input(
                "Valor Limpeza/Gran. (por KG)",
                min_value=0.0,
                format="%.2f",
                key="valor_limpeza") if tem_limpeza == "Sim" else 0.0

            tem_laminacao = st.radio(
                "Laminação?",
                ["Não", "Sim"],
                key="tem_laminacao",
                horizontal=True)
            valor_laminacao = st.number_input(
                "Valor Laminação (por KG)",
                min_value=0.0,
                format="%.2f",
                key="valor_laminacao") if tem_laminacao == "Sim" else 0.0

            tem_ipi = st.radio(
                "IPI?",
                ["Não", "Sim"],
                key="tem_ipi",
                horizontal=True)
            percent_ipi = st.number_input(
                "% IPI",
                min_value=0.0,
                max_value=100.0,
                format="%.1f",
                key="percent_ipi") if tem_ipi == "Sim" else 0.0

    st.divider()

    if st.button(TEXTOS["calc_botao"], use_container_width=True):
        try:
            # Carrega pesos (kg) e perdas (fração)
            peso_50 = float(get_calc_var("peso_50x50")) / 1000
            perda_50 = float(get_calc_var("perda_50x50")) / 100
            peso_30 = float(get_calc_var("peso_30x30")) / 1000
            perda_30 = float(get_calc_var("perda_30x30")) / 100
            peso_25 = float(get_calc_var("peso_25x25")) / 1000
            perda_25 = float(get_calc_var("perda_25x25")) / 100

            # Preço base/kg e preço do scrap tratado/kg
            preco1 = preco_ps * (1 + percent_ipi/100) + valor_frete_kg
            preco2 = preco1 + valor_limpeza + valor_laminacao

            # Função auxiliar para custo da placa
            def custo_placa(peso, perda):
                if valor_limpeza > 0 or valor_laminacao > 0:
                    # Reaproveita sucata (limpeza ou laminação)
                    custo_kg_final = (1 - perda) * preco1 + perda * preco2
                else:
                    # Sucata perdida – ajusta pelo rendimento
                    custo_kg_final = preco1 / (1 - perda)
                return peso * custo_kg_final

            # Calcula custos
            custo_placa50 = custo_placa(peso_50, perda_50)
            custo_placa30 = custo_placa(peso_30, perda_30)
            custo_placa25 = custo_placa(peso_25, perda_25)

            # Exibe resultado
            st.metric("Custo Placa 50x50", f"R$ {custo_placa50:.4f}")
            st.metric("Custo Placa 30x30", f"R$ {custo_placa30:.4f}")
            st.metric("Custo Placa 25x25", f"R$ {custo_placa25:.4f}")

        except Exception as e:
            display_error(f"Erro no cálculo: {e}", e)
    else:
        st.subheader(TEXTOS["calc_resultado"])
        st.info(TEXTOS["calc_info"])


def calculate_cost(formula):
    try:
        variables = get_all_variables_as_dict()

        def replace_var(match):
            var_name = match.group(0)
            if var_name in variables:
                return str(variables[var_name])
            else:
                display_error(
                    f"Variável \'{var_name}\' não encontrada no banco de dados. Usando 0.0.")
                return "0.0"

        processed_formula = re.sub(
            r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', replace_var, formula)

        return eval(processed_formula)
    except NameError as ne:
        display_error(f"Erro na fórmula: Variável não definida - {ne}", ne)
        return None
    except Exception as e:
        display_error(f"Erro ao calcular custo: {e}", e)
        return None


def update_calc_variable(name, value):
    sb = get_supabase_client()
    try:
        sb.table("variaveis_calc").upsert(
            {"nome": name, "valor": value},
            on_conflict="nome",
        ).execute()
        return True
    except Exception as e:
        display_error(f"Erro ao salvar variável \'{name}\'", e)
        return False


def reset_calculator_variables_backend():
    sb = get_supabase_client()
    default_vals = {
        "peso_50x50": 0, "perda_50x50": 0,
        "peso_30x30": 0, "perda_30x30": 0,
        "peso_25x25": 0, "perda_25x25": 0,
    }
    try:
        for nome, valor in default_vals.items():
            sb.table("variaveis_calc").upsert(
                {"nome": nome, "valor": valor},
                on_conflict="nome",
            ).execute()
        return True
    except Exception as e:
        display_error(f"Erro ao redefinir variáveis: {e}", e)
        return False
