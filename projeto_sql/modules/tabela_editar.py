# modules/tabela_editar.py - VERSÃO COMPLETA E CORRIGIDA
import streamlit as st
import pandas as pd
from .tabela_utils import conectar_banco, listar_tabelas, converter_tipo_access_para_mysql, listar_colunas_tabela

def mostrar_fks_tabela(banco, tabela, cursor):
    """Mostra todas as FOREIGN KEYS de uma tabela"""
    try:
        cursor.execute(f"""
            SELECT 
                kcu.CONSTRAINT_NAME,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME,
                rc.UPDATE_RULE,
                rc.DELETE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                AND kcu.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
            WHERE kcu.TABLE_SCHEMA = '{banco}'
                AND kcu.TABLE_NAME = '{tabela}'
                AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY kcu.CONSTRAINT_NAME
        """)
        
        fks = cursor.fetchall()
        
        if fks:
            st.markdown("##### 🔗 FOREIGN KEYS da Tabela:")
            for fk in fks:
                constraint_name = fk[0]
                coluna_fk = fk[1]
                tabela_ref = fk[2]
                coluna_ref = fk[3]
                on_update = fk[4] or "RESTRICT"
                on_delete = fk[5] or "RESTRICT"
                
                st.info(f"""
                **{constraint_name}:**  
                • `{coluna_fk}` → `{tabela_ref}`.`{coluna_ref}`  
                • ON UPDATE: {on_update}  
                • ON DELETE: {on_delete}
                """)
            return True
        return False
    except Exception as e:
        st.info(f"ℹ️ Não foi possível obter detalhes das FKs: {e}")
        return False

def pagina_editar_tabela():
    """Página para editar tabelas existentes"""
    
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
    
    st.header(f"✏️ Editar Tabela: `{tabela}`")
    st.info(f"**Banco:** `{banco}`")
    
    st.markdown("### 🔧 Ações Disponíveis")
    col_op1, col_op2, col_op3, col_op4 = st.columns(4)
    
    with col_op1:
        if st.button("📝 Renomear Tabela", use_container_width=True, key=f"btn_renomear_{tabela}"):
            st.session_state.menu_estado["acao_edicao"] = "renomear"
            st.rerun()
    
    with col_op2:
        if st.button("➕ Adicionar Coluna", use_container_width=True, key=f"btn_adicionar_{tabela}"):
            st.session_state.menu_estado["acao_edicao"] = "adicionar_coluna"
            st.rerun()
    
    with col_op3:
        if st.button("✏️ Modificar Coluna", use_container_width=True, key=f"btn_modificar_{tabela}"):
            st.session_state.menu_estado["acao_edicao"] = "modificar_coluna"
            st.rerun()
    
    with col_op4:
        if st.button("🗑️ Remover Coluna", use_container_width=True, key=f"btn_remover_{tabela}"):
            st.session_state.menu_estado["acao_edicao"] = "remover_coluna"
            st.rerun()
    
    st.markdown("---")
    
    acao = st.session_state.menu_estado.get("acao_edicao", "")
    
    if acao == "renomear":
        renomear_tabela(banco, tabela)
    elif acao == "adicionar_coluna":
        adicionar_coluna_tabela(banco, tabela)
    elif acao == "modificar_coluna":
        modificar_coluna_tabela(banco, tabela)
    elif acao == "remover_coluna":
        remover_coluna_tabela(banco, tabela)
    else:
        mostrar_informacoes_tabela(banco, tabela)
    
    st.markdown("---")
    if st.button("🔙 Voltar para Lista de Tabelas", key=f"btn_voltar_editar_{tabela}"):
        st.session_state.menu_estado["opcao_selecionada"] = "listar_tabelas"
        st.session_state.menu_estado.pop("acao_edicao", None)
        st.rerun()

