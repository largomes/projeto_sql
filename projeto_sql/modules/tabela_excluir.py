# modules/tabela_excluir.py
import streamlit as st
from .tabela_utils import *

def pagina_excluir_tabela():
    """Página para excluir tabelas"""
    
    # Obter estado do menu
    if "menu_estado" not in st.session_state:
        st.error("Menu não inicializado")
        return
    
    banco = st.session_state.menu_estado.get("banco_selecionado")
    tabela = st.session_state.menu_estado.get("tabela_selecionada")
    
    if not banco or not tabela:
        st.warning("⚠️ Selecione um banco e uma tabela primeiro!")
        if st.button("🔙 Voltar para Lista de Tabelas"):
            st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
            st.rerun()
        return
    
    st.header(f"🗑️ Excluir Tabela: `{tabela}`")
    st.error("⚠️ **ATENÇÃO: Esta ação é IRREVERSÍVEL!** ⚠️")
    
    # Informações da tabela
    st.subheader("📋 Informações da Tabela")
    
    # Obter detalhes
    colunas = listar_colunas_tabela(banco, tabela)
    
    if colunas:
        st.write(f"**Banco:** `{banco}`")
        st.write(f"**Colunas:** {len(colunas)}")
        
        # Mostrar relacionamentos
        st.markdown("#### 🔗 Verificar Relacionamentos")
        
        relacionamentos = verificar_relacionamentos(banco, tabela)
        
        if relacionamentos:
            st.warning("**⚠️ Esta tabela tem relacionamentos!**")
            st.write("**Tabelas que dependem desta:**")
            for rel in relacionamentos:
                st.write(f"- `{rel['tabela']}.{rel['coluna']}` → `{tabela}.{rel['coluna_ref']}`")
            
            st.info("**Recomendação:** Primeiro remova os relacionamentos.")
        else:
            st.success("✅ Nenhum relacionamento encontrado.")
    else:
        st.warning(f"Não foi possível obter informações da tabela `{tabela}`")
    
    st.markdown("---")
    
    # Confirmação
    st.subheader("❓ Confirmação de Exclusão")
    
    st.markdown("""
    ### **Você está prestes a excluir PERMANENTEMENTE:**
    
    - **Tabela:** `{tabela}`
    - **Banco:** `{banco}`
    - **Colunas:** {num_colunas}
    
    **TODOS os dados serão perdidos!**
    """.format(tabela=tabela, banco=banco, num_colunas=len(colunas) if colunas else 0))
    
    # Verificação em duas etapas
    st.markdown("#### 🔒 Verificação em Duas Etapas")
    
    # Etapa 1
    col_etapa1, col_etapa2 = st.columns(2)
    
    with col_etapa1:
        confirmacao_1 = st.text_input(
            "**Digite o nome da tabela:**",
            placeholder="Digite o nome exato da tabela",
            key="confirm_1"
        )
    
    with col_etapa2:
        confirmacao_2 = st.selectbox(
            "**Confirme a ação:**",
            options=["", "EXCLUIR", "CANCELAR"],
            key="confirm_2"
        )
    
    # Desabilitar botões se não confirmado
    confirmado = (confirmacao_1 == tabela and confirmacao_2 == "EXCLUIR")
    
    st.markdown("---")
    
    # Botões de ação
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn1:
        if st.button("🔙 Voltar",
                   use_container_width=True,
                   type="secondary"):
            st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
            st.rerun()
    
    with col_btn2:
        if st.button("🗑️ **EXCLUIR TABELA PERMANENTEMENTE**",
                   use_container_width=True,
                   type="primary",
                   disabled=not confirmado):
            excluir_tabela_confirmada(banco, tabela)
    
    with col_btn3:
        if st.button("❌ Cancelar Exclusão",
                   use_container_width=True):
            st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
            st.rerun()

def excluir_tabela_confirmada(banco, tabela):
    """Executa a exclusão da tabela após confirmação"""
    
    try:
        conexao = conectar_banco(banco)
        cursor = conexao.cursor()
        
        # Primeiro, verificar e remover relacionamentos
        cursor.execute(f"""
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME, 
            CONSTRAINT_NAME
        FROM 
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE 
            REFERENCED_TABLE_SCHEMA = '{banco}'
            AND REFERENCED_TABLE_NAME = '{tabela}'
        """)
        
        relacionamentos = cursor.fetchall()
        
        if relacionamentos:
            st.warning("Removendo relacionamentos...")
            for rel in relacionamentos:
                try:
                    cursor.execute(f"ALTER TABLE `{rel[0]}` DROP FOREIGN KEY `{rel[2]}`")
                except:
                    pass
        
        # Excluir tabela
        cursor.execute(f"DROP TABLE IF EXISTS `{tabela}`")
        conexao.commit()
        
        st.success(f"✅ Tabela `{tabela}` excluída com sucesso!")
        st.balloons()
        
        # Redirecionar após 3 segundos
        st.info("Redirecionando para lista de tabelas em 3 segundos...")
        
        import time
        time.sleep(3)
        
        st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
        st.session_state.menu_estado.pop("tabela_selecionada", None)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao excluir tabela: {e}")
        st.info("Verifique se há relacionamentos ou restrições ativas.")

def verificar_relacionamentos(banco, tabela):
    """Verifica se a tabela tem relacionamentos"""
    try:
        conexao = conectar_banco(banco)
        cursor = conexao.cursor()
        
        cursor.execute(f"""
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM 
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE 
            REFERENCED_TABLE_SCHEMA = '{banco}'
            AND REFERENCED_TABLE_NAME = '{tabela}'
        """)
        
        relacionamentos = cursor.fetchall()
        
        resultado = []
        for rel in relacionamentos:
            resultado.append({
                "tabela": rel[0],
                "coluna": rel[1],
                "tabela_ref": rel[2],
                "coluna_ref": rel[3]
            })
        
        cursor.close()
        return resultado
        
    except Exception as e:
        st.error(f"Erro ao verificar relacionamentos: {e}")
        return []
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