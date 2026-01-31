# query_editor.py - Editor SQL completo COM VISUALIZAÇÃO DE TABELAS
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import io
from io import BytesIO

# Verificar se há banco selecionado
if "banco_ativo" not in st.session_state or not st.session_state.banco_ativo:
    st.error("⚠️ Nenhum banco selecionado!")
    st.info("Selecione um banco na barra lateral primeiro.")
    st.stop()

# Agora pode usar
banco_atual = st.session_state.banco_ativo

# Título principal da página
st.title("📊 Sistema de Banco de Dados")

# ============ FUNÇÃO DE CONEXÃO ============
def conectar_mysql(database=None):
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Sua senha aqui
            database=database
        )
        return conexao
    except Error as e:
        st.error(f"Erro: {e}")
        return None

# ============ FUNÇÃO PARA OBTER TABELAS ============
def obter_tabelas(banco):
    """Retorna lista de tabelas do banco selecionado"""
    try:
        conexao = conectar_mysql(banco)
        if not conexao:
            return []
        
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")
        tabelas = [tabela[0] for tabela in cursor.fetchall()]
        cursor.close()
        conexao.close()
        return tabelas
    except Error as e:
        st.error(f"Erro ao obter tabelas: {e}")
        return []

# ============ FUNÇÃO PARA OBTER ESTRUTURA DA TABELA ============
def obter_estrutura_tabela(banco, tabela):
    """Retorna estrutura (colunas) de uma tabela específica"""
    try:
        conexao = conectar_mysql(banco)
        if not conexao:
            return []
        
        cursor = conexao.cursor()
        cursor.execute(f"DESCRIBE {tabela}")
        estrutura = cursor.fetchall()
        cursor.close()
        conexao.close()
        return estrutura
    except Error as e:
        st.error(f"Erro ao obter estrutura da tabela: {e}")
        return []

# ============ CALLBACK PARA LIMPAR ============
def limpar_editor():
    st.session_state.texto_query = ""