def mostrar_informacoes_tabela(banco, tabela):
    """Mostra informações detalhadas da tabela"""
    colunas = listar_colunas_tabela(banco, tabela)
    
    if not colunas:
        st.warning(f"Não foi possível obter informações da tabela {tabela}")
        return
    
    st.subheader("📊 Estrutura da Tabela")
    df = pd.DataFrame(colunas, columns=["Campo", "Tipo", "Null", "Key", "Default", "Extra"])
    st.dataframe(df, use_container_width=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Colunas", len(colunas))
    with col2:
        pk_count = sum(1 for c in colunas if "PRI" in str(c[3]))
        st.metric("PK", pk_count)
    with col3:
        fk_count = sum(1 for c in colunas if "MUL" in str(c[3]))
        st.metric("FK", fk_count)
    with col4:
        not_null_count = sum(1 for c in colunas if "NO" in str(c[2]))
        st.metric("NOT NULL", not_null_count)
    
    if fk_count > 0:
        st.markdown("---")
        try:
            conexao = conectar_banco(banco)
            if conexao:
                cursor = conexao.cursor()
                mostrar_fks_tabela(banco, tabela, cursor)
                cursor.close()
        except:
            pass

def renomear_tabela(banco, tabela_atual):
    """Renomear uma tabela"""
    st.subheader("📝 Renomear Tabela")
    st.write(f"**Tabela atual:** `{tabela_atual}`")
    
    novo_nome = st.text_input("**Novo nome da tabela**", placeholder="Digite o novo nome...", key=f"novo_nome_{tabela_atual}")
    
    if novo_nome and novo_nome != tabela_atual:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.info(f"Alterar de: `{tabela_atual}` para: `{novo_nome}`")
        with col2:
            if st.button("✅ Confirmar", use_container_width=True, type="primary", key=f"btn_confirm_rename_{tabela_atual}"):
                try:
                    conexao = conectar_banco(banco)
                    if conexao:
                        cursor = conexao.cursor()
                        cursor.execute(f"RENAME TABLE `{tabela_atual}` TO `{novo_nome}`")
                        conexao.commit()
                        st.success(f"✅ Tabela renomeada para `{novo_nome}`!")
                        st.session_state.menu_estado["tabela_selecionada"] = novo_nome
                        cursor.close()
                        del st.session_state.menu_estado["acao_edicao"]
                    else:
                        st.error("Não foi possível conectar ao banco")
                except Exception as e:
                    st.error(f"❌ Erro ao renomear: {e}")
        with col3:
            if st.button("❌ Cancelar", use_container_width=True, key=f"btn_cancel_rename_{tabela_atual}"):
                st.session_state.menu_estado["acao_edicao"] = None
                st.rerun()

def adicionar_coluna_tabela(banco, tabela):
    """Adicionar nova coluna à tabela"""
    st.subheader("➕ Adicionar Nova Coluna")
    
    coluna_anterior = None
    fk_info = {"tabela_ref": "", "coluna_ref": "", "on_delete": "RESTRICT", "on_update": "RESTRICT"}
    
    col1, col2 = st.columns(2)
    with col1:
        nome_coluna = st.text_input("**Nome da Coluna** *", placeholder="ex: nova_coluna", key=f"nome_col_{tabela}")
        tipo_coluna = st.selectbox("**Tipo de Dado** *", options=["INT", "VARCHAR(255)", "TEXT", "DATE", "DATETIME", "DECIMAL(10,2)", "FLOAT", "BOOLEAN", "BLOB", "BIGINT", "CHAR(1)"], key=f"tipo_{tabela}")
    
    with col2:
        permite_null = st.radio("**Permite NULL?** *", options=["NOT NULL", "NULL"], horizontal=True, key=f"null_{tabela}")
        posicao = st.selectbox("**Posição da Coluna**", options=["ÚLTIMA", "PRIMEIRA", "APÓS..."], key=f"pos_{tabela}")
        
        if posicao == "APÓS...":
            colunas_existentes = listar_colunas_tabela(banco, tabela)
            if colunas_existentes:
                colunas_nomes = [str(c[0]) for c in colunas_existentes]
                coluna_anterior = st.selectbox("Após qual coluna?", options=colunas_nomes, key=f"after_{tabela}")
    
    st.markdown("##### 🔑 Chaves e Restrições")
    col_key1, col_key2, col_key3, col_key4 = st.columns(4)
    with col_key1:
        is_primary = st.checkbox("PRIMARY KEY", key=f"pk_{tabela}")
    with col_key2:
        is_unique = st.checkbox("UNIQUE", key=f"unique_{tabela}")
    with col_key3:
        is_foreign = st.checkbox("FOREIGN KEY", key=f"fk_{tabela}")
    with col_key4:
        auto_inc = False
        if tipo_coluna in ["INT", "BIGINT"]:
            auto_inc = st.checkbox("AUTO_INCREMENT", key=f"auto_{tabela}")
    
    if is_foreign:
        st.markdown("---")
        with st.container(border=True):
            st.markdown("##### 🔗 Detalhes FOREIGN KEY")
            todas_tabelas = listar_tabelas(banco)
            tabelas_disponiveis = [t for t in todas_tabelas if t != tabela]
            
            if tabelas_disponiveis:
                fk_col1, fk_col2 = st.columns(2)
                with fk_col1:
                    tabela_ref = st.selectbox("**Tabela Referência** *", options=["-- Selecione --"] + tabelas_disponiveis, key=f"fk_tabela_ref_{tabela}")
                    fk_info["tabela_ref"] = str(tabela_ref) if tabela_ref else ""
                
                with fk_col2:
                    if fk_info["tabela_ref"] and fk_info["tabela_ref"] != "-- Selecione --":
                        colunas_ref = listar_colunas_tabela(banco, fk_info["tabela_ref"])
                        if colunas_ref:
                            colunas_ref_nomes = [str(c[0]) for c in colunas_ref]
                            coluna_ref = st.selectbox("**Coluna Referência** *", options=["-- Selecione --"] + colunas_ref_nomes, key=f"fk_coluna_ref_{tabela}")
                            fk_info["coluna_ref"] = str(coluna_ref) if coluna_ref else ""
                    
                    st.markdown("###### ⚡ Ações")
                    on_delete_val = st.selectbox("ON DELETE", ["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"], key=f"on_del_{tabela}")
                    fk_info["on_delete"] = str(on_delete_val) if on_delete_val else "RESTRICT"
                    
                    on_update_val = st.selectbox("ON UPDATE", ["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"], key=f"on_upd_{tabela}")
                    fk_info["on_update"] = str(on_update_val) if on_update_val else "RESTRICT"
            else:
                st.warning("Não há outras tabelas disponíveis para criar FOREIGN KEY")
    
    with st.expander("⚙️ Outras Opções", expanded=False):
        valor_default = st.text_input("Valor DEFAULT (opcional)", placeholder="ex: 0, '', CURRENT_TIMESTAMP", key=f"default_{tabela}")
    
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("✅ Adicionar Coluna", type="primary", use_container_width=True, disabled=not nome_coluna, key=f"btn_add_{tabela}"):
            validation_errors = []
            if is_primary and is_foreign:
                validation_errors.append("❌ Uma coluna não pode ser PRIMARY KEY e FOREIGN KEY ao mesmo tempo!")
            if is_foreign:
                if not fk_info["tabela_ref"] or fk_info["tabela_ref"] == "-- Selecione --":
                    validation_errors.append("❌ Para FOREIGN KEY, selecione uma tabela de referência!")
                if not fk_info["coluna_ref"] or fk_info["coluna_ref"] == "-- Selecione --":
                    validation_errors.append("❌ Para FOREIGN KEY, selecione uma coluna de referência!")
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
                return
            
            try:
                conexao = conectar_banco(banco)
                if not conexao:
                    st.error("Não foi possível conectar ao banco")
                    return
                
                cursor = conexao.cursor()
                sql = f"ALTER TABLE `{tabela}` ADD COLUMN `{nome_coluna}` {tipo_coluna}"
                
                if permite_null == "NOT NULL":
                    sql += " NOT NULL"
                else:
                    sql += " NULL"
                
                if auto_inc:
                    sql += " AUTO_INCREMENT"
                
                if valor_default:
                    if valor_default.upper() in ["CURRENT_TIMESTAMP", "NOW()", "CURRENT_DATE"]:
                        sql += f" DEFAULT {valor_default.upper()}"
                    else:
                        try:
                            float(valor_default)
                            sql += f" DEFAULT {valor_default}"
                        except ValueError:
                            sql += f" DEFAULT '{valor_default}'"
                
                if is_primary:
                    sql += " PRIMARY KEY"
                elif is_unique:
                    sql += " UNIQUE"
                
                if posicao == "PRIMEIRA":
                    sql += " FIRST"
                elif posicao == "APÓS..." and coluna_anterior:
                    sql += f" AFTER `{coluna_anterior}`"
                
                cursor.execute(sql)
                conexao.commit()
                
                if is_foreign and fk_info.get("tabela_ref") and fk_info.get("coluna_ref"):
                    if fk_info["tabela_ref"] != "-- Selecione --" and fk_info["coluna_ref"] != "-- Selecione --":
                        try:
                            try:
                                cursor.execute(f"ALTER TABLE `{tabela}` ENGINE=InnoDB")
                            except:
                                pass
                            
                            try:
                                cursor.execute(f"ALTER TABLE `{fk_info['tabela_ref']}` ENGINE=InnoDB")
                            except:
                                pass
                            
                            fk_sql = f"ALTER TABLE `{tabela}` ADD FOREIGN KEY (`{nome_coluna}`) "
                            fk_sql += f"REFERENCES `{fk_info['tabela_ref']}`(`{fk_info['coluna_ref']}`)"
                            
                            if fk_info.get("on_delete") and fk_info["on_delete"] not in ["", "RESTRICT"]:
                                fk_sql += f" ON DELETE {fk_info['on_delete']}"
                            
                            if fk_info.get("on_update") and fk_info["on_update"] not in ["", "RESTRICT"]:
                                fk_sql += f" ON UPDATE {fk_info['on_update']}"
                            
                            cursor.execute(fk_sql)
                            conexao.commit()
                            st.success("✅ FOREIGN KEY criada com sucesso!")
                            
                            st.markdown("##### 🔗 Detalhes da FK Criada:")
                            st.info(f"""
                            **Tabela:** `{tabela}`  
                            **Coluna FK:** `{nome_coluna}`  
                            **Referência:** `{fk_info['tabela_ref']}`.`{fk_info['coluna_ref']}`  
                            **ON DELETE:** {fk_info.get('on_delete', 'RESTRICT')}  
                            **ON UPDATE:** {fk_info.get('on_update', 'RESTRICT')}
                            """)
                            
                            st.markdown("---")
                            mostrar_fks_tabela(banco, tabela, cursor)
                            
                        except Exception as fk_error:
                            st.warning(f"⚠️ A coluna foi criada, mas a FOREIGN KEY falhou: {fk_error}")
                
                st.success(f"✅ Coluna `{nome_coluna}` adicionada com sucesso!")
                del st.session_state.menu_estado["acao_edicao"]
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao adicionar coluna: {e}")
    
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True, key=f"btn_cancel_{tabela}"):
            st.session_state.menu_estado["acao_edicao"] = None
            st.rerun()

