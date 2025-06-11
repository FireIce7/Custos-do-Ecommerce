import streamlit as st
from textos import TEXTOS
from calculadora import show_price_calculator
from producao import show_production_costs
from banco import init_db

# Inicializar banco de dados
init_db()

# Configuração da página
st.set_page_config(page_title="Custos do Ecommerce", layout="wide")

# Adicionar CSS personalizado
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

# Menu lateral
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", TEXTOS["menu_lateral"])

if menu == "Custos de Produção":
    show_production_costs()
elif menu == "Calculadora de Preços":
    show_price_calculator()
