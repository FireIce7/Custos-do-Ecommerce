import streamlit as st
from textos import TEXTOS
from calculadora import show_price_calculator
from producao import show_production_costs
from banco import init_db

# Inicializar banco de dados
init_db()

# Configuração da página
st.set_page_config(page_title="Custos do Ecommerce", layout="wide")

# Menu lateral
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", TEXTOS["menu_lateral"])

if menu == "Custos de Produção":
    show_production_costs()
elif menu == "Calculadora de Preços":
    show_price_calculator()