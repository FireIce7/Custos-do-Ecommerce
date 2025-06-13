import math
import operator
from textos import TEXTOS
import streamlit as st
from supabase_db import SupabaseError


def evaluate_formula(formula: str, context: dict):
    """Avalia uma fórmula matemática dada um contexto de variáveis e produtos."""
    try:
        # Usar eval com um dicionário de globals e locals para segurança e contexto
        # math e operator são incluídos para permitir operações matemáticas e lógicas
        safe_dict = {**context, **{"math": math, "operator": operator}}
        return eval(formula, {"__builtins__": None}, safe_dict)
    except (NameError, SyntaxError, TypeError) as e:
        raise ValueError(f"Erro de sintaxe ou nome na fórmula: {e}")
    except Exception as e:
        raise ValueError(f"Erro inesperado ao avaliar a fórmula: {e}")


def calculate_product_cost(product_name: str, all_products: list, all_variables: list, evaluated_products: dict = None, path: list = None):
    """Calcula o custo de um produto, resolvendo dependências de outros produtos.
    Detecta e previne dependências circulares.
    """
    if evaluated_products is None:
        evaluated_products = {}
    if path is None:
        path = []

    # Detectar dependência circular
    if product_name in path:
        raise ValueError(f"Dependência circular detectada: {" -> ".join(path + [product_name])}")

    # Retornar custo já calculado, se disponível
    if product_name in evaluated_products:
        return evaluated_products[product_name]

    # Encontrar o produto
    product = next(
        (p for p in all_products if p["nome"] == product_name), None)
    if not product:
        raise ValueError(
            f"Produto \'{product_name}\' não encontrado na lista de produtos.")

    formula = product["formula"]

    # Adicionar produto ao caminho para detecção de ciclo
    path.append(product_name)

    # Dicionário de variáveis para a avaliação
    variables_dict = {v["nome"]: v["custo"] for v in all_variables}

    # Resolver sub-produtos na fórmula
    context_for_eval = {**variables_dict}
    for p in all_products:
        if p["nome"] != product_name and p["nome"] in formula:
            try:
                sub_product_cost = calculate_product_cost(
                    p["nome"], all_products, all_variables, evaluated_products, path)
                context_for_eval[p["nome"]] = sub_product_cost
            except ValueError as e:
                # Propagar erro de sub-produto com contexto
                raise ValueError(
                    f"Erro ao calcular custo do sub-produto \'{p['nome']}\': {e}")

    # Remover produto do caminho após avaliação
    path.pop()

    try:
        cost = evaluate_formula(formula, context_for_eval)
        evaluated_products[product_name] = cost
        return cost
    except ValueError as e:
        raise ValueError(
            f"Erro ao calcular custo para \'{product_name}\' com fórmula \'{formula}\': {e}")
    except Exception as e:
        raise ValueError(
            f"Erro inesperado ao calcular custo para \'{product_name}\': {e}")


def calcular_custo(supabase_db):
    st.title("Calcular Custo de Produto")

    try:
        produtos = supabase_db.get_all_produtos()
        # Alterado para usar variaveis_calc para a calculadora
        variaveis = supabase_db.get_all_variaveis_calc()
    except SupabaseError as e:
        st.error(f"{TEXTOS["erro_carregar_dados"]} Detalhes: {e}")
        return

    if not produtos:
        st.info(TEXTOS["nenhum_produto_encontrado"])
        return

    produto_selecionado_nome = st.selectbox(
        TEXTOS["selecione_produto_calcular"],
        [p["nome"] for p in produtos]
    )

    produto_selecionado = next(
        (p for p in produtos if p["nome"] == produto_selecionado_nome), None)

    if produto_selecionado:
        formula = produto_selecionado["formula"]
        st.write(f"Fórmula para **{produto_selecionado_nome}**: `{formula}`")

        if st.button(TEXTOS["calcular_custo_btn"]):
            try:
                custo_total = calculate_product_cost(
                    produto_selecionado_nome, produtos, variaveis)
                st.success(f"{TEXTOS["custo_calculado"]} R$ {custo_total:.2f}")
            except ValueError as e:
                st.error(f"{TEXTOS["erro_formula_invalida"]} Detalhes: {e}")
            except Exception as e:
                st.error(f"{TEXTOS["erro_generico"]} Detalhes: {e}")
    else:
        st.warning("Selecione um produto para calcular.")
