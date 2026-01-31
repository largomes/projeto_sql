# config_global.py - ATUALIZADO
"""
Configurações globais compartilhadas por TODAS as páginas
Fica no MESMO diretório que app.py
"""
import streamlit as st
import mysql.connector
from mysql.connector import Error
import subprocess
import time

# ============ INICIALIZAÇÃO DOS ESTADOS GLOBAIS ============
def init_global_state():
    """
    DEVE ser chamada no início do app.py
    Inicializa todos os estados compartilhados
    """
    # Banco de dados ativo
    if 'banco_ativo' not in st.session_state:
        st.session_state.banco_ativo = None
    
    # Conexão global (reutilizável)
    if 'conexao_global' not in st.session_state:
        st.session_state.conexao_global = None
    
    # Lista de bancos disponíveis (cache)
    if 'bancos_disponiveis' not in st.session_state:
        st.session_state.bancos_disponiveis = []
    
    # Banco anterior para comparação
    if 'banco_anterior' not in st.session_state:
        st.session_state.banco_anterior = None
    
    # Cache de tabelas por banco
    if 'cache_tabelas' not in st.session_state:
        st.session_state.cache_tabelas = {}

# ============ CONEXÃO INTELIGENTE ============
def verificar_docker_mysql():
    """Verifica se MySQL Docker está rodando"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mysql_fix", "--format", "{{.Status}}"],
            capture_output=True, text=True
        )
        return "Up" in result.stdout
    except:
        return False

def conectar_mysql_basico():
    """Tenta conectar ao MySQL (Docker ou XAMPP)"""
    # Primeiro, tenta conectar normalmente
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            port=3306,
            connection_timeout=5
        )
        return conexao
    except Error as e:
        st.error(f"❌ Erro conexão básica: {e}")
    
    # Se falhou, verifica Docker
    if verificar_docker_mysql():
        try:
            conexao = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                port=3306,
                connection_timeout=10
            )
            return conexao
        except Exception as e:
            st.error(f"❌ Docker rodando mas conexão falhou: {e}")
    
    return None

def get_conexao_global():
    """
    Retorna conexão ao banco ativo.
    Se não houver banco ativo, retorna conexão sem database.
    """
    # Verificar se há conexão ativa e válida
    if (st.session_state.conexao_global and 
        hasattr(st.session_state.conexao_global, 'is_connected') and
        st.session_state.conexao_global.is_connected()):
        return st.session_state.conexao_global
    
    # Se não há banco ativo, retornar conexão básica
    if not st.session_state.banco_ativo:
        try:
            conexao = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                port=3306
            )
            st.session_state.conexao_global = conexao
            return conexao
        except Exception as e:
            st.error(f"❌ Erro de conexão geral: {e}")
            return None
    
    # Criar nova conexão ao banco ativo
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=st.session_state.banco_ativo,
            port=3306
        )
        st.session_state.conexao_global = conexao
        return conexao
    except Error as e:
        st.error(f"❌ Erro ao conectar ao banco '{st.session_state.banco_ativo}': {e}")
        
        # Tentar reconectar sem database
        try:
            conexao = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                port=3306
            )
            st.session_state.conexao_global = conexao
            return conexao
        except:
            return None

# ============ FUNÇÕES PARA ACESSO GLOBAL ============
def get_banco_ativo():
    """Retorna o banco atualmente selecionado"""
    return st.session_state.get('banco_ativo')

def set_banco_ativo(nome_banco):
    """Define um novo banco ativo"""
    banco_anterior = st.session_state.banco_ativo
    st.session_state.banco_ativo = nome_banco
    st.session_state.banco_anterior = banco_anterior
    
    # Resetar conexão para forçar nova com o banco correto
    st.session_state.conexao_global = None
    
    # Limpar cache se mudou de banco
    if banco_anterior != nome_banco:
        st.session_state.cache_tabelas = {}
    
    return nome_banivo

def limpar_cache_banco():
    """Limpa cache quando muda de banco"""
    keys_to_reset = [
        'cache_tabelas', 'dados_relacoes', 'tabelas_carregadas',
        'filtros_aplicados', 'colunas_processadas', 'query_cache'
    ]
    
    for key in keys_to_reset:
        if key in st.session_state:
            if isinstance(st.session_state[key], dict):
                st.session_state[key] = {}
            elif isinstance(st.session_state[key], list):
                st.session_state[key] = []
            else:
                del st.session_state[key]
    
    # Forçar recarregamento em todas as páginas
    if 'buscar_relacoes' in st.session_state:
        st.session_state.buscar_relacoes = False
    if 'dados_carregados' in st.session_state:
        st.session_state.dados_carregados = False

def listar_bancos_disponiveis(forcar_atualizacao=False):
    """Lista todos os bancos do MySQL (com cache)"""
    if (not forcar_atualizacao and 
        st.session_state.bancos_disponiveis and 
        len(st.session_state.bancos_disponiveis) > 0):
        return st.session_state.bancos_disponiveis
    
    try:
        conexao = get_conexao_global()
        if not conexao:
            return []
        
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        todos_bancos = [b[0] for b in cursor.fetchall()]
        cursor.close()
        
        # Filtrar bancos do sistema
        bancos_usuario = [
            b for b in todos_bancos 
            if b not in ['information_schema', 'mysql', 'performance_schema', 'sys']
        ]
        
        st.session_state.bancos_disponiveis = bancos_usuario
        return bancos_usuario
        
    except Exception as e:
        st.error(f"❌ Erro ao listar bancos: {e}")
        return []

def listar_tabelas_banco(banco_nome, forcar_atualizacao=False):
    """Lista tabelas de um banco específico (com cache)"""
    # Verificar cache primeiro
    if (not forcar_atualizacao and 
        banco_nome in st.session_state.cache_tabelas and 
        st.session_state.cache_tabelas[banco_nome]):
        return st.session_state.cache_tabelas[banco_nome]
    
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=banco_nome,
            port=3306
        )
        
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")
        tabelas = [tb[0] for tb in cursor.fetchall()]
        cursor.close()
        conexao.close()
        
        # Atualizar cache
        st.session_state.cache_tabelas[banco_nome] = tabelas
        return tabelas
        
    except Exception as e:
        st.error(f"❌ Erro ao listar tabelas do banco '{banco_nome}': {e}")
        return []

def get_status_sistema():
    """Retorna status atual do sistema"""
    conexao = get_conexao_global()
    return {
        'banco_ativo': st.session_state.banco_ativo,
        'conectado': conexao and conexao.is_connected() if conexao else False,
        'total_bancos': len(st.session_state.bancos_disponiveis),
        'docker_rodando': verificar_docker_mysql()
    }

# ============ FUNÇÕES DE UTILIDADE ============
def conectar_banco_especifico(nome_banco):
    """Conecta a um banco específico e torna ativo"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=nome_banco,
            port=3306
        )
        
        set_banco_ativo(nome_banco)
        st.session_state.conexao_global = conexao
        
        # Atualizar lista de bancos
        listar_bancos_disponiveis(forcar_atualizacao=True)
        
        return conexao
    except Exception as e:
        st.error(f"❌ Erro ao conectar a '{nome_banco}': {e}")
        return None

