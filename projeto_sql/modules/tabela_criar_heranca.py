# modules/tabela_criar_heranca.py - MÓDULO SEPARADO PARA HERANÇA
import streamlit as st
import pandas as pd
from .tabela_utils import *

def pagina_criar_tabela_com_heranca():
    """Página ESPECÍFICA para criar tabelas com herança - NÃO MEXE NO CÓDIGO EXISTENTE"""
    
    st.header("🏗️ Criar Tabela com Herança (PK também é FK)")
    
    # 1. Banco de dados
    bancos = listar_bancos()
    if not bancos:
        st.error("❌ Nenhum banco de dados encontrado!")
        return
    
    banco = st.selectbox("**Banco de Dados**", bancos, key="heranca_banco")
    
    # 2. Informações básicas
    st.markdown("### 📝 Informações da Tabela")
    
    col1, col2 = st.columns(2)
    with col1:
        nome_tabela_filha = st.text_input(
            "**Nome da Tabela Filha** *",
            placeholder="ex: Cliente, Empregado, Aluno...",
            key="heranca_nome_filha"
        )
    
    with col2:
        # Listar tabelas existentes para herança
        tabelas_existentes = listar_tabelas(banco)
        if not tabelas_existentes:
            st.warning("⚠️ Não há tabelas no banco para herança!")
            return
        
        tabela_pai = st.selectbox(
            "**Tabela Pai (herança)** *",
            options=["-- Selecione --"] + tabelas_existentes,
            key="heranca_tabela_pai"
        )
    
    if tabela_pai == "-- Selecione --" or not nome_tabela_filha:
        st.info("ℹ️ Preencha todas as informações acima")
        return
    
    # 3. Analisar tabela pai
    st.markdown("### 🔍 Configurar Herança")
    
    # Obter colunas da tabela pai
    colunas_pai = listar_colunas_tabela(banco, tabela_pai)
    if not colunas_pai:
        st.error(f"❌ Não foi possível obter colunas da tabela `{tabela_pai}`")
        return
    
    # Encontrar PK da tabela pai
    pk_pai = None
    tipo_pk_pai = "INT"  # default
    
    for col in colunas_pai:
        if "PRI" in str(col[3]):
            pk_pai = str(col[0])
            tipo_pk_pai = str(col[1])
            break
    
    if not pk_pai:
        st.error(f"❌ A tabela `{tabela_pai}` não tem PRIMARY KEY definida!")
        return
    
    # Mostrar info da PK pai
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"**PK da tabela pai:**\n`{tabela_pai}`.`{pk_pai}` ({tipo_pk_pai})")
    
    with col_info2:
        coluna_pk_filha = st.text_input(
            "**Nome da coluna PK/FK na tabela filha**",
            value=pk_pai,
            key="heranca_coluna_filha"
        )
        
        on_delete = st.selectbox(
            "**ON DELETE**",
            ["CASCADE", "RESTRICT", "SET NULL", "NO ACTION"],
            index=0,
            key="heranca_on_delete"
        )
        
        on_update = st.selectbox(
            "**ON UPDATE**",
            ["CASCADE", "RESTRICT", "SET NULL", "NO ACTION"],
            index=1,
            key="heranca_on_update"
        )
    
    # 4. Adicionar outras colunas
    st.markdown("### 📊 Outras Colunas da Tabela Filha")
    
    # Inicializar lista de colunas
    if "colunas_filha_heranca" not in st.session_state:
        st.session_state.colunas_filha_heranca = []
    
    # Mostrar colunas já adicionadas
    if st.session_state.colunas_filha_heranca:
        st.markdown("#### ✅ Colunas Adicionadas")
        
        dados = []
        for idx, col in enumerate(st.session_state.colunas_filha_heranca):
            dados.append({
                "#": idx + 1,
                "Nome": col["nome"],
                "Tipo": col["tipo"],
                "PK": "✓" if col.get("is_pk") else "",
                "UNIQUE": "✓" if col.get("is_unique") else "",
                "NULL": "✓" if col.get("permite_null") == "NULL" else "✗"
            })
        
        df = pd.DataFrame(dados)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botão para remover
        if st.button("🗑️ Limpar Todas as Colunas", type="secondary"):
            st.session_state.colunas_filha_heranca = []
            st.rerun()
    
    # Formulário para nova coluna
    with st.container(border=True):
        st.markdown("#### ➕ Adicionar Nova Coluna")
        
        col_geral1, col_geral2 = st.columns(2)
        
        with col_geral1:
            nome_col = st.text_input(
                "Nome da Coluna",
                placeholder="ex: atividade, salario, data_nasc...",
                key="heranca_nova_col_nome"
            )
            
            tipo_col = st.selectbox(
                "Tipo de Dado",
                ["VARCHAR(100)", "INT", "DECIMAL(10,2)", "DATE", "DATETIME", "TEXT", "BOOLEAN"],
                key="heranca_nova_col_tipo"
            )
        
        with col_geral2:
            permite_null_col = st.radio(
                "Permite NULL?",
                ["NOT NULL", "NULL"],
                horizontal=True,
                key="heranca_nova_col_null"
            )
            
            is_unique_col = st.checkbox("UNIQUE", key="heranca_nova_col_unique")
            
            # NOTA: Não permitir PK aqui, pois a PK já é a coluna de herança
            st.caption("⚠️ A PK já é a coluna de herança")
        
        if st.button("✅ Adicionar Esta Coluna", type="primary", use_container_width=True):
            if nome_col and nome_col != coluna_pk_filha:  # Não permitir duplicar a coluna PK/FK
                nova_col = {
                    "nome": nome_col,
                    "tipo": tipo_col,
                    "permite_null": permite_null_col,
                    "is_unique": is_unique_col,
                    "is_pk": False  # Nunca será PK
                }
                
                if "colunas_filha_heranca" not in st.session_state:
                    st.session_state.colunas_filha_heranca = []
                
                st.session_state.colunas_filha_heranca.append(nova_col)
                st.rerun()
            elif nome_col == coluna_pk_filha:
                st.error(f"❌ Já existe a coluna de herança `{coluna_pk_filha}`!")
    
    # 5. Botão final para criar
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    with col_btn1:
        if st.button("🏗️ **CRIAR TABELA COM HERANÇA**", 
                   type="primary", 
                   use_container_width=True,
                   disabled=not nome_tabela_filha):
            
            sql = construir_sql_heranca(
                banco=banco,
                nome_filha=nome_tabela_filha,
                tabela_pai=tabela_pai,
                pk_pai=pk_pai,
                tipo_pk_pai=tipo_pk_pai,
                coluna_pk_filha=coluna_pk_filha,
                colunas_extra=st.session_state.get("colunas_filha_heranca", []),
                on_delete=on_delete,
                on_update=on_update
            )
            
            # Mostrar SQL
            with st.expander("📝 Ver SQL gerado", expanded=True):
                st.code(sql, language="sql")
            
            # Executar
            try:
                conexao = conectar_banco(banco)
                if conexao:
                    cursor = conexao.cursor()
                    cursor.execute(sql)
                    conexao.commit()
                    cursor.close()
                    
                    st.success(f"✅ Tabela `{nome_tabela_filha}` criada com herança de `{tabela_pai}`!")
                    
                    # Limpar estado
                    if "colunas_filha_heranca" in st.session_state:
                        del st.session_state.colunas_filha_heranca
                    
                    # Mostrar estrutura
                    st.markdown("### 📊 Estrutura Criada")
                    colunas_novas = listar_colunas_tabela(banco, nome_tabela_filha)
                    if colunas_novas:
                        df_novo = pd.DataFrame(colunas_novas, 
                                             columns=["Campo", "Tipo", "Null", "Key", "Default", "Extra"])
                        st.dataframe(df_novo, use_container_width=True)
                else:
                    st.error("❌ Erro de conexão com o banco")
                    
            except Exception as e:
                st.error(f"❌ Erro ao criar tabela: {e}")
    
    with col_btn2:
        if st.button("🔄 Recarregar", use_container_width=True):
            st.rerun()
    
    with col_btn3:
        if st.button("🔙 Voltar", use_container_width=True):
            # Voltar para menu principal
            if "menu_estado" in st.session_state:
                st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
            st.rerun()

