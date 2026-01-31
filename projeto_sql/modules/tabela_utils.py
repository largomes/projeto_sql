# modules/tabela_utils.py
import mysql.connector
from mysql.connector import Error
import streamlit as st

# ============ DADOS DOS TIPOS (DA IMAGEM) ============
TIPOS_DADOS_ACCESS = {
    "Tipos Access": [
        {"Código": 1, "Tipo de dados": "Numeração Automática"},
        {"Código": 2, "Tipo de dados": "Texto"},
        {"Código": 3, "Tipo de dados": "Memorando"},
        {"Código": 4, "Tipo de dados": "Número"},
        {"Código": 5, "Tipo de dados": "Data/Hora"},
        {"Código": 6, "Tipo de dados": "Moeda"},
        {"Código": 7, "Tipo de dados": "Sim/Não"},
        {"Código": 8, "Tipo de dados": "Objeto OLE"},
        {"Código": 9, "Tipo de dados": "Hiperlink"},
        {"Código": 10, "Tipo de dados": "Anexo"},
        {"Código": 11, "Tipo de dados": "Calculado"},
        {"Código": 12, "Tipo de dados": "Assistente de pesquisa"}
    ],
    "Equivalente MySQL": [
        {"Código": 1, "Tipo de dados": "INT AUTO_INCREMENT PRIMARY KEY"},
        {"Código": 2, "Tipo de dados": "VARCHAR(255)"},
        {"Código": 3, "Tipo de dados": "TEXT"},
        {"Código": 4, "Tipo de dados": "INT / DECIMAL / FLOAT"},
        {"Código": 5, "Tipo de dados": "DATETIME / TIMESTAMP / DATE"},
        {"Código": 6, "Tipo de dados": "DECIMAL(10,2)"},
        {"Código": 7, "Tipo de dados": "BOOLEAN / TINYINT(1)"},
        {"Código": 8, "Tipo de dados": "BLOB / LONGBLOB"},
        {"Código": 9, "Tipo de dados": "VARCHAR(500)"},
        {"Código": 10, "Tipo de dados": "BLOB / LONGBLOB"},
        {"Código": 11, "Tipo de dados": "GENERATED COLUMN"},
        {"Código": 12, "Tipo de dados": "FOREIGN KEY (Relacionamento)"}
    ]
}

def converter_tipo_access_para_mysql(tipo_access):
    """Converte tipo do Access para MySQL"""
    conversao = {
        "Numeração Automática": "INT AUTO_INCREMENT",
        "Texto": "VARCHAR(255)",
        "Memorando": "TEXT",
        "Número": "INT",
        "Data/Hora": "DATETIME",
        "Moeda": "DECIMAL(10,2)",
        "Sim/Não": "BOOLEAN",
        "Objeto OLE": "BLOB",
        "Hiperlink": "VARCHAR(500)",
        "Anexo": "LONGBLOB",
        "Calculado": "VARCHAR(255)",
        "Assistente de pesquisa": "INT"
    }
    return conversao.get(tipo_access, "VARCHAR(255)")

def conectar_banco(database=None):
    """Conecta ao MySQL usando a conexão existente ou cria nova"""
    if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
        conexao = st.session_state.conexao_mysql
        if database and database != conexao.database:
            try:
                cursor = conexao.cursor()
                cursor.execute(f"USE {database}")
                cursor.close()
                conexao.database = database
                return conexao
            except:
                pass
        return conexao
    
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=database
        )
        return conexao
    except Error as e:
        st.error(f"Erro: {e}")
        return None

def listar_bancos():
    """Lista todos os bancos disponíveis"""
    try:
        conexao_temp = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexao_temp.cursor()
        cursor.execute("SHOW DATABASES")
        todos_bancos = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conexao_temp.close()
        
        bancos = [b for b in todos_bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
        return bancos
    except Exception as e:
        st.error(f"Erro ao listar bancos: {e}")
        return []



def listar_tabelas(database):
    """Lista todas as tabelas de um banco específico - VERSÃO SEGURA"""
    try:
        conexao = conectar_banco(database)
        if conexao:
            cursor = conexao.cursor()
            cursor.execute("SHOW TABLES")
            tabelas = cursor.fetchall()
            cursor.close()
            # Garantir que retorna strings
            return [str(tabela[0]) for tabela in tabelas]
        return []
    except Exception as e:
        st.error(f"Erro ao listar tabelas: {e}")
        return []

def listar_colunas_tabela(database, tabela):
    """Lista colunas de uma tabela - VERSÃO SEGURA"""
    try:
        conexao = conectar_banco(database)
        if conexao:
            cursor = conexao.cursor()
            cursor.execute(f"DESCRIBE `{tabela}`")
            colunas = cursor.fetchall()
            cursor.close()
            # Converter todos os valores para string para evitar erros de tipo
            return [(str(col[0]), str(col[1]), str(col[2]), 
                     str(col[3]), str(col[4]) if col[4] is not None else "", 
                     str(col[5]) if len(col) > 5 else "") 
                    for col in colunas]
    except Exception as e:
        st.error(f"Erro ao listar colunas: {e}")
        return []