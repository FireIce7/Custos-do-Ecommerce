import streamlit as st
from textos import TEXTOS
from supabase_db import SupabaseError  # Importar a exceção customizada


def gerenciar_producao(supabase_db):
    st.title(TEXTOS["gerenciar_producao_titulo"])

    # Gerenciar Produtos
    st.header(TEXTOS["adicionar_produto_titulo"])
    with st.form("form_produto", clear_on_submit=True):
        nome_produto = st.text_input(TEXTOS["nome_produto_label"])
        descricao_produto = st.text_area(TEXTOS["descricao_produto_label"])
        unidade_medida = st.text_input(TEXTOS["unidade_medida_label"])
        formula_produto = st.text_input(TEXTOS["formula_produto_label"])

        try:
            categorias_produtos = supabase_db.get_all_categorias_produtos()
            categoria_produto_nomes = [
                cat["nome"] for cat in categorias_produtos] if categorias_produtos else []
        except SupabaseError as e:
            st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
            categoria_produto_nomes = []

        categoria_produto_selecionada = st.selectbox(
            TEXTOS["categoria_produto_label"], options=categoria_produto_nomes)

        submitted_produto = st.form_submit_button(TEXTOS["salvar_produto_btn"])
        if submitted_produto:
            produto_data = {
                "nome": nome_produto,
                "descricao": descricao_produto,
                "unidade_medida": unidade_medida,
                "formula": formula_produto,
                "categoria": categoria_produto_selecionada
            }
            try:
                supabase_db.add_produto(produto_data)
                st.success(TEXTOS["produto_salvo_sucesso"])
                st.experimental_rerun()
            except SupabaseError as e:
                st.error(f"{TEXTOS["erro_salvar_produto"]} Detalhes: {e}")

    st.subheader(TEXTOS["produtos_existentes_titulo"])
    try:
        produtos = supabase_db.get_all_produtos()
    except SupabaseError as e:
        st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
        produtos = []

    if produtos:
        for produto in produtos:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{produto["nome"]}** ({produto["unidade_medida"]})")
                st.caption(produto["descricao"])
                st.code(produto["formula"])
                st.write(f"Categoria: {produto["categoria"]}")
            with col2:
                if st.button(TEXTOS["editar_produto_btn"], key=f"edit_prod_{produto["id"]}"):
                    # Lógica para edição (a ser implementada ou expandida)
                    st.info("Funcionalidade de edição em desenvolvimento.")
            with col3:
                if st.button(TEXTOS["excluir_produto_btn"], key=f"del_prod_{produto["id"]}"):
                    if st.warning(TEXTOS["confirmar_exclusao_produto"]):
                        try:
                            supabase_db.delete_produto(produto["id"])
                            st.success(TEXTOS["produto_excluido_sucesso"])
                            st.experimental_rerun()
                        except SupabaseError as e:
                            st.error(f"{TEXTOS["erro_excluir_produto"]} Detalhes: {e}")
            with col4:
                pass  # Espaço para futuras ações
    else:
        st.info(TEXTOS["nenhum_produto_encontrado"])

    st.markdown("--- - - -")

    # Gerenciar Variáveis
    st.header(TEXTOS["adicionar_variavel_titulo"])
    with st.form("form_variavel", clear_on_submit=True):
        nome_variavel = st.text_input(TEXTOS["nome_variavel_label"])
        custo_variavel = st.number_input(
            TEXTOS["custo_variavel_label"], min_value=0.0, format="%.2f")

        try:
            categorias_variaveis = supabase_db.get_all_categorias_variaveis()
            categoria_variavel_nomes = [
                cat["nome"] for cat in categorias_variaveis] if categorias_variaveis else []
        except SupabaseError as e:
            st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
            categoria_variavel_nomes = []

        categoria_variavel_selecionada = st.selectbox(
            TEXTOS["categoria_variavel_label"], options=categoria_variavel_nomes)

        submitted_variavel = st.form_submit_button(
            TEXTOS["salvar_variavel_btn"])
        if submitted_variavel:
            variavel_data = {
                "nome": nome_variavel,
                "custo": custo_variavel,
                "categoria": categoria_variavel_selecionada
            }
            try:
                supabase_db.add_variavel(variavel_data)
                st.success(TEXTOS["variavel_salva_sucesso"])
                st.experimental_rerun()
            except SupabaseError as e:
                st.error(f"{TEXTOS["erro_salvar_variavel"]} Detalhes: {e}")

    st.subheader(TEXTOS["variaveis_existentes_titulo"])
    try:
        variaveis = supabase_db.get_all_variaveis()
    except SupabaseError as e:
        st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
        variaveis = []

    if variaveis:
        for variavel in variaveis:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{variavel["nome"]}**: R$ {variavel["custo"]:.2f}")
                st.write(f"Categoria: {variavel["categoria"]}")
            with col2:
                if st.button(TEXTOS["editar_variavel_btn"], key=f"edit_var_{variavel["id"]}"):
                    # Lógica para edição (a ser implementada ou expandida)
                    st.info("Funcionalidade de edição em desenvolvimento.")
            with col3:
                if st.button(TEXTOS["excluir_variavel_btn"], key=f"del_var_{variavel["id"]}"):
                    if st.warning(TEXTOS["confirmar_exclusao_variavel"]):
                        try:
                            supabase_db.delete_variavel(variavel["id"])
                            st.success(TEXTOS["variavel_excluida_sucesso"])
                            st.experimental_rerun()
                        except SupabaseError as e:
                            st.error(f"{TEXTOS["erro_excluir_variavel"]} Detalhes: {e}")
            with col4:
                pass  # Espaço para futuras ações
    else:
        st.info(TEXTOS["nenhuma_variavel_encontrada"])

    st.markdown("--- - - -")

    # Gerenciar Categorias de Produtos
    st.header(TEXTOS["categorias_produtos_titulo"])
    with st.form("form_categoria_produto", clear_on_submit=True):
        nova_categoria_produto = st.text_input(
            TEXTOS["nova_categoria_produto_label"])
        submitted_categoria_produto = st.form_submit_button(
            TEXTOS["adicionar_categoria_produto_btn"])
        if submitted_categoria_produto:
            try:
                supabase_db.add_categoria_produto(
                    {"nome": nova_categoria_produto})
                st.success(TEXTOS["categoria_produto_salva_sucesso"])
                st.experimental_rerun()
            except SupabaseError as e:
                st.error(f"{TEXTOS["erro_salvar_categoria_produto"]} Detalhes: {e}")

    st.subheader("Categorias de Produtos Existentes")
    try:
        categorias_produtos = supabase_db.get_all_categorias_produtos()
    except SupabaseError as e:
        st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
        categorias_produtos = []

    if categorias_produtos:
        for categoria in categorias_produtos:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {categoria["nome"]}")
            with col2:
                if st.button(TEXTOS["excluir_categoria_produto_btn"], key=f"del_cat_prod_{categoria["id"]}"):
                    produtos_com_categoria = []
                    try:
                        all_produtos = supabase_db.get_all_produtos()
                        if all_produtos:
                            produtos_com_categoria = [
                                p for p in all_produtos if p["categoria"] == categoria["nome"]]
                    except SupabaseError as e:
                        st.warning(
                            f"Não foi possível verificar produtos associados à categoria: {e}")

                    if produtos_com_categoria:
                        st.error(TEXTOS["categoria_produto_em_uso"])
                    else:
                        try:
                            supabase_db.delete_categoria_produto(
                                categoria["id"])
                            st.success(TEXTOS["categoria_excluida_sucesso"])
                            st.experimental_rerun()
                        except SupabaseError as e:
                            st.error(f"{TEXTOS["erro_excluir_categoria_produto"]} Detalhes: {e}")
    else:
        st.info("Nenhuma categoria de produto encontrada.")

    st.markdown("--- - - -")

    # Gerenciar Categorias de Variáveis
    st.header(TEXTOS["categorias_variaveis_titulo"])
    with st.form("form_categoria_variavel", clear_on_submit=True):
        nova_categoria_variavel = st.text_input(
            TEXTOS["nova_categoria_variavel_label"])
        submitted_categoria_variavel = st.form_submit_button(
            TEXTOS["adicionar_categoria_variavel_btn"])
        if submitted_categoria_variavel:
            try:
                supabase_db.add_categoria_variavel(
                    {"nome": nova_categoria_variavel})
                st.success(TEXTOS["categoria_variavel_salva_sucesso"])
                st.experimental_rerun()
            except SupabaseError as e:
                st.error(f"{TEXTOS["erro_salvar_categoria_variavel"]} Detalhes: {e}")

    st.subheader("Categorias de Variáveis Existentes")
    try:
        categorias_variaveis = supabase_db.get_all_categorias_variaveis()
    except SupabaseError as e:
        st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
        categorias_variaveis = []

    if categorias_variaveis:
        for categoria in categorias_variaveis:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {categoria["nome"]}")
            with col2:
                if st.button(TEXTOS["excluir_categoria_variavel_btn"], key=f"del_cat_var_{categoria["id"]}"):
                    variaveis_com_categoria = []
                    try:
                        all_variaveis = supabase_db.get_all_variaveis()
                        if all_variaveis:
                            variaveis_com_categoria = [
                                v for v in all_variaveis if v["categoria"] == categoria["nome"]]
                    except SupabaseError as e:
                        st.warning(
                            f"Não foi possível verificar variáveis associadas à categoria: {e}")

                    if variaveis_com_categoria:
                        st.error(TEXTOS["categoria_variavel_em_uso"])
                    else:
                        try:
                            supabase_db.delete_categoria_variavel(
                                categoria["id"])
                            st.success(TEXTOS["categoria_excluida_sucesso"])
                            st.experimental_rerun()
                        except SupabaseError as e:
                            st.error(f"{TEXTOS["erro_excluir_categoria_variavel"]} Detalhes: {e}")
    else:
        st.info("Nenhuma categoria de variável encontrada.")
