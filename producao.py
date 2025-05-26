import streamlit as st
from textos import TEXTOS

def show_production_costs():
    st.subheader(TEXTOS["prod_titulo"])
    menu = st.radio(TEXTOS["prod_menu_titulo"], TEXTOS["prod_menu_opcoes"], horizontal=True)

    if menu == "Produtos":
        show_products()
    elif menu == "Variáveis de Custos":
        show_variables()
    elif menu == "Gerenciar Categorias":
        show_categories()

def show_products():
    st.info("Em construção: Produtos e Fórmulas.")

def show_variables():
    st.info("Em construção: Variáveis de Produção.")

def show_categories():
    st.info("Em construção: Categorias.")