import streamlit as st
from textos import TEXTOS
from banco import get_calc_var, get_connection


def show_calculator_variables():
    st.subheader(TEXTOS["var_titulo"])

    default_vals = {
        "peso_50x50": 137.0, "perda_50x50": 10.0,
        "peso_30x30": 44.0,  "perda_30x30": 8.0,
        "peso_25x25": 40.0,  "perda_25x25": 7.0,
    }

    with st.expander(TEXTOS["calc_resetar"]):
        if st.button(TEXTOS["calc_resetar"], type="primary"):
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
                        "INSERT INTO production_variables (name, value) VALUES (?, ?)", (var, val))
            conn.commit()
            conn.close()
            st.success("Variáveis redefinidas para os valores padrão.")
            st.rerun()

    placas = [
        ("50x50cm", "peso_50x50", "perda_50x50"),
        ("30x30cm", "peso_30x30", "perda_30x30"),
        ("25x25cm", "peso_25x25", "perda_25x25"),
    ]
    aba_labels = [TEXTOS["var_placas"][label[:2]] for label, *_ in placas]

    st.markdown(
        f"<h4 style='{TEXTOS['var_selecione_style']}'>{TEXTOS['var_selecione_texto']}</h4>", unsafe_allow_html=True)
    aba = st.radio("Selecionar Placa para Editar Variáveis",
                   aba_labels, horizontal=True, label_visibility="collapsed")
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
    st.markdown(
        "<style>.big-radio .st-emotion-cache-1wmy9hl { font-size: 26px !important; font-weight: 600 !important; }</style>", unsafe_allow_html=True)
    st.markdown(
        f"<h4 style='{TEXTOS['calc_menu_titulo_style']}'>{TEXTOS['calc_menu_titulo_texto']}</h4>", unsafe_allow_html=True)

    submenu = st.radio("Menu da Calculadora", TEXTOS["calc_menu_opcoes"],
                       horizontal=True, key="menu_radio", label_visibility="collapsed")
    if submenu == "Variáveis":
        show_calculator_variables()
        return

    st.markdown(
        f"<h3 style='{TEXTOS['calc_titulo_style']}'>{TEXTOS['calc_titulo_texto']}</h3>", unsafe_allow_html=True)
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(TEXTOS["calc_dados_base"])
            preco_ps = st.number_input(
                "Preço do PS (por KG)", min_value=0.0, format="%.2f", key="preco_ps")
            quantidade_kg = st.number_input(
                "Quantidade (KG)", min_value=0.1, format="%.2f", key="quantidade_kg", value=1.0)
            valor_frete_kg = st.number_input(
                "Valor do Frete (por KG)", min_value=0.0, format="%.2f", key="valor_frete_kg")
        with col2:
            st.subheader(TEXTOS["calc_adicionais"])
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

    if st.button(TEXTOS["calc_botao"], key="calcular_preco_final", use_container_width=True):
        try:
            peso_50x50 = get_calc_var("peso_50x50") / 1000.0
            peso_30x30 = get_calc_var("peso_30x30") / 1000.0
            peso_25x25 = get_calc_var("peso_25x25") / 1000.0
            perda_50 = get_calc_var("perda_50x50") / 100.0
            perda_30 = get_calc_var("perda_30x30") / 100.0
            perda_29 = get_calc_var("perda_25x25") / 100.0
        except Exception:
            st.error("Erro ao buscar variáveis de peso ou perda.")
            return

        preco1_com_ipi = preco_ps * (1 + percent_ipi / 100.0) + valor_frete_kg
        preco2 = preco1_com_ipi + valor_limpeza + valor_laminacao

        custo_efetivo_50 = (1 - perda_50) * preco1_com_ipi + perda_50 * preco2
        custo_efetivo_30 = (1 - perda_30) * preco1_com_ipi + perda_30 * preco2
        custo_efetivo_29 = (1 - perda_29) * preco1_com_ipi + perda_29 * preco2

        custo_total_processado = quantidade_kg * \
            ((1 - perda_50) * preco1_com_ipi + perda_50 * preco2)
        preco_por_kg_efetivo = custo_total_processado / quantidade_kg

        custo_placa_50 = peso_50x50 * custo_efetivo_50
        custo_placa_30 = peso_30x30 * custo_efetivo_30
        custo_placa_29 = peso_25x25 * custo_efetivo_29

        st.subheader(TEXTOS["calc_resultado"])
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
        st.subheader(TEXTOS["calc_resultado"])
        st.info(TEXTOS["calc_info"])