def pagina_query_editor():
    st.title("🔍 Criar Querys em SQL - Versão Pro")
    
    # Inicializar estado do editor se não existir
    if "texto_query" not in st.session_state:
        st.session_state.texto_query = "SELECT 'Hello MySQL' as teste"
    
    # Seção 1: Seleção do banco
    st.subheader("1. 📁 Selecione um Banco")
    
    conexao = conectar_mysql()
    if not conexao:
        st.error("Não foi possível conectar ao MySQL")
        st.stop()
    
    cursor = conexao.cursor()
    cursor.execute("SHOW DATABASES")
    bancos = [db[0] for db in cursor.fetchall() 
             if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
    cursor.close()
    conexao.close()
    
    if not bancos:
        st.error("Nenhum banco disponível!")
        st.stop()
    
    banco_selecionado = st.selectbox("Banco:", bancos, key="banco_selector")
    st.success(f"✅ Banco selecionado: **{banco_selecionado}**")
    
    # ============ NOVA SEÇÃO: VISUALIZAÇÃO DE TABELAS ============
    with st.expander("📊 Visualizar Tabelas do Banco", expanded=True):
        # Obter tabelas do banco selecionado
        tabelas = obter_tabelas(banco_selecionado)
        
        if tabelas:
            st.info(f"📁 **{len(tabelas)} tabela(s)** encontrada(s) no banco `{banco_selecionado}`")
            
            # Criar abas para cada tabela
            tabs = st.tabs([f"📋 {tabela}" for tabela in tabelas])
            
            for i, (tab, tabela) in enumerate(zip(tabs, tabelas)):
                with tab:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Botão para inserir no editor
                        if st.button(f"📝 Usar {tabela}", key=f"btn_use_{tabela}"):
                            st.session_state.texto_query = f"SELECT * FROM {tabela} LIMIT 10;"
                            st.rerun()
                        
                        # Obter estrutura da tabela
                        estrutura = obter_estrutura_tabela(banco_selecionado, tabela)
                        if estrutura:
                            st.markdown("**Estrutura:**")
                            for coluna in estrutura:
                                nome = coluna[0]
                                tipo = coluna[1]
                                st.code(f"{nome}: {tipo}")
                    
                    with col2:
                        # Mostrar preview dos dados
                        try:
                            conexao = conectar_mysql(banco_selecionado)
                            if conexao:
                                cursor = conexao.cursor()
                                cursor.execute(f"SELECT * FROM {tabela} LIMIT 5")
                                dados = cursor.fetchall()
                                
                                if cursor.description:
                                    colunas = [desc[0] for desc in cursor.description]
                                    if dados:
                                        df_preview = pd.DataFrame(dados, columns=colunas)
                                        st.dataframe(df_preview, use_container_width=True)
                                        st.caption(f"Preview: {len(dados)} registros")
                                    else:
                                        st.info("Tabela vazia")
                                else:
                                    st.info("Sem dados para mostrar")
                                
                                cursor.close()
                                conexao.close()
                        except Error as e:
                            st.warning(f"Não foi possível carregar dados: {e}")
        else:
            st.warning(f"⚠️ Nenhuma tabela encontrada no banco `{banco_selecionado}`")
            st.info("Crie uma tabela para começar:")
            st.code(f"""
-- Exemplo de criação de tabela
CREATE DATABASE {banco_selecionado};
USE {banco_selecionado};

CREATE TABLE clientes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    data_cadastro DATE DEFAULT CURRENT_DATE
);
            """, language="sql")
    
    # Seção 2: Editor
    st.subheader("2. 📝 Editor SQL")
    
    # CSS customizado para o text_area
    st.markdown("""
    <style>
        .stTextArea textarea {
            background-color: #001100;  /* Fundo verde muito escuro */
            color: #00FF41;            /* VERDE NEON */
            font-family: 'Monaco', 'Ubuntu Mono', monospace;
            font-size: 15px;
            border: 2px solid #003300;
            text-shadow: 0 0 5px #00FF41;  /* Brilho sutil */
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Text area usando session_state
    query = st.text_area(
        "Digite sua query:",
        value=st.session_state.texto_query,
        height=350,
        placeholder="Ex: SELECT * FROM tabela LIMIT 10;",
        key="editor_sql"
    )
    
    # Atualizar session_state com o texto atual
    st.session_state.texto_query = query
    
    # Botões
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        executar = st.button("▶️ Executar Query", type="primary", use_container_width=True)
    with col2:
        # Botão limpar com callback
        if st.button("🗑️ Limpar Editor", use_container_width=True, on_click=limpar_editor):
            pass  # A ação é feita pelo callback
    with col3:
        exemplos = st.button("📚 Exemplos", use_container_width=True)
    
    if exemplos:
        with st.expander("📚 Exemplos de Queries", expanded=True):
            tab1, tab2, tab3 = st.tabs(["Básico", "Intermediário", "Avançado"])
            
            with tab1:
                st.code("""
-- Ver todas as tabelas
SHOW TABLES;

-- Ver estrutura de uma tabela
DESCRIBE nome_tabela;

-- Selecionar dados com limite
SELECT * FROM nome_tabela LIMIT 10;

-- Contar registros
SELECT COUNT(*) as total FROM nome_tabela;
                """, language="sql")
            
            with tab2:
                st.code("""
-- JOIN entre tabelas
SELECT t1.coluna, t2.coluna
FROM tabela1 t1
INNER JOIN tabela2 t2 ON t1.id = t2.id_tabela1;

-- Agrupamento com função agregada
SELECT categoria, AVG(preco) as media_preco
FROM produtos
GROUP BY categoria
HAVING AVG(preco) > 100;

-- Subquery
SELECT nome FROM clientes
WHERE id IN (
    SELECT cliente_id FROM pedidos
    WHERE data >= '2024-01-01'
);
                """, language="sql")
            
            with tab3:
                st.code("""
-- Window functions
SELECT 
    nome,
    departamento,
    salario,
    RANK() OVER (PARTITION BY departamento ORDER BY salario DESC) as ranking
FROM funcionarios;

-- Common Table Expression (CTE)
WITH vendas_por_mes AS (
    SELECT 
        DATE_FORMAT(data, '%Y-%m') as mes,
        SUM(valor) as total_vendas
    FROM vendas
    GROUP BY DATE_FORMAT(data, '%Y-%m')
)
SELECT * FROM vendas_por_mes
WHERE total_vendas > 10000;

-- Stored procedure call
CALL relatorio_vendas('2024-01-01', '2024-12-31');
                """, language="sql")
    
    # Seção 3: Execução
    if executar and query.strip():
        st.subheader("3. 📊 Resultados")
        
        conexao = conectar_mysql(banco_selecionado)
        if not conexao:
            st.stop()
        
        cursor = conexao.cursor()
        
        try:
            with st.spinner("Executando query..."):
                cursor.execute(query)
                
                if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                    resultados = cursor.fetchall()
                    
                    if cursor.description:
                        colunas = [desc[0] for desc in cursor.description]
                        
                        if resultados:
                            df = pd.DataFrame(resultados, columns=colunas)
                            st.success(f"✅ {len(df)} linha(s) retornada(s)")
                            
                            # Mostrar dataframe
                            st.dataframe(df, use_container_width=True)
                            
                            # Estatísticas
                            with st.expander("📈 Estatísticas"):
                                st.write(f"**Colunas:** {len(df.columns)}")
                                st.write(f"**Linhas:** {len(df)}")
                                st.write("**Tipos de dados:**")
                                tipos = {col: str(dtype) for col, dtype in df.dtypes.items()}
                                st.json(tipos)
                            
                            # Download
                            col_d1, col_d2, col_d3 = st.columns(3)
                            
                            with col_d1:
                                # CSV
                                csv_buffer = df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    "⬇️ Baixar CSV",
                                    csv_buffer,
                                    f"resultados_{banco_selecionado}.csv",
                                    "text/csv",
                                    use_container_width=True
                                )
                            
                            with col_d2:
                                # JSON
                                json_str = df.to_json(orient='records', indent=2)
                                st.download_button(
                                    "⬇️ Baixar JSON",
                                    json_str,
                                    f"resultados_{banco_selecionado}.json",
                                    "application/json",
                                    use_container_width=True
                                )
                            
                            with col_d3:
                                # EXCEL
                                excel_buffer = BytesIO()
                                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                    df.to_excel(writer, index=False, sheet_name='Resultados')
                                
                                excel_data = excel_buffer.getvalue()
                                st.download_button(
                                    "⬇️ Baixar Excel",
                                    excel_data,
                                    f"resultados_{banco_selecionado}.xlsx",
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True
                                )
                        else:
                            st.info("✅ Query executada, mas sem resultados retornados.")
                    else:
                        st.info("✅ Query executada com sucesso (sem descrição de colunas).")
                
                else:
                    linhas = cursor.rowcount
                    conexao.commit()
                    st.success(f"✅ Query executada com sucesso!")
                    st.info(f"**Linhas afetadas:** {linhas}")
                    
                    # Mostrar informações sobre operações DML
                    if query.strip().upper().startswith('INSERT'):
                        st.balloons()
                        st.success("Dados inseridos com sucesso!")
                    elif query.strip().upper().startswith('UPDATE'):
                        st.info(f"Registros atualizados: {linhas}")
                    elif query.strip().upper().startswith('DELETE'):
                        st.warning(f"Registros excluídos: {linhas}")
        
        except Error as e:
            st.error(f"❌ Erro na execução:")
            st.code(str(e), language='text')
            conexao.rollback()
        
        finally:
            cursor.close()
            conexao.close()
    
    # Seção 4: Histórico (simplificado)
    with st.expander("📋 Histórico de Queries (últimas 5)"):
        if "historico_queries" not in st.session_state:
            st.session_state.historico_queries = []
        
        if executar and query.strip():
            # Adicionar ao histórico
            st.session_state.historico_queries.insert(0, {
                "query": query[:100] + ("..." if len(query) > 100 else ""),
                "banco": banco_selecionado,
                "timestamp": pd.Timestamp.now().strftime("%H:%M:%S")
            })
            
            # Manter apenas as últimas 5
            if len(st.session_state.historico_queries) > 5:
                st.session_state.historico_queries.pop()
        
        # Mostrar histórico
        if st.session_state.historico_queries:
            for i, item in enumerate(st.session_state.historico_queries):
                st.text(f"{i+1}. [{item['timestamp']}] {item['banco']}: {item['query']}")
        else:
            st.info("Nenhuma query no histórico ainda.")
    
    # Botão voltar para home
    st.markdown("---")
    
    if st.button("🏠 Voltar para Página Inicial"):
        st.session_state.pagina = "home"
        st.rerun()
        
    # Botão voltar para consultas
    st.markdown("---")
    if st.button("👷 ir para construtor de Consultas"):
        st.session_state.pagina = "criar_consultas"
        st.rerun()    
    
    # Botão voltar para consultas
    
    if st.button("📊 ir para Criar Tabelas"):
        st.session_state.pagina = "criar_tabelas"
        st.rerun()   
        
        st.markdown("---")  