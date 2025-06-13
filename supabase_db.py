import os
from supabase import create_client, Client


class SupabaseError(Exception):
    """Exceção customizada para erros do Supabase."""
    pass


class SupabaseDB:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")
        if not self.url or not self.key:
            raise SupabaseError(
                "Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não configuradas.")
        try:
            self.client: Client = create_client(self.url, self.key)
        except Exception as e:
            raise SupabaseError(f"Erro ao inicializar cliente Supabase: {e}")

    def _execute_query(self, query_func, error_message):
        try:
            response = query_func().execute()
            if response.data is None:
                return []
            return response.data
        except Exception as e:
            raise SupabaseError(f"{error_message}: {e}")

    # Métodos para Produtos (produtos_custos)
    def get_all_produtos(self):
        return self._execute_query(lambda: self.client.from_("produtos_custos").select("*"), "Erro ao buscar produtos")

    def add_produto(self, produto_data):
        return self._execute_query(lambda: self.client.from_("produtos_custos").insert(produto_data), "Erro ao adicionar produto")

    def update_produto(self, produto_id, produto_data):
        return self._execute_query(lambda: self.client.from_("produtos_custos").update(produto_data).eq("id", produto_id), "Erro ao atualizar produto")

    def delete_produto(self, produto_id):
        return self._execute_query(lambda: self.client.from_("produtos_custos").delete().eq("id", produto_id), "Erro ao deletar produto")

    # Métodos para Variáveis de Custos (variaveis_custos)
    def get_all_variaveis(self):
        return self._execute_query(lambda: self.client.from_("variaveis_custos").select("*"), "Erro ao buscar variáveis de custos")

    def add_variavel(self, variavel_data):
        return self._execute_query(lambda: self.client.from_("variaveis_custos").insert(variavel_data), "Erro ao adicionar variável de custo")

    def update_variavel(self, variavel_id, variavel_data):
        return self._execute_query(lambda: self.client.from_("variaveis_custos").update(variavel_data).eq("id", variavel_id), "Erro ao atualizar variável de custo")

    def delete_variavel(self, variavel_id):
        return self._execute_query(lambda: self.client.from_("variaveis_custos").delete().eq("id", variavel_id), "Erro ao deletar variável de custo")

    # Métodos para Variáveis da Calculadora (variaveis_calc)
    def get_all_variaveis_calc(self):
        return self._execute_query(lambda: self.client.from_("variaveis_calc").select("*"), "Erro ao buscar variáveis da calculadora")

    def add_variavel_calc(self, variavel_data):
        return self._execute_query(lambda: self.client.from_("variaveis_calc").insert(variavel_data), "Erro ao adicionar variável da calculadora")

    def update_variavel_calc(self, variavel_id, variavel_data):
        return self._execute_query(lambda: self.client.from_("variaveis_calc").update(variavel_data).eq("id", variavel_id), "Erro ao atualizar variável da calculadora")

    def delete_variavel_calc(self, variavel_id):
        return self._execute_query(lambda: self.client.from_("variaveis_calc").delete().eq("id", variavel_id), "Erro ao deletar variável da calculadora")

    # NOVOS Métodos para Categorias de Produtos (categorias_produtos)
    def get_all_categorias_produtos(self):
        return self._execute_query(lambda: self.client.from_("categorias_produtos").select("*"), "Erro ao buscar categorias de produtos")

    def add_categoria_produto(self, categoria_data):
        return self._execute_query(lambda: self.client.from_("categorias_produtos").insert(categoria_data), "Erro ao adicionar categoria de produto")

    def delete_categoria_produto(self, categoria_id):
        return self._execute_query(lambda: self.client.from_("categorias_produtos").delete().eq("id", categoria_id), "Erro ao deletar categoria de produto")

    # NOVOS Métodos para Categorias de Variáveis (categorias_variaveis)
    def get_all_categorias_variaveis(self):
        return self._execute_query(lambda: self.client.from_("categorias_variaveis").select("*"), "Erro ao buscar categorias de variáveis")

    def add_categoria_variavel(self, categoria_data):
        return self._execute_query(lambda: self.client.from_("categorias_variaveis").insert(categoria_data), "Erro ao adicionar categoria de variável")

    def delete_categoria_variavel(self, categoria_id):
        return self._execute_query(lambda: self.client.from_("categorias_variaveis").delete().eq("id", categoria_id), "Erro ao deletar categoria de variável")
