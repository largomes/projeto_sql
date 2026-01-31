# app.py - VERSÃO FIX COM DOCKER E TODOS SEUS MÓDULOS
import streamlit as st
import mysql.connector
import pandas as pd
import os
import subprocess
import time
from datetime import datetime

# ============ CONFIGURAÇÃO ============
st.set_page_config(
    page_title="MySQL System - Docker Fix",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ SISTEMA DOCKER MYSQL ============
def iniciar_mysql_docker():
    """Inicia MySQL via Docker (substitui XAMPP)"""
    try:
        # Verificar se Docker está instalado
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            st.error("❌ Docker não está instalado!")
            return False
        
        # Parar container existente
        subprocess.run(["docker", "stop", "mysql_fix"], capture_output=True)
        subprocess.run(["docker", "rm", "mysql_fix"], capture_output=True)
        
        # Iniciar novo container
        cmd = [
            "docker", "run", "-d",
            "--name", "mysql_fix",
            "-p", "3306:3306",
            "-e", "MYSQL_ROOT_PASSWORD=",
            "-e", "MYSQL_ALLOW_EMPTY_PASSWORD=yes",
            "-v", "mysql_fix_data:/var/lib/mysql",
            "mysql:8.0"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            st.success("✅ MySQL Docker iniciado! Aguarde 15 segundos...")
            time.sleep(15)  # Aguardar MySQL inicializar
            return True
        else:
            st.error(f"❌ Erro: {result.stderr}")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro Docker: {e}")
        return False

def verificar_mysql_docker():
    """Verifica se MySQL Docker está rodando"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mysql_fix", "--format", "{{.Status}}"],
            capture_output=True, text=True
        )
        return "Up" in result.stdout
    except:
        return False

# ============ CONEXÃO INTELIGENTE ============
def conectar_mysql():
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
    except:
        pass
    
    # Se falhou, verifica Docker
    if verificar_mysql_docker():
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

def get_conexao():
    """Obtém conexão com tratamento de erro"""
    if "conexao_mysql" not in st.session_state:
        st.session_state.conexao_mysql = None
    
    # Se não tem conexão ou conexão está morta
    if not st.session_state.conexao_mysql:
        st.session_state.conexao_mysql = conectar_mysql()
        return st.session_state.conexao_mysql
    
    # Verificar se conexão ainda está ativa
    try:
        if st.session_state.conexao_mysql.is_connected():
            return st.session_state.conexao_mysql
        else:
            st.session_state.conexao_mysql = conectar_mysql()
            return st.session_state.conexao_mysql
    except:
        st.session_state.conexao_mysql = conectar_mysql()
        return st.session_state.conexao_mysql

# ============ FUNÇÕES AUXILIARES ============
def obter_bancos_mysql():
    """Retorna lista de bancos"""
    conexao = get_conexao()
    if not conexao:
        return []
    
    try:
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        bancos = [b[0] for b in cursor.fetchall() 
                 if b[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
        cursor.close()
        return bancos
    except:
        return []
    
def verificar_tabelas_duplicadas_entre_bancos():
    """Verifica se há tabelas com mesmo nome em bancos diferentes"""
    try:
        conexao = conectar_banco(None)
        cursor = conexao.cursor()
        
        cursor.execute("""
            SELECT TABLE_NAME, GROUP_CONCAT(TABLE_SCHEMA) as bancos
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            GROUP BY TABLE_NAME
            HAVING COUNT(DISTINCT TABLE_SCHEMA) > 1
        """)
        
        duplicadas = cursor.fetchall()
        cursor.close()
        conexao.close()
        
        if duplicadas:
            st.warning("⚠️ **ATENÇÃO:** Tabelas duplicadas entre bancos:")
            for tabela, bancos in duplicadas:
                st.write(f"- `{tabela}` → Bancos: {bancos}")
            
            st.error("Isso pode causar confusão nas relações. Considere renomear ou remover as duplicatas.")
        
        return duplicadas
    except:
        return []    

# ============ ESTADO DA APLICAÇÃO ============
if "pagina" not in st.session_state:
    st.session_state.pagina = "home"

# ============ BARRA LATERAL INTELIGENTE ============
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="margin-bottom: 5px;">🗄️</h1>
        <h3 style="margin-top: 0;">MySQL Manager PRO</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Status da conexão
    conexao = get_conexao()
    status_docker = verificar_mysql_docker()
    
    if conexao and conexao.is_connected():
        st.success("✅ **MySQL Conectado**")
        try:
            cursor = conexao.cursor()
            cursor.execute("SELECT DATABASE()")
            resultado = cursor.fetchone()
            banco = resultado[0] if resultado and resultado[0] else "Nenhum"
            cursor.close()
            st.caption(f"📁 Banco: **{banco}**")
        except:
            st.caption("📁 Banco: Desconhecido")
    else:
        st.error("❌ **Desconectado**")
    
    # Status Docker
    if status_docker:
        st.info("🐳 Docker MySQL Ativo")
    else:
        st.warning("⚡ XAMPP/Tradicional")
    
    st.markdown("---")
    
    # ============ SELEÇÃO DE BANCO (SISTEMA SIMPLES) ============
    st.markdown("### 🎯 Banco de Trabalho")
    
    # Inicializar estado do banco se necessário
    if "banco_ativo" not in st.session_state:
        st.session_state.banco_ativo = None
    
    # Listar bancos disponíveis
    def listar_bancos_sidebar():
        """Lista bancos para a sidebar"""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            todos = [db[0] for db in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            # Filtrar bancos do sistema
            return [b for b in todos if b not in [
                'information_schema', 'mysql', 'performance_schema', 'sys'
            ]]
        except:
            return []
    
    bancos = listar_bancos_sidebar()
    
    if bancos:
        # Mostrar banco atual
        if st.session_state.banco_ativo:
            st.success(f"✅ **{st.session_state.banco_ativo}**")
        else:
            st.warning("⚠️ Nenhum banco selecionado")
        
        # Seletor de banco
        banco_selecionado = st.selectbox(
            "Selecionar banco:",
            bancos,
            index=bancos.index(st.session_state.banco_ativo) if st.session_state.banco_ativo in bancos else 0,
            key="sidebar_select_banco",
            label_visibility="collapsed"
        )
        
        # Botão para aplicar seleção
        if st.button("✅ Aplicar Banco", use_container_width=True, type="primary"):
            st.session_state.banco_ativo = banco_selecionado
            st.success(f"Banco '{banco_selecionado}' selecionado!")
            st.rerun()
        
        # Mostrar informações do banco ativo
        if st.session_state.banco_ativo:
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database=st.session_state.banco_ativo
                )
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES")
                tabelas = cursor.fetchall()
                cursor.close()
                conn.close()
                
                st.caption(f"📊 {len(tabelas)} tabelas")
                
                # Mostrar algumas tabelas
                if tabelas:
                    with st.expander(f"Ver {len(tabelas)} tabelas"):
                        for tabela in tabelas[:5]:  # Mostrar apenas 5
                            st.write(f"• `{tabela[0]}`")
                        if len(tabelas) > 5:
                            st.caption(f"... e mais {len(tabelas) - 5}")
            except:
                st.caption("📊 Carregando...")
        
        # Link para página de gerenciamento
        st.markdown("---")
        if st.button("📋 Gerenciar Todos os Bancos", use_container_width=True):
            st.session_state.pagina = "listar_bancos"
            st.rerun()
    
    else:
        st.error("❌ Nenhum banco encontrado")
        if st.button("🗄️ Criar Primeiro Banco", use_container_width=True, type="primary"):
            st.session_state.pagina = "criar_banco"
            st.rerun()
    
    st.markdown("---")
    
    # Menu Principal mantendo SEUS módulos
    st.markdown("### 📂 **Menu Principal**")
    
    # Lista de páginas baseada nos seus arquivos
    paginas = [
        ("🏠 Página Inicial", "home"),
        ("🔧 Listar Bancos", "listar_bancos"),
        ("🗄️ Criar Banco", "criar_banco"),
        ("🏗️ Criar Tabelas", "criar_tabelas"),
        ("🔍 Criar Consultas", "criar_consultas"),
        ("🔗 Ver Relações Por Grafico", "relacoes"),
        ("📝 Inserir Registos", "Formularios"),
        ("⚡ Editor SQL", "query_editor"),
        ("📚 Guia MySQL", "manual"),
        ("🎯 Exercícios", "exercicios"),
        ("💾 Backup", "backup"),
    ]
    
    for texto, pagina_nome in paginas:
        if st.button(texto, use_container_width=True,
                    type="primary" if st.session_state.pagina == pagina_nome else "secondary"):
            st.session_state.pagina = pagina_nome
            st.rerun()
    
    st.markdown("---")
    
    # Controles de Conexão Avançados
    st.markdown("### 🔌 **Controle MySQL**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🐳 Iniciar Docker", help="Usa Docker MySQL (estável)", use_container_width=True):
            if iniciar_mysql_docker():
                st.session_state.conexao_mysql = None  # Forçar nova conexão
                st.rerun()
    
    with col2:
        if st.button("🔄 Reconectar", help="Tenta reconectar", use_container_width=True):
            st.session_state.conexao_mysql = None
            st.rerun()
    
    st.markdown("---")
            
    st.markdown("---")
    st.caption(f"Página: **{st.session_state.pagina}**")
    st.caption("Docker • Xampp • MySQL")
    st.caption("Idializado por: Luis Gomes ")
    st.caption("Criado 2026")
# ============ PÁGINA HOME ATUALIZADA ============
def pagina_home():
    st.title("🏠 Sistema MySQL - Docker Fix")
    
    # Status do sistema
    conexao = get_conexao()
    docker_rodando = verificar_mysql_docker()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if conexao and conexao.is_connected():
            st.success("✅ Conectado")
        else:
            st.error("❌ Desconectado")
    
    with col2:
        if docker_rodando:
            st.info("🐳 Docker")
        else:
            st.info("⚡ XAMPP")
    
    with col3:
        bancos = obter_bancos_mysql()
        st.metric("Bancos", len(bancos))
    
    with col4:
        st.metric("Hora", datetime.now().strftime("%H:%M"))
    
    st.markdown("---")
    
    # Solução do Problema
    with st.expander("🔧 SOLUÇÃO DO PROBLEMA DO XAMPP", expanded=True):
        st.markdown("""
        ### ❌ **Problema:** XAMPP desliga sozinho
        ### ✅ **Solução:** Use Docker MySQL (mais estável)
        
        **Clique no botão abaixo para iniciar MySQL via Docker:**
        """)
        
        if st.button("🚀 INICIAR MYSQL DOCKER AGORA", type="primary", use_container_width=True):
            if iniciar_mysql_docker():
                st.success("✅ MySQL Docker iniciado! Reconectando...")
                time.sleep(5)
                st.rerun()
        
        st.markdown("""
        **Vantagens do Docker:**
        - ✅ **Estável** - Não desliga sozinho
        - ✅ **Rápido** - Inicia em segundos
        - ✅ **Isolado** - Não interfere com sistema
        - ✅ **Persistente** - Dados salvos
        
        **Depois de iniciar Docker, use normalmente todos os módulos abaixo:**
        """)
    
    st.markdown("---")
    
    # Cards dos seus módulos
    st.subheader("📦 SEUS MÓDULOS DISPONÍVEIS")
    
    modulos = [
        ("🗄️ Criar Banco", "criar_banco", "criar_banco.py", "Crie novos bancos de Dados"),
        ("🔧 listar bancos", "listar_bancos", "listar_bancos.py", "Lista de Bancos de Dados Existentes"),
        ("🏗️ Criar Tabelas", "criar_tabelas", "criar_tabelas.py", "Crie tabelas..."),
        ("🔍 Criar Consultas", "criar_consultas", "criar_consultas.py", "Construa queries"),
        ("🔗 Ver Relações Por Grafico", "relacoes", "relacoes_1.py", "Visualize relacionamentos entre tabelas"),
        ("📝 Formulários", "Formularios", "Formularios.py", "CRUD completo"),
        ("⚡ Editor SQL", "query_editor", "query_editor.py", "Execute SQL direto"),
        ("📚 Guia MySQL", "manual", "manual.py", "Documentação"),
        ("🎯 Exercícios", "exercicios", "exercicios.py", "Pratique SQL"),
        ("💾 Backup", "backup", "backup_restore.py", "Backup e restore"),
        
    ]
    
    # Verificar quais módulos existem
    modulos_existentes = []
    for titulo, pagina, arquivo, desc in modulos:
        if os.path.exists(arquivo) or os.path.exists(f"modules/{arquivo}"):
            modulos_existentes.append((titulo, pagina, desc))
    
    # Mostrar em grid 3x3
    for i in range(0, len(modulos_existentes), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(modulos_existentes):
                titulo, pagina, desc = modulos_existentes[i + j]
                with cols[j]:
                    with st.container(border=True, height=150):
                        st.markdown(f"**{titulo}**")
                        st.caption(desc)
                        if st.button("Abrir →", key=f"btn_{pagina}", use_container_width=True):
                            st.session_state.pagina = pagina
                            st.rerun()
    
    # Se faltam módulos
    faltantes = []
    for titulo, pagina, arquivo, desc in modulos:
        if not os.path.exists(arquivo) and not os.path.exists(f"modules/{arquivo}"):
            faltantes.append(arquivo)
    
    if faltantes:
        st.warning(f"⚠️ {len(faltantes)} módulo(s) não encontrado(s)")
        with st.expander("Ver módulos faltantes"):
            for f in faltantes:
                st.write(f"- {f}")

# ============ CARREGADOR DE MÓDULOS SEGURO ============
def carregar_modulo_seguro(modulo_nome, funcao_principal=None):
    """Carrega módulos com tratamento de erro"""
    try:
        # Tentar importar diretamente
        modulo = __import__(modulo_nome)
        
        if funcao_principal:
            # Executar função principal do módulo
            if hasattr(modulo, funcao_principal):
                getattr(modulo, funcao_principal)()
            else:
                # Tentar nome alternativo
                funcoes_possiveis = ['main', 'pagina_principal', 'interface_principal', 
                                    'pagina_' + modulo_nome, modulo_nome + '_main']
                
                for funcao in funcoes_possiveis:
                    if hasattr(modulo, funcao):
                        getattr(modulo, funcao)()
                        return
                
                # Se não encontrou função, assumir que módulo executa diretamente
                if callable(modulo):
                    modulo()
                else:
                    st.error(f"Módulo {modulo_nome} não tem função principal clara")
        else:
            # Módulo auto-executável
            if callable(modulo):
                modulo()
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar {modulo_nome}: {str(e)[:100]}")
        
        # Botões de recuperação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Voltar para Home", key=f"voltar_{modulo_nome}"):
                st.session_state.pagina = "home"
                st.rerun()
        with col2:
            if st.button("🔄 Tentar Novamente", key=f"retry_{modulo_nome}"):
                st.rerun()
                
# ============ FUNÇÃO PARA VERIFICAR BANCO ============
def verificar_banco_pagina():
    """Verifica se há banco selecionado, se não, mostra aviso"""
    if "banco_ativo" not in st.session_state or not st.session_state.banco_ativo:
        st.error("⚠️ Nenhum banco de dados selecionado!")
        
        # Listar bancos rapidamente
        try:
            conexao = conectar_mysql()
            if conexao:
                cursor = conexao.cursor()
                cursor.execute("SHOW DATABASES")
                bancos = [b[0] for b in cursor.fetchall()]
                cursor.close()
                
                bancos_usuario = [b for b in bancos if b not in [
                    'information_schema', 'mysql', 'performance_schema', 'sys'
                ]]
                
                if bancos_usuario:
                    banco = st.selectbox("Selecione um banco:", bancos_usuario)
                    if st.button("✅ Usar este banco"):
                        st.session_state.banco_ativo = banco
                        st.rerun()
                else:
                    st.warning("❌ Nenhum banco encontrado. Crie um primeiro.")
        except:
            st.error("❌ Não foi possível conectar ao MySQL")
        
        st.stop()
    
    return st.session_state.banco_ativo                

# ============ ROTEADOR PRINCIPAL ROBUSTO ============
def main():
    pagina = st.session_state.pagina
    
    # Mapeamento de páginas e suas funções principais
    mapeamento = {
        "home": (pagina_home,),
        "criar_banco": ("criar_banco", "pagina_criar_banco"),
        "criar_tabelas": ("criar_tabelas", "pagina_criar_tabelas"),
        "criar_consultas": ("criar_consultas", "interface_consulta_visual"),
        "relacoes": ("relacoes_1", "pagina_relacoes"),  # Note: relacoes_1.py
        "Formularios": ("Formularios", "pagina_formularios"),
        "query_editor": ("query_editor", "pagina_query_editor"),
        "manual": ("manual", "pagina_guia"),
        "exercicios": ("exercicios", "pagina_exercicios"),
        "backup": ("backup_restore", "main"),
        "listar_bancos": ("listar_bancos", "main"),
    }
    
    # Verificar se página existe no mapeamento
    if pagina not in mapeamento:
        st.error(f"Página '{pagina}' não encontrada!")
        if st.button("🏠 Voltar para Home"):
            st.session_state.pagina = "home"
            st.rerun()
        return
    
    # Se é página home (local)
    if pagina == "home":
        pagina_home()
        return
    
    # Para outras páginas, carregar módulo
    info = mapeamento[pagina]
    
    # Adicionar botão de voltar no topo
    col_top1, col_top2 = st.columns([1, 5])
    with col_top1:
        if st.button("← Voltar", key=f"btn_voltar_{pagina}"):
            st.session_state.pagina = "home"
            st.rerun()
    
    with col_top2:
        st.title(f"{pagina.replace('_', ' ').title()}")
    
    st.markdown("---")
    
    # Carregar módulo
    if len(info) == 2:
        modulo_nome, funcao = info
        carregar_modulo_seguro(modulo_nome, funcao)
    else:
        # Backup é especial
        if pagina == "backup":
            try:
                import backup_restore
                backup_restore.main()
            except Exception as e:
                st.error(f"Erro backup: {e}")
    
    # Rodapé com status
    st.markdown("---")
    
    conexao = get_conexao()
    docker_status = "🐳 Docker" if verificar_mysql_docker() else "⚡ XAMPP"
    
    if conexao and conexao.is_connected():
        try:
            cursor = conexao.cursor()
            cursor.execute("SELECT DATABASE()")
            resultado = cursor.fetchone()
            banco = resultado[0] if resultado and resultado[0] else "Nenhum"
            cursor.close()
            
            st.caption(f"✨ {docker_status} | Banco: {banco} | {datetime.now().strftime('%H:%M:%S')}")
        except:
            st.caption(f"✨ {docker_status} | Conectado | {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.caption(f"✨ {docker_status} | Desconectado | {datetime.now().strftime('%H:%M:%S')}")

# ============ PONTO DE ENTRADA COM TRATAMENTO ============
if __name__ == "__main__":
    try:
        # Verificar dependências
        import mysql.connector
        
        # Executar app
        main()
        
    except ImportError as e:
        st.error(f"❌ Falta dependência: {e}")
        st.code("pip install mysql-connector-python pandas streamlit")
        
    except Exception as e:
        st.error(f"❌ Erro crítico: {e}")
        
        # Solução emergencial
        if st.button("🔄 Tentar Solução Emergencial"):
            try:
                # Tentar iniciar Docker
                iniciar_mysql_docker()
                time.sleep(10)
                st.rerun()
            except:
                st.error("Falha na solução emergencial")