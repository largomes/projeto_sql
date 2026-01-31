import streamlit as st
import re
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# ============ SISTEMA DE CONEXÃO ============
def conectar_banco(database=None):
    """Conecta ao MySQL usando a conexão existente ou cria nova"""
    # Primeiro, tenta usar a conexão do app.py
    if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
        conexao = st.session_state.conexao_mysql
        
        # Se pediu banco específico, tenta usar
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
    
    # Se não tem conexão no session_state, cria nova
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
        # Cria nova conexão sem banco específico para ver TODOS os bancos
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
        
        # Filtra bancos de sistema
        bancos = [b for b in todos_bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
        
        return bancos
        
    except Exception as e:
        st.error(f"Erro ao listar bancos: {e}")
        return []

def criar_banco_dados(nome_banco):
    """Cria um novo banco de dados"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conexao.cursor()
        # Usar backticks para lidar com nomes especiais
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{nome_banco}`")
        st.success(f"✅ Banco de dados '{nome_banco}' criado com sucesso!")
        cursor.close()
        conexao.close()
        return True
    except Error as e:
        st.error(f"❌ Erro ao criar banco: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        return False

def excluir_banco_dados(nome_banco):
    """Exclui um banco de dados"""
    try:
        # Verificação de segurança
        if nome_banco in ['information_schema', 'mysql', 'performance_schema', 'sys']:
            st.error("❌ Não é possível excluir bancos de dados do sistema!")
            return False
            
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conexao.cursor()
        # Usar backticks para lidar com nomes especiais
        cursor.execute(f"DROP DATABASE IF EXISTS `{nome_banco}`")
        st.success(f"✅ Banco de dados '{nome_banco}' excluído com sucesso!")
        cursor.close()
        conexao.close()
        return True
    except Error as e:
        st.error(f"❌ Erro ao excluir banco: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        return False

# ============ PÁGINAS DE FUNCIONALIDADE ============
def pagina_listar_bancos():
    """Página para listar todos os bancos de dados"""
    st.subheader("📋 Bancos de Dados Disponíveis")
    
    # Atualizar lista de bancos
    if st.button("🔄 Atualizar Lista", key="btn_atualizar_lista"):
        st.rerun()
    
    bancos = listar_bancos()
    
    if bancos:
        st.markdown(f"**Total de bancos encontrados:** {len(bancos)}")
        
        # Exibir em formato de tabela
        df_bancos = pd.DataFrame(bancos, columns=["Nome do Banco"])
        st.dataframe(df_bancos, use_container_width=True, hide_index=True)
        
        # Mostrar informações extras
        with st.expander("📊 Estatísticas"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Bancos", len(bancos))
            with col2:
                st.metric("Bancos do Sistema", 4)  # Fixo: information_schema, mysql, performance_schema, sys
    else:
        st.info("📭 Nenhum banco de dados encontrado ou ocorreu um erro ao listar.")

def pagina_criar_novo_banco():
    """Página para criar um novo banco de dados"""
    st.subheader("🆕 Criar Novo Banco de Dados")
    
    nome_banco = st.text_input(
        "Nome do Banco de Dados",
        placeholder="Digite o nome do banco...",
        help="Use apenas letras, números e underscores. Evite caracteres especiais.",
        key="input_nome_banco_criar"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        criar_button = st.button("✅ Criar Banco", use_container_width=True, key="btn_criar_banco")
    
    with col2:
        limpar_button = st.button("🧹 Limpar Campo", use_container_width=True, key="btn_limpar_campo")
    
    with col3:
        # Botão ajustado - mostra mensagem em vez de tentar mudar de página
        ver_existentes = st.button("📋 Ver Bancos Existentes", use_container_width=True, key="btn_ver_existentes")
    
    # Processar botão Criar
    if criar_button and nome_banco:
        # Validação do nome
        if not re.match(r'^[a-zA-Z0-9_]+$', nome_banco):
            st.warning("⚠️ Use apenas letras, números e underscores no nome.")
        elif len(nome_banco) < 3:
            st.warning("⚠️ O nome deve ter pelo menos 3 caracteres.")
        elif len(nome_banco) > 64:
            st.warning("⚠️ O nome deve ter no máximo 64 caracteres.")
        else:
            # Verificar se já existe
            bancos_existentes = listar_bancos()
            if nome_banco in bancos_existentes:
                st.warning(f"⚠️ O banco '{nome_banco}' já existe!")
            else:
                if criar_banco_dados(nome_banco):
                    st.success(f"Banco '{nome_banco}' criado com sucesso! Use o botão 'Limpar Campo' para criar outro.")
    
    # Processar botão Limpar
    if limpar_button:
        # Usando session_state para limpar
        st.session_state["input_nome_banco_criar"] = ""
        st.rerun()
    
    # Processar botão Ver Existentes
    if ver_existentes:
        st.info("📋 **Bancos disponíveis:**")
        bancos = listar_bancos()
        if bancos:
            for banco in bancos:
                st.write(f"- {banco}")
        else:
            st.write("Nenhum banco encontrado.")
    
    # Dicas de uso
    with st.expander("💡 Dicas para nomes de bancos"):
        st.markdown("""
        - Use apenas letras (a-z, A-Z), números (0-9) e underscore (_)
        - Não use espaços, acentos ou caracteres especiais
        - O nome deve começar com uma letra
        - Exemplos válidos: `meubanco`, `banco_2024`, `sistema_vendas`
        - Exemplos inválidos: `meu-banco`, `banco teste`, `sistema@vendas`
        """)

def pagina_excluir_banco():
    """Página para excluir bancos de dados"""
    st.subheader("🗑️ Excluir Banco de Dados")
    
    # Lista de bancos disponíveis para exclusão
    bancos = listar_bancos()
    
    if bancos:
        st.warning("⚠️ **Atenção:** Esta ação é irreversível! Todos os dados serão perdidos.")
        
        banco_selecionado = st.selectbox(
            "Selecione o banco para excluir:",
            bancos,
            index=None,
            placeholder="Escolha um banco...",
            key="select_excluir_banco"
        )
        
        # Confirmação de segurança
        if banco_selecionado:
            st.error(f"**Você está prestes a excluir:** `{banco_selecionado}`")
            
            # Requer confirmação explícita
            confirmacao = st.text_input(
                f"Digite '{banco_selecionado}' para confirmar:",
                placeholder=f"Digite {banco_selecionado}...",
                key="input_confirmar_exclusao"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                excluir_disabled = confirmacao != banco_selecionado
                if st.button("❌ Excluir Banco", 
                           use_container_width=True, 
                           disabled=excluir_disabled,
                           key="btn_excluir_banco"):
                    if excluir_banco_dados(banco_selecionado):
                        # Recarregar a página para atualizar a lista
                        st.rerun()
            with col2:
                if st.button("🔙 Cancelar", 
                           use_container_width=True,
                           key="btn_cancelar_exclusao"):
                    # Recarregar para limpar seleção
                    st.rerun()
    else:
        st.info("📭 Nenhum banco de dados disponível para exclusão.")

# ============ PÁGINA PRINCIPAL ============
def pagina_criar_banco():
    """Página principal do construtor SQL"""
    
    st.title("🗄️ Gerenciador de Bancos de Dados SQL")
    st.markdown("Gerencie seus bancos de dados MySQL de forma simples e intuitiva.")
    
    # Menu de navegação
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📋 Listar Bancos", "🆕 Criar Banco", "🗑️ Excluir Banco"])
    
    with tab1:
        pagina_listar_bancos()
    
    with tab2:
        pagina_criar_novo_banco()
    
    with tab3:
        pagina_excluir_banco()
    
    # Rodapé com informações
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🛠️ Gerenciador MySQL")
    with col2:
        st.caption("📊 Streamlit + Python")
    with col3:
        # Mostrar conexão atual se disponível
        if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
            conexao = st.session_state.conexao_mysql
            st.caption(f"🔗 {conexao.database or 'Sem banco selecionado'}")
        else:
            st.caption("🔌 Sem conexão ativa")

# ============ EXECUÇÃO DIRETA ============
if __name__ == "__main__":
    st.set_page_config(
        page_title="Gerenciador de Bancos de Dados SQL", 
        layout="wide",
        page_icon="🗄️"
    )
    
    # Inicializar session state se necessário
    if "conexao_mysql" not in st.session_state:
        st.session_state.conexao_mysql = None
    
    # Testar conexão básica
    try:
        conexao_test = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        conexao_test.close()
        st.session_state.conexao_disponivel = True
    except Exception as e:
        st.session_state.conexao_disponivel = False
        st.error(f"⚠️ Não foi possível conectar ao MySQL. Erro: {e}")
        st.info("Certifique-se que:")
        st.info("1. O MySQL está rodando (XAMPP/WAMP/LAMP ou serviço MySQL)")
        st.info("2. As credenciais estão corretas (usuário: root, sem senha)")
        st.info("3. O host é 'localhost'")
        st.stop()
    
    pagina_criar_banco()