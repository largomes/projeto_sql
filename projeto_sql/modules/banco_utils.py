# banco_utils.py - ARQUIVO SEPARADO
"""
Utilitários para gerenciamento de banco de dados
SEM dependências circulares
"""
import streamlit as st
import mysql.connector

def listar_bancos():
    """Lista todos os bancos disponíveis"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        bancos = [b[0] for b in cursor.fetchall()]
        cursor.close()
        conexao.close()
        
        return [b for b in bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
    except:
        return []

def verificar_banco_selecionado():
    """Verifica se há banco selecionado, mostra seletor se não houver"""
    # Inicializar se não existir
    if "banco_ativo" not in st.session_state:
        st.session_state.banco_ativo = None
    
    # Se já tem banco selecionado, retorna
    if st.session_state.banco_ativo:
        return st.session_state.banco_ativo
    
    # Se não tem, mostra seletor
    st.warning("⚠️ Selecione um banco de dados para continuar")
    
    bancos = listar_bancos()
    
    if not bancos:
        st.error("❌ Nenhum banco encontrado!")
        st.info("Crie um banco primeiro na página 'Criar Banco'")
        return None
    
    # Seletor simples
    banco = st.selectbox("Banco de trabalho:", bancos)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Usar este banco", type="primary"):
            st.session_state.banco_ativo = banco
            st.rerun()
    
    with col2:
        if st.button("📋 Ver todos os bancos"):
            st.session_state.pagina = "listar_bancos"
            st.rerun()
    
    return None

def get_banco_ativo():
    """Retorna o banco ativo atual"""
    return st.session_state.get("banco_ativo")

def set_banco_ativo(banco_nome):
    """Define um novo banco ativo"""
    st.session_state.banco_ativo = banco_nome
    return banco_nome