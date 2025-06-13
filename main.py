import streamlit as st
from supabase_db import SupabaseDB, SupabaseError
from producao import gerenciar_producao
from calculadora import calcular_custo
from textos import TEXTOS


def main():
    st.set_page_config(layout="wide")
    st.title(TEXTOS["titulo_app"])

    try:
        supabase_db = SupabaseDB()
    except SupabaseError as e:
        st.error(f"{TEXTOS["erro_conexao_db"]} Detalhes: {e}")
        st.stop()  # Interrompe a execução se não conseguir conectar ao Supabase

    menu = ["Gerenciar Produção", "Calcular Custo"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Gerenciar Produção":
        gerenciar_producao(supabase_db)
    elif choice == "Calcular Custo":
        calcular_custo(supabase_db)


if __name__ == "__main__":
    main()