def construir_sql_heranca(banco, nome_filha, tabela_pai, pk_pai, tipo_pk_pai, 
                         coluna_pk_filha, colunas_extra, on_delete, on_update):
    """Constrói o SQL para criação de tabela com herança"""
    
    # 1. Começar com a coluna PK/FK
    sql_parts = [f"`{coluna_pk_filha}` {tipo_pk_pai} NOT NULL"]
    
    # 2. Adicionar colunas extras
    for col in colunas_extra:
        col_def = f"`{col['nome']}` {col['tipo']}"
        
        if col['permite_null'] == "NOT NULL":
            col_def += " NOT NULL"
        
        if col.get('is_unique'):
            col_def += " UNIQUE"
        
        sql_parts.append(col_def)
    
    # 3. PRIMARY KEY constraint (separada)
    sql_parts.append(f"PRIMARY KEY (`{coluna_pk_filha}`)")
    
    # 4. FOREIGN KEY para herança
    fk_constraint = f"FOREIGN KEY (`{coluna_pk_filha}`) "
    fk_constraint += f"REFERENCES `{tabela_pai}`(`{pk_pai}`)"
    
    if on_delete:
        fk_constraint += f" ON DELETE {on_delete}"
    if on_update:
        fk_constraint += f" ON UPDATE {on_update}"
    
    sql_parts.append(fk_constraint)
    
    # 5. Juntar tudo
    sql = f"CREATE TABLE `{nome_filha}` (\n  "
    sql += ",\n  ".join(sql_parts)
    sql += "\n) ENGINE=InnoDB"
    
    return sql