def criar_novo_banco(nome_banco):
    """Cria um novo banco de dados"""
    try:
        conexao = get_conexao_global()
        if not conexao:
            return False
        
        cursor = conexao.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{nome_banco}`")
        conexao.commit()
        cursor.close()
        
        # Atualizar cache
        listar_bancos_disponiveis(forcar_atualizacao=True)
        
        return True
    except Exception as e:
        st.error(f"❌ Erro ao criar banco '{nome_banco}': {e}")
        return False

def obter_info_banco(banco_nome):
    """Obtém informações detalhadas do banco"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=banco_nome,
            port=3306
        )
        
        cursor = conexao.cursor()
        
        # Contar tabelas
        cursor.execute("SHOW TABLES")
        tabelas = cursor.fetchall()
        num_tabelas = len(tabelas)
        
        # Estimar tamanho
        cursor.execute("""
            SELECT SUM(data_length + index_length) as tamanho_bytes
            FROM information_schema.TABLES 
            WHERE table_schema = %s
        """, (banco_nome,))
        
        tamanho_result = cursor.fetchone()
        tamanho_bytes = tamanho_result[0] if tamanho_result[0] else 0
        
        cursor.close()
        conexao.close()
        
        # Converter tamanho
        if tamanho_bytes < 1024:
            tamanho_str = f"{tamanho_bytes} bytes"
        elif tamanho_bytes < 1024*1024:
            tamanho_str = f"{tamanho_bytes/1024:.2f} KB"
        else:
            tamanho_str = f"{tamanho_bytes/(1024*1024):.2f} MB"
        
        return {
            'nome': banco_nome,
            'tabelas': num_tabelas,
            'tamanho': tamanho_str,
            'status': '✅ Disponível'
        }
        
    except Exception as e:
        return {
            'nome': banco_nome,
            'tabelas': 0,
            'tamanho': '0 bytes',
            'status': f'❌ Erro: {str(e)[:50]}'
        }