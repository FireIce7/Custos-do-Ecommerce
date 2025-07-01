import logging
from typing import Optional
import streamlit as st
from supabase import create_client
from supabase.client import ClientOptions, Client as SupabaseClient

# Configura logger para registrar erros e debugging
logger = logging.getLogger(__name__)

# Variável global para singleton do cliente Supabase
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Retorna um cliente Supabase singleton, inicializando-o apenas na primeira chamada.
    Usa st.secrets['SUPABASE_URL'] e st.secrets['SUPABASE_KEY'] para configuração.

    Raises:
        RuntimeError: Se SUPABASE_URL ou SUPABASE_KEY não estiverem configurados em st.secrets.
    """
    global _supabase_client
    if _supabase_client is None:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError(
                "Configure SUPABASE_URL e SUPABASE_KEY em st.secrets.")
        try:
            # força uso do esquema 'public'
            opts = ClientOptions(schema="public")
            _supabase_client = create_client(url, key, options=opts)
        except Exception:
            logger.exception("Falha ao instanciar SupabaseClient")
            st.error("Erro de conexão com o banco de dados.")
            raise
    return _supabase_client


def fetch_table(table_name: str, **filters: object) -> list[dict]:
    """
    Realiza consulta genérica em uma tabela do Supabase.

    Args:
        table_name: Nome da tabela no Supabase.
        **filters: Filtros a serem aplicados na consulta (igualdade exata).

    Returns:
        Lista de registros como dicionários.
    """
    sb = get_supabase_client()
    query = sb.table(table_name).select("*")
    for column, value in filters.items():
        query = query.eq(column, value)
    try:
        res = query.execute()
        if res.error:
            logger.error(
                f"Erro Supabase ao buscar {table_name}: {res.error.message}")
            st.error(f"Não foi possível buscar {table_name}.")
            return []
        return res.data or []
    except Exception:
        logger.exception(f"Exceção ao executar consulta em {table_name}")
        st.error(f"Erro ao executar consulta em {table_name}.")
        return []