def modificar_coluna_tabela(banco, tabela):
    """Modificar propriedades de uma coluna"""
    st.subheader("✏️ Modificar Coluna")
    
    colunas = listar_colunas_tabela(banco, tabela)
    if not colunas:
        st.warning("Nenhuma coluna encontrada!")
        return
    
    coluna_selecionada = st.selectbox("**Selecione a coluna para modificar**", options=[str(c[0]) for c in colunas], key=f"sel_col_mod_{tabela}")
    
    if coluna_selecionada:
        coluna_detalhes = None
        for c in colunas:
            if str(c[0]) == coluna_selecionada:
                coluna_detalhes = c
                break
        
        if coluna_detalhes:
            tem_fk_atual = "MUL" in str(coluna_detalhes[3])
            tem_pk_atual = "PRI" in str(coluna_detalhes[3])
            
            st.info(f"**Coluna atual:** `{coluna_selecionada}`")
            
            adicionar_fk = False
            fk_info = {"tabela_ref": "", "coluna_ref": "", "on_delete": "RESTRICT", "on_update": "RESTRICT"}
            
            tab1, tab2, tab3 = st.tabs(["📝 Nome e Tipo", "🔑 Chaves", "⚙️ Outras Opções"])
            
            with tab1:
                st.markdown("#### 📝 Nome e Tipo")
                novo_nome = st.text_input("**Novo nome da coluna**", value=coluna_selecionada, placeholder="Deixe igual para não alterar", key=f"novo_nome_{tabela}_{coluna_selecionada}")
                
                tipos_disponiveis = ["INT", "VARCHAR(255)", "TEXT", "DATE", "DATETIME", "DECIMAL(10,2)", "FLOAT", "BOOLEAN", "BLOB", "BIGINT"]
                tipo_atual = str(coluna_detalhes[1])
                tipo_padrao = 0
                for i, tipo in enumerate(tipos_disponiveis):
                    if tipo in tipo_atual.upper():
                        tipo_padrao = i
                        break
                
                novo_tipo = st.selectbox("**Novo tipo de dado**", options=tipos_disponiveis, index=tipo_padrao, key=f"novo_tipo_{tabela}_{coluna_selecionada}")
                
                if novo_tipo == "VARCHAR(255)":
                    tamanho = st.number_input("Tamanho do VARCHAR", min_value=1, max_value=65535, value=255, key=f"tamanho_{tabela}_{coluna_selecionada}")
                    novo_tipo = f"VARCHAR({int(tamanho)})"
            
            with tab2:
                st.markdown("#### 🔑 Chaves e Restrições")
                col_chave1, col_chave2, col_chave3 = st.columns(3)
                
                with col_chave1:
                    novo_primary = st.checkbox("PRIMARY KEY", value=tem_pk_atual, disabled=tem_fk_atual, key=f"novo_pk_{tabela}_{coluna_selecionada}")
                    if tem_fk_atual and novo_primary:
                        st.warning("Uma coluna FK não pode ser PK")
                
                with col_chave2:
                    novo_unique = st.checkbox("UNIQUE", value="UNI" in str(coluna_detalhes[3]), key=f"novo_unique_{tabela}_{coluna_selecionada}")
                
                with col_chave3:
                    if "INT" in novo_tipo.upper():
                        novo_auto = st.checkbox("AUTO_INCREMENT", value="auto_increment" in str(coluna_detalhes[5]).lower(), key=f"novo_auto_{tabela}_{coluna_selecionada}")
                    else:
                        novo_auto = False
                        st.write("Auto: Não disponível")
                
                st.markdown("##### 🔗 FOREIGN KEY")
                if tem_fk_atual:
                    st.warning("⚠️ Esta coluna já tem uma FOREIGN KEY")
                    st.info("Para modificar FK, remova a atual e adicione nova na aba 'Adicionar Coluna'")
                else:
                    adicionar_fk = st.checkbox("Adicionar FOREIGN KEY", key=f"add_fk_{tabela}_{coluna_selecionada}")
                    
                    if adicionar_fk:
                        with st.container(border=True):
                            st.markdown("###### Detalhes FK")
                            todas_tabelas = listar_tabelas(banco)
                            tabelas_disponiveis = [t for t in todas_tabelas if t != tabela]
                            
                            if tabelas_disponiveis:
                                fk_col1, fk_col2 = st.columns(2)
                                with fk_col1:
                                    tabela_ref = st.selectbox("Tabela referência", options=["-- Selecione --"] + tabelas_disponiveis, key=f"fk_mod_tabela_{tabela}_{coluna_selecionada}")
                                    fk_info["tabela_ref"] = str(tabela_ref) if tabela_ref else ""
                                
                                with fk_col2:
                                    if fk_info["tabela_ref"] and fk_info["tabela_ref"] != "-- Selecione --":
                                        colunas_ref = listar_colunas_tabela(banco, fk_info["tabela_ref"])
                                        if colunas_ref:
                                            colunas_nomes = [str(c[0]) for c in colunas_ref]
                                            coluna_ref = st.selectbox("Coluna referência", options=["-- Selecione --"] + colunas_nomes, key=f"fk_mod_coluna_{tabela}_{coluna_selecionada}")
                                            fk_info["coluna_ref"] = str(coluna_ref) if coluna_ref else ""
                                
                                if fk_info.get("tabela_ref"):
                                    col_acao1, col_acao2 = st.columns(2)
                                    with col_acao1:
                                        fk_info["on_delete"] = st.selectbox("ON DELETE", ["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"], key=f"on_del_mod_{tabela}_{coluna_selecionada}")
                                    with col_acao2:
                                        fk_info["on_update"] = st.selectbox("ON UPDATE", ["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"], key=f"on_upd_mod_{tabela}_{coluna_selecionada}")
            
            with tab3:
                st.markdown("#### ⚙️ Outras Opções")
                st.markdown("##### Permite NULL?")
                novo_null = st.radio("", options=["NULL", "NOT NULL"], index=0 if str(coluna_detalhes[2]) == "YES" else 1, horizontal=True, key=f"novo_null_{tabela}_{coluna_selecionada}")
                
                st.markdown("##### Valor DEFAULT")
                valor_default_atual = str(coluna_detalhes[4]) if coluna_detalhes[4] else ""
                novo_default = st.text_input("Novo valor DEFAULT", value=valor_default_atual, placeholder="Deixe vazio para remover DEFAULT", key=f"novo_default_{tabela}_{coluna_selecionada}")
                
                st.markdown("##### Comentário (opcional)")
                comentario = st.text_area("Descrição da coluna", placeholder="Adicione um comentário sobre esta coluna...", height=100, key=f"comentario_{tabela}_{coluna_selecionada}")
            
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✅ Aplicar Todas as Modificações", use_container_width=True, type="primary", key=f"btn_aplicar_todas_{tabela}_{coluna_selecionada}"):
                    try:
                        conexao = conectar_banco(banco)
                        if not conexao:
                            st.error("Não foi possível conectar ao banco")
                            return
                        
                        cursor = conexao.cursor()
                        
                        if novo_nome and novo_nome != coluna_selecionada:
                            try:
                                rename_sql = f"ALTER TABLE `{tabela}` CHANGE COLUMN `{coluna_selecionada}` `{novo_nome}` {novo_tipo}"
                                
                                if novo_null == "NOT NULL":
                                    rename_sql += " NOT NULL"
                                else:
                                    rename_sql += " NULL"
                                
                                if novo_default:
                                    if novo_default.upper() in ["CURRENT_TIMESTAMP", "NOW()", "CURRENT_DATE"]:
                                        rename_sql += f" DEFAULT {novo_default.upper()}"
                                    else:
                                        try:
                                            float(novo_default)
                                            rename_sql += f" DEFAULT {novo_default}"
                                        except ValueError:
                                            rename_sql += f" DEFAULT '{novo_default}'"
                                elif valor_default_atual:
                                    rename_sql += " DROP DEFAULT"
                                
                                if novo_primary:
                                    rename_sql += " PRIMARY KEY"
                                elif novo_unique:
                                    rename_sql += " UNIQUE"
                                
                                if novo_auto and "INT" in novo_tipo.upper():
                                    rename_sql += " AUTO_INCREMENT"
                                
                                cursor.execute(rename_sql)
                                st.success(f"✅ Nome alterado para: `{novo_nome}`")
                                coluna_selecionada = novo_nome
                                
                            except Exception as rename_err:
                                st.error(f"❌ Erro ao renomear coluna: {rename_err}")
                        else:
                            modify_sql = f"ALTER TABLE `{tabela}` MODIFY COLUMN `{coluna_selecionada}` {novo_tipo}"
                            
                            if novo_null == "NOT NULL":
                                modify_sql += " NOT NULL"
                            else:
                                modify_sql += " NULL"
                            
                            if novo_default:
                                if novo_default.upper() in ["CURRENT_TIMESTAMP", "NOW()", "CURRENT_DATE"]:
                                    modify_sql += f" DEFAULT {novo_default.upper()}"
                                else:
                                    try:
                                        float(novo_default)
                                        modify_sql += f" DEFAULT {novo_default}"
                                    except ValueError:
                                        modify_sql += f" DEFAULT '{novo_default}'"
                            elif valor_default_atual:
                                modify_sql += " DROP DEFAULT"
                            
                            if novo_primary:
                                modify_sql += " PRIMARY KEY"
                            elif novo_unique:
                                modify_sql += " UNIQUE"
                            
                            if novo_auto and "INT" in novo_tipo.upper():
                                modify_sql += " AUTO_INCREMENT"
                            
                            cursor.execute(modify_sql)
                            st.success("✅ Tipo e atributos modificados")
                        
                        if adicionar_fk and fk_info.get("tabela_ref") and fk_info.get("coluna_ref"):
                            if fk_info["tabela_ref"] != "-- Selecione --" and fk_info["coluna_ref"] != "-- Selecione --":
                                try:
                                    try:
                                        cursor.execute(f"ALTER TABLE `{tabela}` ENGINE=InnoDB")
                                    except:
                                        pass
                                    
                                    fk_sql = f"ALTER TABLE `{tabela}` ADD FOREIGN KEY (`{coluna_selecionada}`) "
                                    fk_sql += f"REFERENCES `{fk_info['tabela_ref']}`(`{fk_info['coluna_ref']}`)"
                                    
                                    if fk_info.get("on_delete"):
                                        fk_sql += f" ON DELETE {fk_info['on_delete']}"
                                    
                                    if fk_info.get("on_update"):
                                        fk_sql += f" ON UPDATE {fk_info['on_update']}"
                                    
                                    cursor.execute(fk_sql)
                                    st.success("✅ FOREIGN KEY adicionada")
                                    
                                    st.markdown("##### 🔗 Detalhes da FK Adicionada:")
                                    st.info(f"""
                                    **Tabela:** `{tabela}`  
                                    **Coluna FK:** `{coluna_selecionada}`  
                                    **Referência:** `{fk_info['tabela_ref']}`.`{fk_info['coluna_ref']}`  
                                    **ON DELETE:** {fk_info.get('on_delete', 'RESTRICT')}  
                                    **ON UPDATE:** {fk_info.get('on_update', 'RESTRICT')}
                                    """)
                                    
                                    st.markdown("---")
                                    mostrar_fks_tabela(banco, tabela, cursor)
                                    
                                except Exception as fk_err:
                                    st.warning(f"⚠️ Coluna modificada, mas FK falhou: {fk_err}")
                        
                        if comentario:
                            try:
                                comment_sql = f"ALTER TABLE `{tabela}` MODIFY COLUMN `{coluna_selecionada}` {novo_tipo} COMMENT '{comentario}'"
                                cursor.execute(comment_sql)
                                st.info("💬 Comentário adicionado")
                            except Exception as comment_err:
                                st.info(f"ℹ️ Não foi possível adicionar comentário: {comment_err}")
                        
                        conexao.commit()
                        cursor.close()
                        
                        st.success("✅ Todas as modificações aplicadas!")
                        st.markdown("---")
                        st.subheader("📊 Estrutura Atualizada da Tabela")
                        
                        colunas_atualizadas = listar_colunas_tabela(banco, tabela)
                        if colunas_atualizadas:
                            df_atualizado = pd.DataFrame(colunas_atualizadas, columns=["Campo", "Tipo", "Null", "Key", "Default", "Extra"])
                            st.dataframe(df_atualizado, use_container_width=True)
                        
                        del st.session_state.menu_estado["acao_edicao"]
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao modificar coluna: {e}")
            
            with col_btn2:
                if st.button("❌ Cancelar", use_container_width=True, key=f"btn_cancelar_mod_{tabela}"):
                    st.session_state.menu_estado["acao_edicao"] = None
                    st.rerun()

