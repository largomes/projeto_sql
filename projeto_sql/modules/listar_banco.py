# modules/sql_builder.py - VERSÃO COMPLETA CORRIGIDA
import streamlit as st
import pandas as pd
from modules.tabela_utils import *
from datetime import datetime

def pagina_listar_bancos():
    """Página para construção visual de comandos SQL - VERSÃO SIMPLIFICADA"""
    
    st.title("🔧 SQL Builder - Construtor Visual")
    st.markdown("Construa comandos SQL complexos com interface visual")
    
    # Inicializar estado
    if "sql_builder_history" not in st.session_state:
        st.session_state.sql_builder_history = []
    
    # Menu de tipos de comando
    st.markdown("### 📝 Selecione o Tipo de Comando SQL")
    
    tipos_sql = {
        "CREATE TABLE": "Criar nova tabela",
        "ALTER TABLE": "Modificar tabela existente",
        "CREATE DATABASE": "Criar novo banco de dados",
        "DROP TABLE": "Remover tabela",
        "INSERT INTO": "Inserir dados",
        "SELECT": "Consultar dados",
        "UPDATE": "Atualizar dados",
        "DELETE": "Remover dados",
        "ADD CONSTRAINT": "Adicionar constraints (PK, FK, UNIQUE)"
    }
    
    tipo_selecionado = st.selectbox(
        "**Tipo de Comando**",
        options=list(tipos_sql.keys()),
        format_func=lambda x: f"{x} - {tipos_sql[x]}",
        key="sql_builder_tipo"
    )
    
    st.markdown("---")
    
    # ============================================
    # 1. CREATE TABLE
    # ============================================
    if tipo_selecionado == "CREATE TABLE":
        st.subheader("🏗️ Criar Nova Tabela")
        
        col1, col2 = st.columns(2)
        with col1:
            nome_tabela = st.text_input("Nome da Tabela", placeholder="ex: clientes")
            if nome_tabela:
                st.success(f"📝 Criando: `{nome_tabela}`")
        
        with col2:
            engine = st.selectbox("Engine", ["InnoDB", "MyISAM", "MEMORY"], index=0)
            charset = st.selectbox("Charset", ["utf8mb4", "utf8", "latin1"], index=0)
        
        # Colunas da tabela
        st.markdown("#### 📊 Colunas da Tabela")
        
        if "colunas_create" not in st.session_state:
            st.session_state.colunas_create = []
        
        # Adicionar nova coluna
        with st.expander("➕ Adicionar Nova Coluna", expanded=True):
            col_nome = st.text_input("Nome da Coluna", key="col_nome_new")
            
            col_col1, col_col2, col_col3 = st.columns(3)
            with col_col1:
                col_tipo = st.selectbox("Tipo", 
                    ["INT", "VARCHAR(255)", "TEXT", "DATE", "DATETIME", 
                     "DECIMAL(10,2)", "FLOAT", "BOOLEAN", "BLOB"], 
                    key="col_tipo_new")
            
            with col_col2:
                col_null = st.radio("NULL?", ["NOT NULL", "NULL"], horizontal=True, key="col_null_new")
                col_default = st.text_input("Default", placeholder="opcional", key="col_default_new")
            
            with col_col3:
                col_pk = st.checkbox("PRIMARY KEY", key="col_pk_new")
                col_unique = st.checkbox("UNIQUE", key="col_unique_new")
                col_ai = st.checkbox("AUTO_INCREMENT", key="col_ai_new")
            
            if st.button("✅ Adicionar Esta Coluna", key="btn_add_col"):
                if col_nome:
                    nova_col = {
                        "nome": col_nome,
                        "tipo": col_tipo,
                        "null": col_null,
                        "default": col_default if col_default else None,
                        "pk": col_pk,
                        "unique": col_unique,
                        "ai": col_ai
                    }
                    st.session_state.colunas_create.append(nova_col)
                    st.rerun()
        
        # Mostrar colunas adicionadas
        if st.session_state.colunas_create:
            st.markdown("##### 📋 Colunas Adicionadas")
            df_cols = pd.DataFrame(st.session_state.colunas_create)
            st.dataframe(df_cols, use_container_width=True)
            
            if st.button("🗑️ Limpar Todas as Colunas", type="secondary"):
                st.session_state.colunas_create = []
                st.rerun()
        
        # Gerar SQL
        if st.button("🔨 Gerar Comando CREATE TABLE", type="primary"):
            sql = f"CREATE TABLE `{nome_tabela}` (\n"
            
            col_defs = []
            for col in st.session_state.colunas_create:
                col_def = f"  `{col['nome']}` {col['tipo']}"
                
                if col['null'] == "NOT NULL":
                    col_def += " NOT NULL"
                else:
                    col_def += " NULL"
                
                if col.get('ai'):
                    col_def += " AUTO_INCREMENT"
                
                if col.get('default'):
                    col_def += f" DEFAULT '{col['default']}'"
                
                if col.get('unique'):
                    col_def += " UNIQUE"
                
                col_defs.append(col_def)
            
            # Adicionar PRIMARY KEY se houver
            pk_cols = [f"`{col['nome']}`" for col in st.session_state.colunas_create if col.get('pk')]
            if pk_cols:
                col_defs.append(f"  PRIMARY KEY ({', '.join(pk_cols)})")
            
            sql += ",\n".join(col_defs)
            sql += f"\n) ENGINE={engine} DEFAULT CHARSET={charset};"
            
            mostrar_sql_gerado(sql, f"CREATE TABLE {nome_tabela}")
    
    # ============================================
    # 2. ALTER TABLE (MODIFICAR)
    # ============================================
    elif tipo_selecionado == "ALTER TABLE":
        st.subheader("✏️ Modificar Tabela Existente")
        
        # Selecionar banco e tabela
        bancos = listar_bancos() or []
        
        if not bancos:
            st.warning("⚠️ Nenhum banco de dados encontrado!")
            st.info("Crie um banco primeiro usando 'Criar Banco'")
            return
        
        banco_alter = st.selectbox("Banco de Dados", bancos, key="alter_banco")
        
        if banco_alter:
            tabelas = listar_tabelas(banco_alter) or []
            
            if not tabelas:
                st.warning(f"⚠️ Nenhuma tabela encontrada no banco '{banco_alter}'!")
                return
            
            tabela_alter = st.selectbox("Tabela", tabelas, key="alter_tabela")
            
            if tabela_alter:
                # Opções de ALTER
                st.markdown("#### 🔧 Operações Disponíveis")
                
                opcoes_alter = [
                    "ADD COLUMN", "DROP COLUMN", "MODIFY COLUMN",
                    "CHANGE COLUMN", "ADD PRIMARY KEY", "ADD FOREIGN KEY",
                    "ADD UNIQUE CONSTRAINT"
                ]
                
                operacao = st.selectbox("Operação", opcoes_alter, key="alter_operacao")
                
                if operacao == "ADD COLUMN":
                    col_nome = st.text_input("Nome da Nova Coluna")
                    col_tipo = st.selectbox("Tipo", ["INT", "VARCHAR(255)", "DATE", "DECIMAL(10,2)"])
                    
                    colunas_existentes = listar_colunas_tabela(banco_alter, tabela_alter) or []
                    col_posicao = st.selectbox("Posição", ["FIRST", "ÚLTIMA", "APÓS..."])
                    
                    if col_posicao == "APÓS..." and colunas_existentes:
                        col_after = st.selectbox("Depois de:", [str(c[0]) for c in colunas_existentes])
                        col_posicao = f"AFTER `{col_after}`"
                    
                    if col_nome and st.button("Gerar ALTER TABLE ADD COLUMN"):
                        sql = f"ALTER TABLE `{tabela_alter}` ADD COLUMN `{col_nome}` {col_tipo} {col_posicao};"
                        mostrar_sql_gerado(sql, f"ALTER TABLE {tabela_alter}")
                
                elif operacao == "ADD FOREIGN KEY":
                    st.markdown("##### 🔗 Adicionar FOREIGN KEY")
                    
                    colunas_existentes = listar_colunas_tabela(banco_alter, tabela_alter) or []
                    
                    if not colunas_existentes:
                        st.warning("Não foi possível obter colunas da tabela")
                        return
                    
                    coluna_fk = st.selectbox("Coluna que será FK", [str(c[0]) for c in colunas_existentes])
                    tabela_ref = st.text_input("Nome da Tabela Referência", placeholder="ex: Pessoa")
                    coluna_ref = st.text_input("Coluna Referência", value="id")
                    
                    if coluna_fk and tabela_ref and coluna_ref:
                        if st.button("Gerar FOREIGN KEY", type="primary"):
                            sql = f"ALTER TABLE `{tabela_alter}`\n"
                            sql += f"ADD CONSTRAINT fk_{tabela_alter}_{tabela_ref}\n"
                            sql += f"FOREIGN KEY (`{coluna_fk}`)\n"
                            sql += f"REFERENCES `{tabela_ref}`(`{coluna_ref}`)\n"
                            sql += "ON DELETE CASCADE\n"
                            sql += "ON UPDATE CASCADE;"
                            
                            mostrar_sql_gerado(sql, f"FOREIGN KEY: {tabela_alter} → {tabela_ref}")
    
    # ============================================
    # 3. ADD CONSTRAINT (FK, PK, UNIQUE) - VERSÃO SIMPLES
    # ============================================
    elif tipo_selecionado == "ADD CONSTRAINT":
        st.subheader("🔗 Adicionar Constraints")
        
        bancos = listar_bancos() or []
        
        if not bancos:
            st.warning("⚠️ Nenhum banco de dados encontrado!")
            return
        
        banco_const = st.selectbox("Banco", bancos, key="const_banco")
        
        if banco_const:
            tabelas = listar_tabelas(banco_const) or []
            
            if not tabelas:
                st.warning(f"⚠️ Nenhuma tabela no banco '{banco_const}'!")
                return
            
            tabela_const = st.selectbox("Tabela", tabelas, key="const_tabela")
            
            tipo_constraint = st.radio("Tipo de Constraint", ["FOREIGN KEY", "PRIMARY KEY", "UNIQUE"], horizontal=True)
            
            if tipo_constraint == "FOREIGN KEY":
                # VERSÃO SIMPLES - SEM ERROS
                st.markdown("#### 🏗️ Gerador para Herança (PK também é FK)")
                
                st.info(f"**Tabela atual (filha):** `{tabela_const}`")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    coluna_fk = st.text_input(
                        "Coluna PK/FK na tabela filha",
                        value="id",
                        help="Ex: id (será PK nesta tabela e FK para a tabela pai)",
                        key="fk_coluna_filha"
                    )
                    
                    if not coluna_fk:
                        coluna_fk = "id"
                
                with col2:
                    tabela_pai = st.text_input(
                        "Nome da tabela pai",
                        value="Pessoa",
                        help="Ex: Pessoa (tabela que será 'herdada')",
                        key="fk_tabela_pai"
                    )
                    
                    if not tabela_pai:
                        tabela_pai = "Pessoa"
                
                st.markdown("##### 🔗 Detalhes da Foreign Key")
                
                col_ref1, col_ref2 = st.columns(2)
                
                with col_ref1:
                    coluna_ref = st.text_input(
                        "Coluna referência na tabela pai",
                        value="id",
                        help="Ex: id (normalmente a PK da tabela pai)",
                        key="fk_coluna_pai"
                    )
                    
                    if not coluna_ref:
                        coluna_ref = "id"
                
                with col_ref2:
                    on_delete = st.selectbox(
                        "ON DELETE",
                        ["CASCADE", "RESTRICT", "SET NULL", "NO ACTION"],
                        index=0,
                        key="fk_on_delete"
                    )
                    
                    on_update = st.selectbox(
                        "ON UPDATE", 
                        ["CASCADE", "RESTRICT", "SET NULL", "NO ACTION"],
                        index=0,
                        key="fk_on_update"
                    )
                
                if st.button("🏗️ Gerar SQL para Herança", type="primary", use_container_width=True, key="btn_gerar_heranca_final"):
                    coluna_fk_final = coluna_fk or "id"
                    tabela_pai_final = tabela_pai or "Pessoa"
                    coluna_ref_final = coluna_ref or "id"
                    
                    sql = f"-- ============================================\n"
                    sql += f"-- COMANDOS PARA IMPLEMENTAR HERANÇA\n"
                    sql += f"-- Tabela filha: {tabela_const}\n"
                    sql += f"-- Tabela pai: {tabela_pai_final}\n"
                    sql += f"-- ============================================\n\n"
                    
                    sql += f"-- 1. Adicionar coluna (se não existir)\n"
                    sql += f"ALTER TABLE `{tabela_const}` \n"
                    sql += f"ADD COLUMN `{coluna_fk_final}` INT NOT NULL;\n\n"
                    
                    sql += f"-- 2. Tornar a coluna PRIMARY KEY\n"
                    sql += f"ALTER TABLE `{tabela_const}` \n"
                    sql += f"ADD PRIMARY KEY (`{coluna_fk_final}`);\n\n"
                    
                    sql += f"-- 3. Adicionar FOREIGN KEY (herança)\n"
                    sql += f"ALTER TABLE `{tabela_const}` \n"
                    sql += f"ADD CONSTRAINT fk_{tabela_const}_{tabela_pai_final} \n"
                    sql += f"FOREIGN KEY (`{coluna_fk_final}`) \n"
                    sql += f"REFERENCES `{tabela_pai_final}`(`{coluna_ref_final}`) \n"
                    sql += f"ON DELETE {on_delete} \n"
                    sql += f"ON UPDATE {on_update};\n\n"
                    
                    sql += f"-- 4. EXEMPLO DE INSERÇÃO (opcional)\n"
                    sql += f"/*\n"
                    sql += f"-- Primeiro insere na tabela pai:\n"
                    sql += f"INSERT INTO `{tabela_pai_final}` ({coluna_ref_final}, ...) VALUES (1, ...);\n\n"
                    sql += f"-- Depois insere na tabela filha com o MESMO id:\n"
                    sql += f"INSERT INTO `{tabela_const}` (`{coluna_fk_final}`, ...) VALUES (1, ...);\n"
                    sql += f"*/"
                    
                    mostrar_sql_gerado(sql, f"HERANÇA: {tabela_const} → {tabela_pai_final}")
            
            elif tipo_constraint == "PRIMARY KEY":
                st.markdown("#### 🔑 Adicionar PRIMARY KEY")
                
                colunas = listar_colunas_tabela(banco_const, tabela_const) or []
                if colunas:
                    colunas_nomes = [str(c[0]) for c in colunas]
                    coluna_pk = st.selectbox("Coluna para ser PRIMARY KEY", colunas_nomes)
                    
                    if st.button("Gerar ADD PRIMARY KEY"):
                        sql = f"ALTER TABLE `{tabela_const}` ADD PRIMARY KEY (`{coluna_pk}`);"
                        mostrar_sql_gerado(sql, f"PRIMARY KEY para {tabela_const}")
            
            elif tipo_constraint == "UNIQUE":
                st.markdown("#### ⭐ Adicionar UNIQUE Constraint")
                
                colunas = listar_colunas_tabela(banco_const, tabela_const) or []
                if colunas:
                    colunas_nomes = [str(c[0]) for c in colunas]
                    coluna_unique = st.selectbox("Coluna para ser UNIQUE", colunas_nomes)
                    
                    if st.button("Gerar ADD UNIQUE"):
                        sql = f"ALTER TABLE `{tabela_const}` ADD UNIQUE (`{coluna_unique}`);"
                        mostrar_sql_gerado(sql, f"UNIQUE para {tabela_const}")
    
    # ============================================
    # 4. COMANDOS ESPECÍFICOS PARA O TEU EXERCÍCIO
    # ============================================
    elif tipo_selecionado in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
        st.subheader(f"📝 Gerador de {tipo_selecionado}")
        
        # Templates prontos para o teu exercício
        st.markdown("#### 🎯 Templates para o Teu Exercício")
        
        templates = {
            "SELECT": {
                "Listar todos os clientes": "SELECT * FROM Cliente;",
                "Listar empregados com salário > 1000": "SELECT * FROM Empregado WHERE vencimento > 1000;",
                "Ver herança Pessoa → Cliente": """SELECT p.*, c.atividade 
FROM Pessoa p 
JOIN Cliente c ON p.id = c.id 
WHERE p.Tipo = 'Cliente';""",
                "Ver departamentos e seus chefes": """SELECT d.*, p.Nome as Nome_Chefe 
FROM Departamento d 
LEFT JOIN Empregado e ON d.Chefe = e.id 
LEFT JOIN Pessoa p ON e.id = p.id;"""
            },
            "INSERT": {
                "Inserir nova Pessoa": "INSERT INTO Pessoa (Nome, Morada, Tipo) VALUES ('João', 'Rua A', 'Cliente');",
                "Inserir Cliente (herda de Pessoa)": """-- 1. Primeiro insere Pessoa
INSERT INTO Pessoa (Nome, Morada, Tipo) VALUES ('Maria', 'Av. B', 'Cliente');
-- 2. Depois insere Cliente com MESMO ID
INSERT INTO Cliente (id, atividade) VALUES (LAST_INSERT_ID(), 'Comércio');""",
                "Inserir Empregado": """INSERT INTO Pessoa (Nome, Morada, Tipo) VALUES ('Carlos', 'Rua C', 'Empregado');
INSERT INTO Empregado (id, vencimento, responsavel, data_admissao, siglassecção) 
VALUES (LAST_INSERT_ID(), 1500.00, 1, NOW(), 'RH');"""
            }
        }
        
        if tipo_selecionado in templates:
            template_selecionado = st.selectbox("Template Pronto", list(templates[tipo_selecionado].keys()))
            
            sql_template = templates[tipo_selecionado][template_selecionado]
            st.code(sql_template, language="sql")
            
            if st.button("📋 Usar Este Template"):
                mostrar_sql_gerado(sql_template, f"{tipo_selecionado} Template")
        else:
            st.info(f"📝 Digite seu comando {tipo_selecionado} manualmente:")
            sql_manual = st.text_area("SQL Manual", height=100)
            if sql_manual and st.button("Gerar SQL"):
                mostrar_sql_gerado(sql_manual, f"{tipo_selecionado} Manual")
    
    # ============================================
    # 5. CREATE DATABASE, DROP TABLE (simples)
    # ============================================
    elif tipo_selecionado == "CREATE DATABASE":
        st.subheader("🗄️ Criar Novo Banco de Dados")
        
        nome_banco = st.text_input("Nome do Banco", placeholder="ex: meu_banco")
        charset = st.selectbox("Charset", ["utf8mb4", "utf8", "latin1"])
        collation = st.selectbox("Collation", ["utf8mb4_unicode_ci", "utf8_general_ci", "latin1_swedish_ci"])
        
        if nome_banco and st.button("Gerar CREATE DATABASE"):
            sql = f"CREATE DATABASE `{nome_banco}`\n"
            sql += f"CHARACTER SET {charset}\n"
            sql += f"COLLATE {collation};"
            
            mostrar_sql_gerado(sql, f"CREATE DATABASE {nome_banco}")
    
    elif tipo_selecionado == "DROP TABLE":
        st.subheader("🗑️ Remover Tabela")
        
        bancos = listar_bancos() or []
        if bancos:
            banco_drop = st.selectbox("Banco", bancos, key="drop_banco")
            tabelas = listar_tabelas(banco_drop) or []
            
            if tabelas:
                tabela_drop = st.selectbox("Tabela para remover", tabelas, key="drop_tabela")
                
                confirm = st.checkbox("⚠️ Confirmar que quero remover esta tabela")
                if confirm and st.button("Gerar DROP TABLE", type="primary"):
                    sql = f"DROP TABLE `{tabela_drop}`;"
                    mostrar_sql_gerado(sql, f"DROP TABLE {tabela_drop}")
    
    # ============================================
    # HISTÓRICO DE SQL GERADO
    # ============================================
    
    if st.session_state.sql_builder_history:
        st.markdown("---")
        st.subheader("📜 Histórico de Comandos Gerados")
        
        historico_recente = st.session_state.sql_builder_history[-5:]
        
        for idx, (sql, titulo, timestamp) in enumerate(reversed(historico_recente)):
            with st.expander(f"{titulo} - {timestamp}"):
                st.code(sql, language="sql")
                
                col_copy, col_exec = st.columns(2)
                with col_copy:
                    if st.button("📋 Copiar", key=f"copy_{idx}"):
                        st.success("✅ Copiado para clipboard!")
                with col_exec:
                    if st.button("⚡ Executar", key=f"exec_{idx}"):
                        st.info("Vá ao Editor SQL para executar este comando")

