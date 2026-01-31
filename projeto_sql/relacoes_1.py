# relacoes.py - Versão simplificada que funciona com seu app.py
import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

def conectar_banco(database=None):
    """Conecta ao MySQL usando sua conexão existente"""
    if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
        return st.session_state.conexao_mysql
    
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=database
        )
        return conexao
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

def pagina_relacoes():
    """Página de relações que funciona com seu app.py"""
    
    st.title("🔗 Relações entre Tabelas")
    st.markdown("Analise as relações (FOREIGN KEYS) entre tabelas do seu banco.")
    
    # Verificar conexão
    conexao = conectar_banco()
    if not conexao or not conexao.is_connected():
        st.warning("⚠️ Conecte-se ao MySQL primeiro!")
        
        # Mostrar bancos disponíveis para seleção
        try:
            cursor = conexao.cursor()
            cursor.execute("SHOW DATABASES")
            todos_bancos = [db[0] for db in cursor.fetchall()]
            cursor.close()
            
            bancos = [b for b in todos_bancos if b not in [
                'information_schema', 'mysql', 'performance_schema', 'sys'
            ]]
            
            if bancos:
                banco_selecionado = st.selectbox(
                    "Selecione um banco de dados:",
                    options=["Selecione um banco"] + bancos
                )
                
                if banco_selecionado != "Selecione um banco":
                    try:
                        cursor = conexao.cursor()
                        cursor.execute(f"USE {banco_selecionado}")
                        cursor.close()
                        st.success(f"✅ Banco {banco_selecionado} selecionado!")
                        st.rerun()
                    except:
                        st.error(f"Não foi possível usar o banco {banco_selecionado}")
            else:
                st.info("Nenhum banco de dados encontrado.")
        except:
            st.info("Não foi possível listar os bancos.")
        
        return
    
    # Obter banco atual
    cursor = conexao.cursor()
    cursor.execute("SELECT DATABASE()")
    banco_atual = cursor.fetchone()[0]
    cursor.close()
    
    if not banco_atual:
        st.warning("Nenhum banco selecionado. Use um banco primeiro.")
        return
    
    st.success(f"📂 Banco atual: **{banco_atual}**")
    
    # Criar abas
    tab1, tab2, tab3 = st.tabs(["📋 Relações", "📊 Estatísticas", "🔍 Explorar"])
    
    with tab1:
        # Obter relações do banco
        try:
            cursor = conexao.cursor(dictionary=True)
            
            query = """
            SELECT 
                TABLE_NAME as tabela_origem,
                COLUMN_NAME as coluna_origem,
                REFERENCED_TABLE_NAME as tabela_destino,
                REFERENCED_COLUMN_NAME as coluna_destino
            FROM 
                INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE 
                TABLE_SCHEMA = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY 
                TABLE_NAME, COLUMN_NAME
            """
            
            cursor.execute(query, (banco_atual,))
            relacoes = cursor.fetchall()
            cursor.close()
            
            if relacoes:
                st.subheader(f"📊 {len(relacoes)} Relações Encontradas")
                
                # Criar DataFrame
                dados = []
                for rel in relacoes:
                    dados.append({
                        "Tabela Origem": rel['tabela_origem'],
                        "Coluna": rel['coluna_origem'],
                        "→": "→",
                        "Tabela Destino": rel['tabela_destino'],
                        "Coluna Referência": rel['coluna_destino']
                    })
                
                df = pd.DataFrame(dados)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Estatísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    tabelas_unicas = set()
                    for rel in relacoes:
                        tabelas_unicas.add(rel['tabela_origem'])
                        tabelas_unicas.add(rel['tabela_destino'])
                    st.metric("Tabelas Relacionadas", len(tabelas_unicas))
                
                with col2:
                    # Contar tabelas que são apenas origem
                    tabelas_origem = set(rel['tabela_origem'] for rel in relacoes)
                    st.metric("Tabelas com FK", len(tabelas_origem))
                
                with col3:
                    # Contar tabelas que são apenas destino
                    tabelas_destino = set(rel['tabela_destino'] for rel in relacoes)
                    st.metric("Tabelas Referenciadas", len(tabelas_destino))
                
                # Gráfico simples
                st.subheader("📈 Distribuição de Relações")
                
                # Contar relações por tabela origem
                contagem = {}
                for rel in relacoes:
                    tabela = rel['tabela_origem']
                    contagem[tabela] = contagem.get(tabela, 0) + 1
                
                if contagem:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    tabelas = list(contagem.keys())
                    valores = list(contagem.values())
                    
                    ax.barh(tabelas, valores)
                    ax.set_xlabel('Número de Relações (FK)')
                    ax.set_title('Relações por Tabela')
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
            
            else:
                st.info("ℹ️ Este banco não possui relações (FOREIGN KEYS) entre tabelas.")
                
        except Exception as e:
            st.error(f"Erro ao obter relações: {e}")
    
    with tab2:
        st.subheader("📊 Estatísticas do Banco")
        
        try:
            # Listar tabelas
            cursor = conexao.cursor()
            cursor.execute("SHOW TABLES")
            tabelas = [t[0] for t in cursor.fetchall()]
            
            if tabelas:
                # Coletar estatísticas
                dados_tabelas = []
                for tabela in tabelas:
                    cursor.execute(f"DESCRIBE {tabela}")
                    colunas = cursor.fetchall()
                    
                    num_pk = sum(1 for c in colunas if 'PRI' in str(c[3]))
                    num_fk = sum(1 for c in colunas if 'MUL' in str(c[3]))
                    
                    dados_tabelas.append({
                        "Tabela": tabela,
                        "Colunas": len(colunas),
                        "PK": num_pk,
                        "FK": num_fk
                    })
                
                df_tabelas = pd.DataFrame(dados_tabelas)
                st.dataframe(df_tabelas, use_container_width=True, hide_index=True)
                
                # Totais
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tabelas", len(tabelas))
                with col2:
                    st.metric("Total Colunas", df_tabelas['Colunas'].sum())
                with col3:
                    st.metric("Chaves Primárias", df_tabelas['PK'].sum())
                with col4:
                    st.metric("Chaves Estrangeiras", df_tabelas['FK'].sum())
            
            cursor.close()
            
        except Exception as e:
            st.error(f"Erro ao obter estatísticas: {e}")
    
    with tab3:
        st.subheader("🔍 Explorar Relações")
        
        # Selecionar uma tabela para ver detalhes
        try:
            cursor = conexao.cursor()
            cursor.execute("SHOW TABLES")
            tabelas = [t[0] for t in cursor.fetchall()]
            
            if tabelas:
                tabela_selecionada = st.selectbox(
                    "Selecione uma tabela para ver detalhes:",
                    tabelas
                )
                
                if tabela_selecionada:
                    # Obter colunas da tabela
                    cursor.execute(f"DESCRIBE {tabela_selecionada}")
                    colunas = cursor.fetchall()
                    
                    st.write(f"**Colunas da tabela `{tabela_selecionada}`:**")
                    
                    dados_colunas = []
                    for col in colunas:
                        tipo_chave = ""
                        if 'PRI' in str(col[3]):
                            tipo_chave = "🔑 PRIMARY KEY"
                        elif 'MUL' in str(col[3]):
                            tipo_chave = "🔗 FOREIGN KEY"
                        elif 'UNI' in str(col[3]):
                            tipo_chave = "⭐ UNIQUE"
                        
                        dados_colunas.append({
                            "Coluna": col[0],
                            "Tipo": col[1],
                            "Nulo": "✅" if col[2] == "YES" else "❌",
                            "Chave": tipo_chave,
                            "Default": str(col[4]) if col[4] else ""
                        })
                    
                    df_colunas = pd.DataFrame(dados_colunas)
                    st.dataframe(df_colunas, use_container_width=True, hide_index=True)
            
            cursor.close()
            
        except Exception as e:
            st.error(f"Erro ao explorar tabela: {e}")
    
    # Botão para voltar
    st.markdown("---")
    if st.button("🏠 Voltar para Página Inicial", use_container_width=True):
        st.session_state.pagina = "home"
        st.rerun()
        
    # Botão para voltar
    st.markdown("---")
    if st.button("🏠 Voltar para Página criar tabelas", use_container_width=True):
        st.session_state.pagina = "criar_tabelas"
        st.rerun()        