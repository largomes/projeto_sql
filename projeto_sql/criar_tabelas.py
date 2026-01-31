# criar_tabelas.py (ATUALIZADO - adicione import e roteamento)
import streamlit as st
from modules.tabela_utils import *
from modules.tabela_menu import criar_menu_superior
from modules.tabela_criar import pagina_criar_tabela
from modules.tabela_visualizar import pagina_visualizar_tabela
from modules.tabela_tipos import mostrar_tabela_tipos
from modules.tabela_editar import pagina_editar_tabela
from modules.tabela_excluir import pagina_excluir_tabela
from relacoes import pagina_relacoes # NOVO IMPORT
from modules.tabela_criar_heranca import pagina_criar_tabela_com_heranca
from modules.listar_banco import pagina_listar_bancos
import os
import sys

# Verificar se há banco selecionado
if "banco_ativo" not in st.session_state or not st.session_state.banco_ativo:
    st.error("⚠️ Nenhum banco selecionado!")
    st.info("Selecione um banco na barra lateral primeiro.")
    st.stop()

# Agora pode usar
banco_atual = st.session_state.banco_ativo

# Título principal da página
st.title("📊 Sistema de Banco de Dados")

# Banner vermelho com o banco atual
st.markdown(f"""
<div style="background-color: #ffebee; padding: 15px; border-radius: 10px; 
            border-left: 5px solid #f44336; margin: 20px 0;">
    <h3 style="color: #d32f2f; margin: 0;">
        🎯 Banco Atual: 
        <span style="color: #b71c1c; font-weight: bold;">
            {banco_atual}
        </span>
    </h3>
</div>
""", unsafe_allow_html=True)

