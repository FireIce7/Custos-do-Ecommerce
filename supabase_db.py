import streamlit as st
from supabase import create_client
from supabase.client import ClientOptions

def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    opts = ClientOptions(schema="public")  # força usar o public
    return create_client(url, key, options=opts)
