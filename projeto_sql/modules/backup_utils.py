# modules/backup_utils.py
"""
Utilitários para o sistema de backup
Inclui funções para gerenciar chaves únicas
"""
import streamlit as st
import hashlib
import time
import random

def get_backup_session_id():
    """Obtém ou cria um ID único para a sessão de backup"""
    if "backup_session_id" not in st.session_state:
        st.session_state.backup_session_id = random.randint(10000, 99999)
    return st.session_state.backup_session_id

def backup_key(base_name):
    """
    Gera uma chave única para elementos do backup
    
    Args:
        base_name: Nome base da chave (ex: "backup_select")
    
    Returns:
        Chave única no formato: "backup_select_12345"
    """
    session_id = get_backup_session_id()
    return f"{base_name}_{session_id}"

def reset_backup_keys():
    """Reseta as chaves do backup para evitar conflitos"""
    if "backup_session_id" in st.session_state:
        del st.session_state.backup_session_id
    
    # Remove outras chaves relacionadas ao backup
    keys_to_remove = [
        key for key in st.session_state.keys() 
        if 'backup' in key.lower() or 'select' in key.lower() # pyright: ignore[reportAttributeAccessIssue]
    ]
    
    for key in keys_to_remove:
        try:
            del st.session_state[key]
        except:
            pass

def generate_unique_id(prefix=""):
    """Gera um ID único para uso geral"""
    timestamp = str(time.time())
    unique_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"{prefix}_{unique_hash}" if prefix else unique_hash