def remover_coluna_tabela(banco, tabela):
    """Remover uma coluna da tabela"""
    st.subheader("🗑️ Remover Coluna")
    st.warning("⚠️ **Atenção:** Esta ação é irreversível!")
    
    colunas = listar_colunas_tabela(banco, tabela)
    if not colunas:
        st.warning("Nenhuma coluna encontrada!")
        return
    
    coluna_para_remover = st.selectbox("**Selecione a coluna para remover**", options=[str(c[0]) for c in colunas], key=f"sel_col_rem_{tabela}")
    
    if coluna_para_remover:
        coluna_detalhes = None
        for c in colunas:
            if str(c[0]) == coluna_para_remover:
                coluna_detalhes = c
                break
        
        if coluna_detalhes:
            if "PRI" in str(coluna_detalhes[3]):
                st.error("❌ **Não é possível remover uma coluna que é PRIMARY KEY!**")
                return
            
            if "MUL" in str(coluna_detalhes[3]):
                st.warning("⚠️ Esta coluna é uma FOREIGN KEY!")
            
            st.error(f"**Você está prestes a remover a coluna:** `{coluna_para_remover}`")
            st.write(f"**Tipo:** {coluna_detalhes[1]}")
            
            confirmacao = st.text_input("Digite **CONFIRMAR** para prosseguir:", placeholder="CONFIRMAR", key=f"confirm_remover_{tabela}")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Confirmar Remoção", use_container_width=True, type="primary", disabled=confirmacao != "CONFIRMAR", key=f"btn_confirm_rem_{tabela}"):
                    try:
                        conexao = conectar_banco(banco)
                        if conexao:
                            cursor = conexao.cursor()
                            cursor.execute(f"ALTER TABLE `{tabela}` DROP COLUMN `{coluna_para_remover}`")
                            conexao.commit()
                            st.success(f"✅ Coluna `{coluna_para_remover}` removida com sucesso!")
                            del st.session_state.menu_estado["acao_edicao"]
                            st.rerun()
                        else:
                            st.error("Não foi possível conectar ao banco")
                    except Exception as e:
                        st.error(f"❌ Erro ao remover coluna: {e}")
            
            with col_btn2:
                if st.button("❌ Cancelar", use_container_width=True, key=f"btn_cancel_rem_{tabela}"):
                    st.session_state.menu_estado["acao_edicao"] = None
                    st.rerun()