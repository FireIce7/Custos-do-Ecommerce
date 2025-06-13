import streamlit as st
from textos import TEXTOS
from calculadora import show_price_calculator
from producao import show_production_costs

st.set_page_config(page_title="Custos do Ecommerce", layout="wide")

st.markdown("""
<style>
div.stButton > button {
    font-weight: bold;
    border-radius: 4px;
    height: 2.5em;
    margin-top: 0.5em;
}
div.stButton > button p {
    text-align: center;
    width: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
div[data-testid="stExpander"] {
    border-radius: 4px;
}
h3 {
    font-size: 1.5em !important;
}
.pagination-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 1em 0;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", TEXTOS["menu_lateral"])

if menu == "Custos de Produção":
    show_production_costs()
elif menu == "Calculadora de Preços":
    show_price_calculator()