"""
# DEBUG
print("=== DIAGNÓSTICO ===")
print("Diretório atual:", os.getcwd())
print("Caminho do script:", __file__)

# Lista modules
modules_path = os.path.join(os.getcwd(), "modules")
print("Caminho modules:", modules_path)
print("Modules existe?", os.path.exists(modules_path))

if os.path.exists(modules_path):
    print("Conteúdo de modules:")
    for file in os.listdir(modules_path):
        print(f"  - {file}")

# Adiciona modules ao path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, modules_path)
print("sys.path atualizado")
print("==================")

# Verifica caminhos
st.write("Caminho atual:", os.getcwd())
st.write("Conteúdo da pasta modules:", os.listdir("modules") if os.path.exists("modules") else "Pasta modules não existe")
"""
def pagina_criar_tabelas():
    """Página principal do gerenciador de tabelas - ROTEADOR"""
    
    # 1. Menu superior
    menu_estado = criar_menu_superior()
    opcao = menu_estado.get("opcao_selecionada", "listar_tabelas")
    
    # 2. Roteamento para os módulos
    if opcao == "tipos_dados":
        mostrar_tabela_tipos()
        
        # Botão para voltar
        if st.button("🔙 Voltar para Lista de Tabelas"):
            st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
            st.rerun()
    
    elif opcao == "criar_tabela":
        pagina_criar_tabela()  # ← CHAMA O MÓDULO!
        
    elif opcao == "criar_tabela_heranca":  # NOVO - Adiciona esta opção
        pagina_criar_tabela_com_heranca()
        
    elif opcao == "criar_tabela_heranca":  # ← NOVO!
        pagina_criar_tabela_com_heranca()    
        
    elif opcao == "visualizar_tabela":
        pagina_visualizar_tabela()
    
    elif opcao == "editar_tabela":
        pagina_editar_tabela()
    
    elif opcao == "excluir_tabela":
        pagina_excluir_tabela()
    
    elif opcao == "Visualizar_relacoes":  # NOVO - Página de Relações
        pagina_relacoes()
        
    elif opcao == "listar_bancos":  # ← NOVA OPÇÃO
        pagina_listar_bancos()    
    
    elif opcao == "listar_tabelas":
        st.header("📋 Tabelas do Banco")
        
        banco = menu_estado.get("banco_atual")
        if not banco:
            st.warning("Selecione um banco de dados primeiro!")
            return
        
        tabelas = listar_tabelas(banco_atual)
        
        if tabelas:
            st.markdown(f"**Banco:** `{banco}` | **Total:** {len(tabelas)}")
            
            # Exibir em cards elegantes
            cols = st.columns(2)
            
            for idx, tabela in enumerate(tabelas):
                with cols[idx % 2]:
                    with st.container(border=True, height=300):
                        # Layout interno do card
                        col_left, col_right = st.columns([3, 1])
                        
                        with col_left:
                            # Nome da tabela
                            st.markdown(f"##### 📊 {tabela}")
                            
                            # Informações da tabela
                            colunas = listar_colunas_tabela(banco, tabela)
                            num_colunas = len(colunas) if colunas else 0
                            
                            # Mini estatísticas
                            st.markdown(f"**Colunas:** {num_colunas}")
                            
                            # Contar chaves
                            if colunas:
                                pk_count = sum(1 for c in colunas if len(c) > 3 and "PRI" in str(c[3]))
                                fk_count = sum(1 for c in colunas if len(c) > 3 and "MUL" in str(c[3]))
                                
                                col_stat1, col_stat2 = st.columns(2)
                                with col_stat1:
                                    st.metric("PK", pk_count)
                                with col_stat2:
                                    st.metric("FK", fk_count)
                        
                        with col_right:
                            # Botões de ação verticais
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Botão Visualizar
                            if st.button("👁️ - Visualizar", 
                                       key=f"ver_{tabela}",
                                       help="Visualizar",
                                       use_container_width=True):
                                st.session_state.menu_estado["tabela_selecionada"] = tabela
                                st.session_state.menu_estado["opcao_selecionada"] = "visualizar_tabela"
                                st.rerun()
                            
                            # Botão Editar
                            if st.button("✏️ - Editar", 
                                       key=f"editar_{tabela}",
                                       help="Editar",
                                       use_container_width=True):
                                st.session_state.menu_estado["tabela_selecionada"] = tabela
                                st.session_state.menu_estado["opcao_selecionada"] = "editar_tabela"
                                st.rerun()
                            
                            # Botão Relações (NOVO)
                            if st.button("🔗- Ver Diagrama", 
                                       key=f"rel_{tabela}",
                                       help="Ver Relações",
                                       use_container_width=True):
                                # Primeiro seleciona a tabela, mas vai para página geral
                                st.session_state.menu_estado["tabela_selecionada"] = tabela
                                st.session_state.menu_estado["opcao_selecionada"] = "relacoes"
                                st.rerun()
                            
                            # Botão Excluir
                            if st.button("🗑️ - Excluir", 
                                       key=f"excluir_{tabela}",
                                       help="Excluir",
                                       use_container_width=True,
                                       type="secondary"):
                                st.session_state.menu_estado["tabela_selecionada"] = tabela
                                st.session_state.menu_estado["opcao_selecionada"] = "excluir_tabela"
                                st.rerun()
        else:
            st.info(f"O banco `{banco_atual}` não contém tabelas.")
        
        # Botão para ver relações gerais de TODO o banco
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔗 **VER TODAS AS RELAÇÕES DO BANCO**", 
                       use_container_width=True,
                       type="primary"):
                st.session_state.menu_estado["opcao_selecionada"] = "visualizar_relacoes"
                st.rerun()
    
    
        
        if st.button("🔙 Voltar"):
            st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
            st.rerun()
    
    # 3. Rodapé
    st.markdown("---")
    st.caption("🛠️ Gerenciador de Tabelas SQL | Desenvolvido com Streamlit")

# Função auxiliar (pode estar aqui ou em utils)
def listar_colunas_tabela(database, tabela):
    """Lista colunas de uma tabela"""
    try:
        conexao = conectar_banco(database)
        if conexao:
            cursor = conexao.cursor()
            cursor.execute(f"DESCRIBE {tabela}")
            colunas = cursor.fetchall()
            cursor.close()
            return colunas
    except Exception as e:
        st.error(f"Erro: {e}")
        return []