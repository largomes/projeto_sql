# modules/tabela_menu.py COMPLETO CORRIGIDO
import streamlit as st
from .tabela_utils import listar_bancos, listar_tabelas

def criar_menu_superior():
    """Cria o menu horizontal superior - VERSÃO MODULAR CORRIGIDA"""
    
    # Inicializar estado do menu se não existir
    if "menu_estado" not in st.session_state:
        st.session_state.menu_estado = {
            "opcao_selecionada": "listar_tabelas",
            "banco_selecionado": None,
            "tabela_selecionada": None
        }
    
    # Container para o menu
    with st.container():
        # Primeira linha: Título e Banco
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.subheader("🗄️ Gerenciador de Tabelas SQL")
        
        with col2:
            # Lista de bancos disponíveis
            bancos = listar_bancos()
            if bancos:
                banco_atual = st.session_state.menu_estado.get("banco_selecionado", "Selecione um banco")
                banco_selecionado = st.selectbox(
                    "📂 Banco de Dados",
                    options=["Selecione um banco"] + bancos,
                    index=0 if banco_atual == "Selecione um banco" else bancos.index(banco_atual) + 1 if banco_atual in bancos else 0,
                    key="select_banco_menu",
                    help="Selecione o banco de dados para trabalhar"
                )
                
                if banco_selecionado != "Selecione um banco":
                    st.session_state.menu_estado["banco_selecionado"] = banco_selecionado
                    # Atualizar a conexão com o banco selecionado
                    if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
                        try:
                            cursor = st.session_state.conexao_mysql.cursor()
                            cursor.execute(f"USE {banco_selecionado}")
                            cursor.close()
                            st.session_state.conexao_mysql.database = banco_selecionado
                        except:
                            pass
                else:
                    st.session_state.menu_estado["banco_selecionado"] = None
            else:
                st.info("📭 Nenhum banco disponível")
        
        with col3:
            # Se houver banco selecionado, mostrar contador de tabelas
            if st.session_state.menu_estado.get("banco_selecionado"):
                tabelas = listar_tabelas(st.session_state.menu_estado["banco_selecionado"])
                st.metric("📊 Tabelas", len(tabelas))
        
        st.markdown("---")
        
        # Segunda linha: Menu de Operações
        if st.session_state.menu_estado.get("banco_selecionado"):
            st.markdown("### 📋 Operações com Tabelas")
            
            # 9 botões em linha - CORRIGIDO
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
            
            # Lista de botões: (texto, opção, tooltip, precisa_tabela_selecionada)
            botoes_info = [
                ("🏗️ Criar", "criar_tabela", "Criar uma nova tabela", False),
                ("✏️ Editar", "editar_tabela", "Editar uma tabela existente", True),
                ("🗑️ Excluir", "excluir_tabela", "Excluir uma tabela existente", True),
                ("➕ Com herança", "criar_tabela_heranca", "Criar tabela com herança (PK+FK)", False),
                ("🔧 SQL Builder", "sql_builder", "Construtor visual de SQL", False),
                ("👁️ Visualizar", "visualizar_tabela", "Ver dados e estrutura", True),
                ("📋 Listar", "listar_tabelas", "Listar todas as tabelas", False),
                ("🔗 Ver Diagrama", "Visualizar_relacoes", "Visualizar relações", False),
                ("📊 Tipos", "tipos_dados", "Ver tabela de tipos de dados", False)
            ]
            
            cols = [col1, col2, col3, col4, col5, col6, col7, col8, col9]
            
            for i, (texto, opcao, tooltip, precisa_tabela) in enumerate(botoes_info):
                with cols[i]:
                    # CORREÇÃO AQUI: Converter para booleano explícito
                    if precisa_tabela:
                        disabled = not st.session_state.menu_estado.get("tabela_selecionada")
                    else:
                        disabled = False
                    
                    if st.button(texto, 
                               use_container_width=True,
                               key=f"btn_menu_{opcao}",
                               help=tooltip,
                               disabled=disabled):  # disabled já é booleano
                        st.session_state.menu_estado["opcao_selecionada"] = opcao
                        st.rerun()
            
            # Terceira linha: Seleção de Tabela
            st.markdown("---")
            col_esq, col_dir = st.columns([3, 1])
            
            with col_esq:
                tabelas = listar_tabelas(st.session_state.menu_estado["banco_selecionado"])
                if tabelas:
                    tabela_atual = st.session_state.menu_estado.get("tabela_selecionada")
                    # Encontrar índice correto
                    index = 0  # padrão: "Selecione uma tabela"
                    if tabela_atual and tabela_atual in tabelas:
                        index = tabelas.index(tabela_atual) + 1
                    
                    tabela_selecionada = st.selectbox(
                        "📝 Tabela Selecionada",
                        options=["Selecione uma tabela"] + tabelas,
                        index=index,
                        key="select_tabela_menu",
                        help="Selecione uma tabela para operações"
                    )
                    
                    if tabela_selecionada != "Selecione uma tabela":
                        st.session_state.menu_estado["tabela_selecionada"] = tabela_selecionada
                    else:
                        st.session_state.menu_estado["tabela_selecionada"] = None
                else:
                    st.info("📭 Nenhuma tabela neste banco")
            
            with col_dir:
                # Status do banco selecionado
                if st.session_state.menu_estado.get("banco_selecionado"):
                    st.info(f"📂 Banco: **{st.session_state.menu_estado['banco_selecionado']}**")
                    
                    # Botão para voltar à seleção de banco
                    if st.button("🔙 Trocar Banco", 
                               use_container_width=True,
                               key="btn_trocar_banco"):
                        st.session_state.menu_estado["banco_selecionado"] = None
                        st.session_state.menu_estado["tabela_selecionada"] = None
                        st.rerun()
        
        st.markdown("---")
    
    return st.session_state.menu_estado