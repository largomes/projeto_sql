# modules/tabela_criar.py - VERSÃO COMPLETA E CORRIGIDA
import streamlit as st
import pandas as pd
from .tabela_utils import conectar_banco, listar_tabelas, converter_tipo_access_para_mysql, listar_colunas_tabela

def pagina_criar_tabela():
    """Página para criar tabelas"""
    
    if "menu_estado" not in st.session_state:
        st.error("Menu não inicializado")
        return
    
    banco = st.session_state.menu_estado.get("banco_selecionado")
    if not banco:
        st.warning("⚠️ Selecione um banco de dados primeiro!")
        return
    
    st.header("🏗️ Criar Nova Tabela")
    st.info(f"**Criando tabela no banco:** `{banco}`")
    
    # Nome da tabela
    with st.container(border=True):
        st.markdown("### 1️⃣ Nome da Tabela")
        nome_tabela = st.text_input(
            "**Digite o nome da tabela** *",
            placeholder="ex: clientes, produtos, vendas...",
            key="input_nome_tabela_principal"
        )
        
        if nome_tabela:
            st.session_state.nome_tabela_temp = nome_tabela.strip()
    
    if not st.session_state.get("nome_tabela_temp"):
        st.info("👆 Primeiro digite o nome da tabela acima")
        return
    
    # Botão para ver tipos
    col_tipos, _ = st.columns([1, 3])
    with col_tipos:
        if st.button("📊 Consultar Tipos de Dados", use_container_width=True):
            st.session_state.menu_estado["opcao_selecionada"] = "tipos_dados"
            st.rerun()
    
    st.markdown(f"### 📝 Adicionando colunas à tabela: **{st.session_state.nome_tabela_temp}**")
    
    # Inicializar lista de colunas
    if "colunas_tabela" not in st.session_state:
        st.session_state.colunas_tabela = []
    
    # Mostrar colunas já adicionadas
    if st.session_state.colunas_tabela:
        st.markdown("#### 📋 Colunas Adicionadas")
        st.success(f"✅ **{len(st.session_state.colunas_tabela)} coluna(s) adicionada(s)**")
        
        dados = []
        for idx, coluna in enumerate(st.session_state.colunas_tabela):
            fk_text = ""
            if coluna.get("is_foreign_key") and coluna.get("fk_info"):
                fk_text = f"→ {coluna['fk_info']['tabela_ref']}({coluna['fk_info']['coluna_ref']})"
            
            dados.append({
                "#": idx + 1,
                "Nome": coluna["nome"],
                "Tipo": coluna.get("tipo_mysql", ""),
                "PK": "✓" if coluna.get("is_primary_key") else "",
                "FK": fk_text,
                "UNIQUE": "✓" if coluna.get("is_unique") else "",
                "NULL": "✓" if coluna.get("permite_null") == "NULL" else "✗",
                "DEFAULT": coluna.get("default", "") or ""
            })
        
        if dados:
            df = pd.DataFrame(dados)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Botões para remover
        st.markdown("##### 🗑️ Remover Coluna")
        num_cols = len(st.session_state.colunas_tabela)
        
        for i in range(0, num_cols, 6):
            cols = st.columns(min(6, num_cols - i))
            for j, col in enumerate(cols):
                idx = i + j
                if idx < num_cols:
                    with col:
                        if st.button(f"Remover {idx + 1}", 
                                   key=f"remover_col_{idx}_{len(st.session_state.colunas_tabela)}",
                                   use_container_width=True):
                            st.session_state.colunas_tabela.pop(idx)
                            st.rerun()
        
        st.markdown("---")
    
    # Formulário para nova coluna
    with st.container(border=True):
        st.markdown("#### 📋 Criar Coluna Principal")
        current_index = len(st.session_state.colunas_tabela)
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            nome_coluna = st.text_input(
                "**Nome da Coluna** *",
                key=f"nome_coluna_{current_index}",
                placeholder="ex: id, nome, email..."
            )
            
            tipo_access = st.selectbox(
                "**Tipo de Dado Access** *",
                options=[
                    "Numeração Automática", "Texto", "Memorando", "Número",
                    "Data/Hora", "Moeda", "Sim/Não", "Assistente de pesquisa"
                ],
                key=f"tipo_access_{current_index}"
            )
            
            tipo_mysql = converter_tipo_access_para_mysql(tipo_access)
            st.caption(f"**MySQL:** `{tipo_mysql}`")
        
        with col2:
            permite_null = st.radio(
                "**Permite NULL?**",
                options=["NOT NULL (obrigatório)", "NULL (opcional)"],
                horizontal=True,
                key=f"null_option_{current_index}"
            )
            
            st.markdown("###### 🔑 Chaves e Restrições")
            col_key1, col_key2, col_key3, col_key4 = st.columns(4)
            
            with col_key1:
                is_unique = st.checkbox("**UNIQUE**", key=f"unique_{current_index}")
            
            with col_key2:
                is_primary = st.checkbox("**PRIMARY**", key=f"primary_{current_index}")
            
            with col_key3:
                is_foreign = st.checkbox("**🔗 FK**", key=f"foreign_{current_index}")
            
            with col_key4:
                auto_inc = False
                if tipo_access == "Numeração Automática":
                    auto_inc = st.checkbox("**AUTO**", key=f"autoinc_{current_index}")
            
            default_value = st.text_input(
                "**Valor DEFAULT** (opcional)",
                key=f"default_{current_index}",
                placeholder='ex: 0, "", CURRENT_TIMESTAMP'
            )
            
            # Seção FK
            fk_info = {}
            if is_foreign:
                with st.container(border=True):
                    st.markdown("##### 🔗 FOREIGN KEY Details")
                    
                    fk_col1, fk_col2, fk_col3 = st.columns(3)
                    
                    with fk_col1:
                        tabelas_disponiveis = listar_tabelas(banco)
                        tabela_ref = st.selectbox(
                            "Tabela Referência",
                            options=["Selecione uma tabela"] + tabelas_disponiveis,
                            key=f"fk_table_{current_index}"
                        )
                        fk_info["tabela_ref"] = str(tabela_ref) if tabela_ref else ""
                    
                    with fk_col2:
                        if fk_info.get("tabela_ref") and fk_info["tabela_ref"] != "Selecione uma tabela":
                            colunas_ref = listar_colunas_tabela(banco, fk_info["tabela_ref"])
                            if colunas_ref:
                                colunas_nomes = [str(col[0]) for col in colunas_ref]
                                coluna_ref = st.selectbox(
                                    "Coluna Referência",
                                    options=["Selecione uma coluna"] + colunas_nomes,
                                    key=f"fk_col_{current_index}"
                                )
                                fk_info["coluna_ref"] = str(coluna_ref) if coluna_ref else ""
                    
                    with fk_col3:
                        on_delete = st.selectbox(
                            "ON DELETE",
                            ["", "CASCADE", "SET NULL", "RESTRICT", "NO ACTION"],
                            key=f"on_delete_{current_index}"
                        )
                        fk_info["on_delete"] = str(on_delete) if on_delete else ""
                        
                        on_update = st.selectbox(
                            "ON UPDATE",
                            ["", "CASCADE", "SET NULL", "RESTRICT", "NO ACTION"],
                            key=f"on_update_{current_index}"
                        )
                        fk_info["on_update"] = str(on_update) if on_update else ""
    
    # Botões de ação
    st.markdown("##### 🎯 Ações")
    col_acao1, col_acao2, col_acao3, col_acao4 = st.columns(4)
    
    with col_acao1:
        if st.button("✅ **CONFIRMAR ENTRADA**", 
                   use_container_width=True,
                   type="primary",
                   disabled=not nome_coluna,
                   key=f"btn_add_{current_index}"):
            
            # Validações
            errors = []
            if is_primary and is_foreign:
                errors.append("❌ Uma coluna não pode ser PRIMARY KEY e FOREIGN KEY ao mesmo tempo!")
            
            if is_foreign:
                if not fk_info.get("tabela_ref") or fk_info["tabela_ref"] == "Selecione uma tabela":
                    errors.append("❌ Para FOREIGN KEY, selecione uma tabela de referência!")
                if not fk_info.get("coluna_ref") or fk_info["coluna_ref"] == "Selecione uma coluna":
                    errors.append("❌ Para FOREIGN KEY, selecione uma coluna de referência!")
            
            if errors:
                for error in errors:
                    st.error(error)
                return
            
            # Criar objeto da coluna
            coluna_info = {
                "nome": nome_coluna,
                "tipo_access": tipo_access,
                "tipo_mysql": tipo_mysql,
                "permite_null": "NOT NULL" if "NOT NULL" in permite_null else "NULL",
                "is_unique": is_unique,
                "is_primary_key": is_primary,
                "is_foreign_key": is_foreign,
                "is_auto_increment": auto_inc,
                "default": default_value if default_value else None,
                "fk_info": None
            }
            
            if is_foreign and fk_info.get("tabela_ref") and fk_info.get("coluna_ref"):
                coluna_info["fk_info"] = {
                    "tabela_ref": fk_info["tabela_ref"],
                    "coluna_ref": fk_info["coluna_ref"],
                    "on_delete": fk_info.get("on_delete", ""),
                    "on_update": fk_info.get("on_update", "")
                }
            
            st.session_state.colunas_tabela.append(coluna_info)
            st.rerun()
    
    with col_acao2:
        if st.button("🗑️ **LIMPAR FORMULÁRIO**",
                   use_container_width=True,
                   type="secondary",
                   key="btn_limpar_form"):
            st.rerun()
    
    with col_acao3:
        if st.button("🚀 **ADICIONAR TABELA NO BANCO**",
                   use_container_width=True,
                   type="primary",
                   disabled=len(st.session_state.colunas_tabela) == 0,
                   key="btn_criar_tabela"):
            criar_tabela_no_banco(banco, st.session_state.nome_tabela_temp)
    
    with col_acao4:
        if st.button("❌ **CANCELAR TUDO**",
                   use_container_width=True,
                   type="secondary",
                   key="btn_cancelar_tudo"):
            if "nome_tabela_temp" in st.session_state:
                del st.session_state.nome_tabela_temp
            if "colunas_tabela" in st.session_state:
                del st.session_state.colunas_tabela
            st.rerun()

