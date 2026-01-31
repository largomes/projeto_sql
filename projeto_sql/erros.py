# diagnostico.py - CRIE ESTE ARQUIVO SEPARADO
import os
import sys
import streamlit as st

st.set_page_config(page_title="Diagnóstico", layout="wide")
st.title("🔍 Diagnóstico do Sistema MySQL")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Estrutura de Arquivos")
    st.write("**Diretório atual:**", os.getcwd())
    st.write("---")
    
    arquivos = sorted(os.listdir("."))
    for arquivo in arquivos:
        tamanho = os.path.getsize(arquivo) if os.path.isfile(arquivo) else 0
        st.write(f"- `{arquivo}` ({tamanho} bytes)")

with col2:
    st.subheader("📦 Módulos Necessários")
    
    modulos_necessarios = {
        "app.py": "Arquivo principal",
        "Formularios.py": "Formulários CRUD",
        "query_editor.py": "Editor SQL",
        "manual.py": "Documentação",
        "exercicios.py": "Exercícios",
        "criar_banco.py": "Criar bancos",
        "criar_tabelas.py": "Criar tabelas"
    }
    
    for modulo, descricao in modulos_necessarios.items():
        existe = os.path.exists(modulo)
        status = "✅" if existe else "❌"
        cor = "green" if existe else "red"
        
        st.markdown(f"<span style='color:{cor}'>{status} **{modulo}**</span> - {descricao}", 
                   unsafe_allow_html=True)
    
    st.subheader("🐍 Ambiente Python")
    st.code(f"Python {sys.version}")
    
    st.subheader("📦 Pacotes Instalados")
    try:
        import mysql.connector
        st.success("✅ mysql.connector-python")
    except:
        st.error("❌ mysql.connector-python (pip install mysql-connector-python)")
    
    try:
        import pandas
        st.success("✅ pandas")
    except:
        st.error("❌ pandas (pip install pandas)")

st.markdown("---")
st.subheader("🔧 Comandos para Correção")

st.code("""
# Se faltar pacotes:
pip install mysql-connector-python pandas streamlit

# Se faltar arquivos:
# Copie os arquivos do seu projeto anterior para este diretório

# Para criar módulos básicos:
echo "# Módulo placeholder" > manual.py
echo "# Módulo placeholder" > exercicios.py
""")

if st.button("🔄 Verificar Novamente"):
    st.rerun()