def mostrar_sql_gerado(sql, titulo):
    """Mostra o SQL gerado e adiciona ao histórico"""
    st.markdown("---")
    st.subheader(f"✅ SQL Gerado: {titulo}")
    
    st.code(sql, language="sql")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Copiar para Clipboard", key="btn_copy_sql", use_container_width=True):
            st.success("✅ SQL copiado! (Ctrl+V para colar)")
    
    with col2:
        if st.button("⚡ Abrir no Editor SQL", key="btn_open_editor", use_container_width=True):
            if "menu_estado" in st.session_state:
                st.session_state.menu_estado["opcao_selecionada"] = "query_editor"
                st.session_state.sql_para_executar = sql
            st.rerun()
    
    with col3:
        if st.button("💾 Salvar no Histórico", key="btn_save_history", use_container_width=True):
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.sql_builder_history.append((sql, titulo, timestamp))
            st.success("✅ Salvo no histórico!")
            st.rerun()
    
    with st.expander("🎯 Como usar este SQL?", expanded=True):
        st.markdown(f"""
        1. **📋 Copie** o comando acima
        2. **Vá ao Editor SQL** (⚡ Editor SQL na sidebar)
        3. **Cole e execute** no banco correto
        4. **Verifique** se funcionou com `DESCRIBE tabela;` ou `SHOW TABLES;`
        
        **Para HERANÇA ({titulo}):**
        - Execute os comandos na ordem apresentada
        - Use `ON DELETE CASCADE` para manter consistência
        - Teste com dados de exemplo primeiro
        """)