def criar_tabela_no_banco(banco, nome_tabela):
    """Cria a tabela no banco de dados"""
    try:
        conexao = conectar_banco(banco)
        if not conexao:
            st.error("❌ Não foi possível conectar ao banco")
            return
        
        cursor = conexao.cursor()
        
        # Verificar engine
        cursor.execute("SHOW ENGINES")
        engines = cursor.fetchall()
        innodb_available = any(engine[0] == 'InnoDB' for engine in engines)
        
        # Construir SQL
        sql_parts = []
        fk_constraints = []
        
        for coluna in st.session_state.colunas_tabela:
            col_def = f"`{coluna['nome']}` {coluna['tipo_mysql']}"
            
            if coluna['permite_null'] == "NOT NULL":
                col_def += " NOT NULL"
            elif coluna['permite_null'] == "NULL":
                col_def += " NULL"
            
            if coluna['is_unique']:
                col_def += " UNIQUE"
            
            if coluna.get('is_auto_increment'):
                col_def += " AUTO_INCREMENT"
            
            if coluna['default']:
                default_val = coluna['default']
                if default_val.upper() in ["CURRENT_TIMESTAMP", "NOW()"]:
                    col_def += f" DEFAULT {default_val.upper()}"
                else:
                    col_def += f" DEFAULT '{default_val}'"
            
            sql_parts.append(col_def)
            
            if coluna['is_primary_key']:
                sql_parts.append(f"PRIMARY KEY (`{coluna['nome']}`)")
            
            if coluna['is_foreign_key'] and coluna['fk_info']:
                fk = f"FOREIGN KEY (`{coluna['nome']}`) "
                fk += f"REFERENCES `{coluna['fk_info']['tabela_ref']}`(`{coluna['fk_info']['coluna_ref']}`)"
                
                if coluna['fk_info']['on_delete']:
                    fk += f" ON DELETE {coluna['fk_info']['on_delete']}"
                if coluna['fk_info']['on_update']:
                    fk += f" ON UPDATE {coluna['fk_info']['on_update']}"
                
                fk_constraints.append(fk)
        
        # Juntar tudo
        all_parts = sql_parts + fk_constraints
        sql = f"CREATE TABLE `{nome_tabela}` (\n  " + ",\n  ".join(all_parts) + "\n)"
        
        if innodb_available:
            sql += " ENGINE=InnoDB"
        
        # Executar
        cursor.execute(sql)
        conexao.commit()
        
        st.success(f"✅ Tabela **'{nome_tabela}'** criada com sucesso!")
        
        # Limpar estado
        if "nome_tabela_temp" in st.session_state:
            del st.session_state.nome_tabela_temp
        if "colunas_tabela" in st.session_state:
            del st.session_state.colunas_tabela
        
        cursor.close()
        
    except Exception as e:
        st.error(f"❌ Erro ao criar tabela: {e}")