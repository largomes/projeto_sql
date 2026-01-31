import streamlit as st
import mysql.connector
from mysql.connector import Error

# ============ FUNÇÕES BÁSICAS ============
def listar_bancos_local():
    """Lista bancos do MySQL"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        todos_bancos = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conexao.close()
        
        # Filtrar bancos do sistema
        bancos = [b for b in todos_bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
        return bancos
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return []
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return []

# ============ SELETOR DE BANCO SIMPLES ============
def seletor_banco(titulo="🏦 Selecionar Banco de Dados"):
    """
    Componente SIMPLES para seleção de banco
    Retorna: banco_selecionado
    """
    # Listar bancos disponíveis
    bancos = listar_bancos_local()
    
    if not bancos:
        st.error("❌ Nenhum banco de dados encontrado!")
        st.info("""
        Verifique:
        1. MySQL está rodando (XAMPP ou Docker)
        2. Há bancos de dados criados
        3. Credenciais estão corretas (root/sem senha)
        """)
        return None
    
    # Inicializar estado
    if "banco_ativo" not in st.session_state:
        st.session_state.banco_ativo = None
    
    # Container para seleção
    with st.container(border=True):
        st.markdown(f"### {titulo}")
        
        # Mostrar lista de bancos encontrados
        st.info(f"📁 **Encontrados {len(bancos)} banco(s):** {', '.join(bancos[:3])}{'...' if len(bancos) > 3 else ''}")
        
        col_selecao, col_botao = st.columns([3, 1])
        
        with col_selecao:
            # Determinar índice padrão
            default_index = 0
            if st.session_state.banco_ativo and st.session_state.banco_ativo in bancos:
                default_index = bancos.index(st.session_state.banco_ativo)
            
            banco_selecionado = st.selectbox(
                "Escolha o banco para trabalhar:",
                bancos,
                index=default_index,
                label_visibility="collapsed",
                key="select_banco_trabalho"
            )
        
        with col_botao:
            st.write("⠀")  # Espaçador
            if st.button("✅ Selecionar", type="primary", use_container_width=True):
                # Salvar no estado
                st.session_state.banco_ativo = banco_selecionado
                st.success(f"✅ Banco '{banco_selecionado}' selecionado!")
                st.rerun()
    
    # Mostrar banco ativo atual
    if st.session_state.banco_ativo:
        st.markdown("---")
        st.success(f"**🎯 Banco atual para trabalho:** **{st.session_state.banco_ativo}**")
    
    return st.session_state.banco_ativo

# ============ VERSÃO MINI (para sidebar) ============
def seletor_banco_mini():
    """Versão compacta para sidebar"""
    bancos = listar_bancos_local()
    
    if not bancos:
        st.error("Sem bancos")
        return None
    
    # Seletor simples
    banco_selecionado = st.selectbox(
        "Banco de trabalho:",
        bancos,
        index=bancos.index(st.session_state.banco_ativo) if st.session_state.banco_ativo in bancos else 0,
        key="sidebar_banco"
    )
    
    # Atualizar se mudou
    if banco_selecionado != st.session_state.get("banco_ativo"):
        st.session_state.banco_ativo = banco_selecionado
        st.rerun()
    
    return st.session_state.banco_ativo

# ============ PÁGINA DE LISTAGEM DE BANCOS ============
def pagina_listar_bancos():
    """Página completa para listar e selecionar bancos"""
    st.title("🗄️ Bancos de Dados Disponíveis")
    
    # Opções de ação
    col_atualizar, col_criar, col_status = st.columns(3)
    
    with col_atualizar:
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.rerun()
    
    with col_criar:
        if st.button("➕ Criar Banco", use_container_width=True):
            st.session_state.criando_banco = True
    
    with col_status:
        if st.session_state.get("banco_ativo"):
            st.success(f"✅ {st.session_state.banco_ativo}")
        else:
            st.warning("⚠️ Nenhum selecionado")
    
    st.markdown("---")
    
    # Listar bancos
    bancos = listar_bancos_local()
    
    if not bancos:
        st.info("📭 Nenhum banco de dados encontrado.")
        
        # Opção para criar
        if st.session_state.get("criando_banco", False):
            with st.form("criar_banco_form"):
                nome = st.text_input("Nome do novo banco:", placeholder="meu_banco")
                
                col1, col2 = st.columns(2)
                with col1:
                    criar = st.form_submit_button("✅ Criar", type="primary")
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar")
                
                if criar and nome:
                    try:
                        conexao = mysql.connector.connect(
                            host="localhost",
                            user="root",
                            password=""
                        )
                        cursor = conexao.cursor()
                        cursor.execute(f"CREATE DATABASE `{nome}`")
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        
                        st.success(f"✅ Banco '{nome}' criado com sucesso!")
                        st.session_state.criando_banco = False
                        st.session_state.banco_ativo = nome
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao criar banco: {e}")
                
                if cancelar:
                    st.session_state.criando_banco = False
                    st.rerun()
        
        return
    
    # Mostrar bancos em cards
    st.subheader(f"📁 Bancos encontrados: {len(bancos)}")
    
    # Layout de cards
    for i in range(0, len(bancos), 3):  # 3 colunas
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(bancos):
                banco = bancos[i + j]
                is_ativo = (banco == st.session_state.get("banco_ativo"))
                
                with cols[j]:
                    with st.container(border=True, height=200):
                        # Título
                        if is_ativo:
                            st.markdown(f"### 🎯 {banco}")
                            st.success("**ATIVO**")
                        else:
                            st.markdown(f"### 📁 {banco}")
                        
                        # Botão de ação
                        if not is_ativo:
                            if st.button("Usar Este", key=f"usar_{banco}", use_container_width=True):
                                st.session_state.banco_ativo = banco
                                st.rerun()
                        else:
                            st.button("✅ Em Uso", disabled=True, use_container_width=True)
    
    # Seletor rápido abaixo
    st.markdown("---")
    st.subheader("🎯 Seleção Rápida")
    
    banco_atual = seletor_banco()
    
    if banco_atual:
        st.balloons()
        st.success(f"Pronto! Todas as operações usarão o banco: **{banco_atual}**")

# ============ TESTE RÁPIDO ============
if __name__ == "__main__":
    st.set_page_config(page_title="Seletor de Bancos", layout="wide")
    
    # Testar seletor
    banco = seletor_banco()
    st.write("**Banco retornado:**", banco)
    
    # Mostrar estado atual
    with st.expander("🔧 Estado da sessão"):
        st.write(st.session_state)
    
    # Botão para página completa
    if st.button("📋 Ver Página Completa de Bancos"):
        pagina_listar_bancos()