import math
import operator
from textos import TEXTOS
import streamlit as st
from supabase_db import SupabaseError


def evaluate_formula(formula: str, all_variables: dict, all_products: dict, evaluated_products: dict = None):
    if evaluated_products is None:
        evaluated_products = {}

    # Prevenir recursão infinita
    if formula in evaluated_products:
        return evaluated_products[formula]  # Retorna o valor já calculado

    # Criar um dicionário de valores para avaliação da fórmula
    # Inclui variáveis e produtos já avaliados
    context = {**all_variables, **evaluated_products}

    # Substituir nomes de variáveis/produtos na fórmula pelos seus valores
    formula_to_evaluate = formula
    for name, value in context.items():
        # Garante que a substituição seja para o nome completo da variável/produto
        # e não para substrings (ex: 'prod' em 'produto')
        formula_to_evaluate = formula_to_evaluate.replace(name, str(value))

    try:
        # Avaliar a fórmula
        # ATENÇÃO: eval() pode ser perigoso se a entrada não for controlada.
        # Para este caso, assumimos que as fórmulas são inseridas por usuários confiáveis.
        result = eval(formula_to_evaluate)
        return result
    except Exception as e:
        raise ValueError(f"Erro ao avaliar a fórmula '{formula}': {e}")


def calculate_product_cost(product_name: str, all_products: list, all_variables: list, evaluated_products: dict = None):
    if evaluated_products is None:
        evaluated_products = {}

    if product_name in evaluated_products:
        return evaluated_products[product_name]

    product = next(
        (p for p in all_products if p["nome"] == product_name), None)
    if not product:
        raise ValueError(f"Produto '{product_name}' não encontrado.")

    formula = product["formula"]

    # Marcar o produto como em avaliação para detectar dependências circulares
    evaluated_products[product_name] = "_EVALUATING_"

    # Dicionário de variáveis para a avaliação
    variables_dict = {v["nome"]: v["custo"] for v in all_variables}

    # Identificar produtos na fórmula
    # Isso é uma simplificação. Uma análise de AST seria mais robusta.
    # Por enquanto, assumimos que nomes de produtos/variáveis não se sobrepõem
    # e são palavras completas.
    sub_product_costs = {}
    for p in all_products:
        if p["nome"] != product_name and p["nome"] in formula:
            if evaluated_products.get(p["nome"]) == "_EVALUATING_":
                raise ValueError(f"Dependência circular detectada: {product_name} -> {p["nome"]}")
            sub_product_costs[p["nome"]] = calculate_product_cost(
                p["nome"], all_products, all_variables, evaluated_products)

    # Combinar variáveis e custos de sub-produtos para avaliação
    evaluation_context = {**variables_dict, **sub_product_costs}

    # Substituir nomes na fórmula pelos seus valores
    resolved_formula = formula
    for name, value in evaluation_context.items():
        resolved_formula = resolved_formula.replace(name, str(value))

    try:
        cost = eval(resolved_formula)
        evaluated_products[product_name] = cost
        return cost
    except Exception as e:
        raise ValueError(
            f"Erro ao calcular custo para '{product_name}' com fórmula '{formula}': {e}")


def calcular_custo(supabase_db):
    st.title("Calcular Custo de Produto")

    try:
        produtos = supabase_db.get_all_produtos()
        # Alterado para usar get_all_variaveis_calc() para a calculadora
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
