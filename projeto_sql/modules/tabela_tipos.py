# modules/tabela_tipos.py
import streamlit as st
import pandas as pd
from .tabela_utils import TIPOS_DADOS_ACCESS

def mostrar_tabela_tipos():
    """Mostra a tabela de tipos de dados igual à imagem"""
    
    st.markdown("""
    <style>
    .container-tipos-dados {
        border: 2px solid #E5E7EB;
        border-radius: 8px;
        padding: 20px;
        background-color: #FFFFFF;
        margin: 15px 0;
    }
    .titulo-tabela-tipos {
        font-size: 20px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #3B82F6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container principal
    st.markdown('<div class="container-tipos-dados">', unsafe_allow_html=True)
    st.markdown('<div class="titulo-tabela-tipos">📋 Tipos de Dados - Microsoft Access / MySQL</div>', unsafe_allow_html=True)
    
    # Criar DataFrame
    df_access = pd.DataFrame(TIPOS_DADOS_ACCESS["Tipos Access"])
    df_mysql = pd.DataFrame(TIPOS_DADOS_ACCESS["Equivalente MySQL"])
    
    df_final = pd.DataFrame({
        "Código": df_access["Código"],
        "Tipo Access": df_access["Tipo de dados"],
        "Tipo MySQL": df_mysql["Tipo de dados"]
    })
    
    # Exibir tabela
    st.dataframe(
        df_final,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Código": st.column_config.NumberColumn("Código", width="small"),
            "Tipo Access": st.column_config.TextColumn("Tipo Access", width="medium"),
            "Tipo MySQL": st.column_config.TextColumn("Tipo MySQL", width="medium")
        }
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Conversor prático
    with st.expander("🔄 Conversor Prático", expanded=False):
        tipo_access = st.selectbox(
            "Selecione tipo Access:",
            options=[t["Tipo de dados"] for t in TIPOS_DADOS_ACCESS["Tipos Access"]]
        )
        
        if tipo_access:
            idx = [t["Tipo de dados"] for t in TIPOS_DADOS_ACCESS["Tipos Access"]].index(tipo_access)
            tipo_mysql = TIPOS_DADOS_ACCESS["Equivalente MySQL"][idx]["Tipo de dados"]
            st.info(f"**{tipo_access}** → **{tipo_mysql}**")