# modules/tabela_visualizar.py
import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional
from io import BytesIO

def get_conexao():
    """Obtém conexão do session_state ou cria nova"""
    if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
        try:
            if st.session_state.conexao_mysql.is_connected():
                return st.session_state.conexao_mysql
        except:
            pass
    return None

def listar_bancos() -> List[str]:
    """Lista todos os bancos de dados disponíveis"""
    conexao = get_conexao()
    if not conexao:
        return []
    
    try:
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        bancos = [db[0] for db in cursor.fetchall() 
                 if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
        cursor.close()
        return bancos
    except Exception as e:
        st.error(f"Erro ao listar bancos: {e}")
        return []

def listar_tabelas(banco: str) -> List[str]:
    """Lista todas as tabelas de um banco específico"""
    conexao = get_conexao()
    if not conexao:
        return []
    
    try:
        cursor = conexao.cursor()
        cursor.execute(f"USE `{banco}`")
        cursor.execute("SHOW TABLES")
        tabelas = [t[0] for t in cursor.fetchall()]
        cursor.close()
        return tabelas
    except Exception as e:
        st.error(f"Erro ao listar tabelas: {e}")
        return []

def obter_estrutura_tabela(banco: str, tabela: str) -> pd.DataFrame:
    """Obtém a estrutura (campos) de uma tabela"""
    conexao = get_conexao()
    if not conexao:
        return pd.DataFrame()
    
    try:
        cursor = conexao.cursor()
        cursor.execute(f"USE `{banco}`")
        cursor.execute(f"DESCRIBE `{tabela}`")
        
        colunas = ["Campo", "Tipo", "Nulo", "Chave", "Default", "Extra"]
        dados = cursor.fetchall()
        
        df = pd.DataFrame(dados, columns=colunas)
        cursor.close()
        return df
    except Exception as e:
        st.error(f"Erro ao obter estrutura: {e}")
        return pd.DataFrame()

def obter_dados_tabela(banco: str, tabela: str, limite: int = 100) -> pd.DataFrame:
    """Obtém os dados de uma tabela com limite"""
    conexao = get_conexao()
    if not conexao:
        return pd.DataFrame()
    
    try:
        cursor = conexao.cursor()
        cursor.execute(f"USE `{banco}`")
        cursor.execute(f"SELECT * FROM `{tabela}` LIMIT {limite}")
        
        # Obter nomes das colunas
        colunas = [desc[0] for desc in cursor.description]
        
        # Obter dados
        dados = cursor.fetchall()
        
        df = pd.DataFrame(dados, columns=colunas)
        cursor.close()
        return df
    except Exception as e:
        st.error(f"Erro ao obter dados: {e}")
        return pd.DataFrame()

def obter_contagem_registros(banco: str, tabela: str) -> int:
    """Obtém o total de registros em uma tabela"""
    conexao = get_conexao()
    if not conexao:
        return 0
    
    try:
        cursor = conexao.cursor()
        cursor.execute(f"USE `{banco}`")
        cursor.execute(f"SELECT COUNT(*) FROM `{tabela}`")
        total = cursor.fetchone()[0]
        cursor.close()
        return total
    except Exception as e:
        st.error(f"Erro ao contar registros: {e}")
        return 0

def obter_chaves_tabela(banco: str, tabela: str) -> Dict:
    """Obtém informações sobre chaves primárias e estrangeiras"""
    conexao = get_conexao()
    if not conexao:
        return {"primarias": [], "estrangeiras": []}
    
    try:
        cursor = conexao.cursor()
        cursor.execute(f"USE `{banco}`")
        
        # Chaves primárias
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = '{banco}' 
            AND TABLE_NAME = '{tabela}' 
            AND CONSTRAINT_NAME = 'PRIMARY'
        """)
        primarias = [row[0] for row in cursor.fetchall()]
        
        # Chaves estrangeiras
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME,
                CONSTRAINT_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = '{banco}' 
            AND TABLE_NAME = '{tabela}' 
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        estrangeiras = cursor.fetchall()
        
        resultado = {
            "primarias": primarias,
            "estrangeiras": estrangeiras
        }
        
        cursor.close()
        return resultado
    except Exception as e:
        st.error(f"Erro ao obter chaves: {e}")
        return {"primarias": [], "estrangeiras": []}

def obter_indices_tabela(banco: str, tabela: str) -> pd.DataFrame:
    """Obtém informações sobre índices da tabela"""
    conexao = get_conexao()
    if not conexao:
        return pd.DataFrame()
    
    try:
        cursor = conexao.cursor()
        cursor.execute(f"USE `{banco}`")
        cursor.execute(f"SHOW INDEX FROM `{tabela}`")
        
        # Obter descrição das colunas
        column_descriptions = cursor.description
        dados = cursor.fetchall()
        
        if not dados:
            cursor.close()
            return pd.DataFrame()
        
        # Verificar quantas colunas foram retornadas
        num_colunas = len(column_descriptions)
        
        # Mapeamento de colunas baseado na versão do MySQL
        if num_colunas == 13:  # MySQL 8.0+
            colunas = [
                "Tabela", "Nao_Unico", "Nome_Indice", 
                "Seq_Indice", "Nome_Coluna", "Colacao", 
                "Cardinalidade", "Sub_parte", "Packed", 
                "Nulo", "Tipo_Indice", "Comentario", "Comentario_Indice"
            ]
        elif num_colunas == 12:  # MySQL 5.x ou versões mais antigas
            colunas = [
                "Tabela", "Nao_Unico", "Nome_Indice", 
                "Seq_Indice", "Nome_Coluna", "Colacao", 
                "Cardinalidade", "Sub_parte", "Packed", 
                "Nulo", "Tipo_Indice", "Comentario"
            ]
        else:
            # Usar nomes das colunas da descrição ou genéricos
            colunas = [desc[0] if desc[0] else f"Coluna_{i}" 
                      for i, desc in enumerate(column_descriptions)]
        
        # Criar DataFrame
        df = pd.DataFrame(dados, columns=colunas)
        cursor.close()
        
        # Renomear para português se necessário
        if 'Non_unique' in df.columns:
            df = df.rename(columns={'Non_unique': 'Nao_Unico'})
        if 'Key_name' in df.columns:
            df = df.rename(columns={'Key_name': 'Nome_Indice'})
        if 'Column_name' in df.columns:
            df = df.rename(columns={'Column_name': 'Nome_Coluna'})
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao obter índices: {e}")
        return pd.DataFrame()

# ============ INTERFACE PRINCIPAL ============
def pagina_visualizar_tabela():
    """Página principal para visualizar tabelas"""
    st.title("👁️ Visualizador de Tabelas")
    
    # Verificar conexão
    conexao = get_conexao()
    if not conexao:
        st.warning("⚠️ Não há conexão com o MySQL")
        if st.button("🔄 Tentar Conectar"):
            from app import conectar_mysql
            st.session_state.conexao_mysql = conectar_mysql()
            st.rerun()
        return
    
    st.markdown("Visualize tabelas, seus campos e dados de forma interativa.")
    
    # Seleção de banco de dados
    bancos = listar_bancos()
    
    if not bancos:
        st.info("📭 Nenhum banco de dados encontrado")
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        banco_selecionado = st.selectbox(
            "Selecione o banco de dados:",
            bancos,
            index=0,
            help="Escolha o banco que contém as tabelas que deseja visualizar"
        )
    
    with col2:
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.rerun()
    
    # Seleção de tabela
    tabelas = listar_tabelas(banco_selecionado)
    
    if not tabelas:
        st.info(f"📭 Nenhuma tabela encontrada no banco '{banco_selecionado}'")
        return
    
    tabela_selecionada = st.selectbox(
        "Selecione a tabela:",
        tabelas,
        index=0,
        help="Escolha a tabela que deseja visualizar"
    )
    
    st.markdown("---")
    
    # Abas para diferentes visualizações
    tab_estrutura, tab_dados, tab_estatisticas, tab_sql = st.tabs([
        "🏗️ Estrutura", 
        "📊 Dados", 
        "📈 Estatísticas", 
        "🔍 SQL"
    ])
    
    with tab_estrutura:
        visualizar_estrutura(banco_selecionado, tabela_selecionada)
    
    with tab_dados:
        visualizar_dados(banco_selecionado, tabela_selecionada)
    
    with tab_estatisticas:
        visualizar_estatisticas(banco_selecionado, tabela_selecionada)
    
    with tab_sql:
        visualizar_sql(banco_selecionado, tabela_selecionada)

# ============ FUNÇÕES DE VISUALIZAÇÃO ============
def visualizar_estrutura(banco: str, tabela: str):
    """Visualiza a estrutura da tabela"""
    st.subheader("🏗️ Estrutura da Tabela")
    
    # Obter estrutura
    df_estrutura = obter_estrutura_tabela(banco, tabela)
    
    if df_estrutura.empty:
        st.info("Não foi possível obter a estrutura da tabela")
        return
    
    # Mostrar estrutura
    st.dataframe(
        df_estrutura,
        use_container_width=True,
        hide_index=True
    )
    
    # Informações adicionais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_campos = len(df_estrutura)
        st.metric("Total de Campos", total_campos)
    
    with col2:
        campos_nulos = df_estrutura[df_estrutura["Nulo"] == "YES"].shape[0]
        st.metric("Campos Nulos", campos_nulos)
    
    with col3:
        campos_chave = df_estrutura[df_estrutura["Chave"] != ""].shape[0]
        st.metric("Campos com Chave", campos_chave)
    
    # Chaves da tabela
    st.subheader("🔑 Chaves da Tabela")
    chaves = obter_chaves_tabela(banco, tabela)
    
    col_ch1, col_ch2 = st.columns(2)
    
    with col_ch1:
        if chaves["primarias"]:
            st.write("**Chave(s) Primária(s):**")
            for chave in chaves["primarias"]:
                st.code(chave)
        else:
            st.info("Sem chave primária definida")
    
    with col_ch2:
        if chaves["estrangeiras"]:
            st.write("**Chave(s) Estrangeira(s):**")
            for chave in chaves["estrangeiras"]:
                coluna, constraint, tabela_ref, coluna_ref = chave
                st.write(f"**{coluna}** → {tabela_ref}.{coluna_ref}")
        else:
            st.info("Sem chaves estrangeiras")
    
        # Índices
    st.subheader("📑 Índices da Tabela")
    df_indices = obter_indices_tabela(banco, tabela)
    
    if not df_indices.empty:
        # Selecionar apenas colunas que existem
        colunas_possiveis = ["Nome_Indice", "Nome_Coluna", "Tipo_Indice", "Nao_Unico", "Nulo"]
        colunas_existentes = [col for col in colunas_possiveis if col in df_indices.columns]
        
        if colunas_existentes:
            st.dataframe(
                df_indices[colunas_existentes],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(
                df_indices,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Nenhum índice definido")

def visualizar_dados(banco: str, tabela: str):
    """Visualiza os dados da tabela"""
    st.subheader("📊 Dados da Tabela")
    
    # Controle de limite
    col_lim1, col_lim2 = st.columns([3, 1])
    
    with col_lim1:
        limite = st.slider(
            "Quantidade de registros:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Limite de registros a exibir"
        )
    
    with col_lim2:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.rerun()
    
    # Obter dados
    df_dados = obter_dados_tabela(banco, tabela, limite)
    
    if df_dados.empty:
        st.info("A tabela está vazia ou não foi possível obter os dados")
        return
    
    # Estatísticas rápidas
    total_registros = obter_contagem_registros(banco, tabela)
    
    st.info(f"**Total de registros na tabela:** {total_registros:,}")
    st.info(f"**Mostrando:** {len(df_dados):,} de {total_registros:,} registros")
    
    # Visualizar dados
    st.dataframe(
        df_dados,
        use_container_width=True,
        height=400
    )
    
    # Opções de visualização
    with st.expander("⚙️ Opções de Visualização"):
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            mostrar_tipos = st.checkbox("Mostrar tipos de dados", value=False)
            if mostrar_tipos:
                st.write("**Tipos de dados das colunas:**")
                for coluna in df_dados.columns:
                    tipo = str(df_dados[coluna].dtype)
                    st.write(f"• {coluna}: `{tipo}`")
        
        with col_opt2:
            formato_download = st.radio(
                "Formato para download:",
                ["CSV", "Excel", "JSON"],
                horizontal=True
            )
            
            if st.button("💾 Baixar Dados"):
                buffer = BytesIO()
                
                if formato_download == "CSV":
                    df_dados.to_csv(buffer, index=False, encoding='utf-8')
                    mime_type = "text/csv"
                    extensao = "csv"
                elif formato_download == "Excel":
                    df_dados.to_excel(buffer, index=False)
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    extensao = "xlsx"
                else:  # JSON
                    df_dados.to_json(buffer, orient='records', indent=2)
                    mime_type = "application/json"
                    extensao = "json"
                
                buffer.seek(0)
                
                st.download_button(
                    label=f"⬇️ Baixar {formato_download}",
                    data=buffer,
                    file_name=f"{tabela}_dados.{extensao}",
                    mime=mime_type,
                    use_container_width=True
                )

def visualizar_estatisticas(banco: str, tabela: str):
    """Visualiza estatísticas da tabela"""
    st.subheader("📈 Estatísticas da Tabela")
    
    # Obter dados para estatísticas
    df_dados = obter_dados_tabela(banco, tabela, 1000)
    
    if df_dados.empty:
        st.info("Não há dados suficientes para análise estatística")
        return
    
    # Métricas principais
    total_registros = obter_contagem_registros(banco, tabela)
    
    col_met1, col_met2, col_met3 = st.columns(3)
    
    with col_met1:
        st.metric("Total de Registros", f"{total_registros:,}")
    
    with col_met2:
        colunas = len(df_dados.columns)
        st.metric("Total de Colunas", colunas)
    
    with col_met3:
        linhas_exibidas = len(df_dados)
        st.metric("Registros Carregados", linhas_exibidas)
    
    # Tipos de dados
    st.subheader("📋 Tipos de Dados")
    
    tipos_contagem = {}
    for coluna in df_dados.columns:
        tipo = str(df_dados[coluna].dtype)
        tipos_contagem[tipo] = tipos_contagem.get(tipo, 0) + 1
    
    if tipos_contagem:
        df_tipos = pd.DataFrame({
            "Tipo de Dado": list(tipos_contagem.keys()),
            "Quantidade": list(tipos_contagem.values())
        })
        
        st.dataframe(
            df_tipos,
            use_container_width=True,
            hide_index=True
        )
    
        # Valores nulos - VERSÃO SIMPLIFICADA
    st.subheader("🔍 Valores Nulos")
    
    if len(df_dados) > 0:
        # Lista para armazenar resultados
        resultados = []
        
        for coluna in df_dados.columns:
            valores_nulos = df_dados[coluna].isnull().sum()
            percentual = (valores_nulos / len(df_dados) * 100) if len(df_dados) > 0 else 0
            
            if valores_nulos > 0:
                resultados.append({
                    "Coluna": coluna,
                    "Valores Nulos": valores_nulos,
                    "Percentual": round(percentual, 2)
                })
        
        if resultados:
            df_nulos = pd.DataFrame(resultados)
            st.dataframe(
                df_nulos,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ Nenhum valor nulo encontrado!")
    else:
        st.info("Não há dados para analisar valores nulos")
    
    # Estatísticas descritivas
    st.subheader("📊 Estatísticas Descritivas")
    
    colunas_numericas = df_dados.select_dtypes(include=['int64', 'float64']).columns
    
    if len(colunas_numericas) > 0:
        df_descricao = df_dados[colunas_numericas].describe().T
        st.dataframe(
            df_descricao,
            use_container_width=True
        )
    else:
        st.info("Não há colunas numéricas para análise estatística")

def visualizar_sql(banco: str, tabela: str):
    """Mostra informações SQL da tabela"""
    st.subheader("🔍 Informações SQL")
    
    # CREATE TABLE statement
    st.markdown("#### 📝 Comando CREATE TABLE")
    
    conexao = get_conexao()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute(f"USE `{banco}`")
            cursor.execute(f"SHOW CREATE TABLE `{tabela}`")
            
            resultado = cursor.fetchone()
            if resultado and len(resultado) > 1:
                create_statement = resultado[1]
                
                st.code(create_statement, language="sql")
                
                # Botão para copiar
                if st.button("📋 Copiar CREATE TABLE", use_container_width=True):
                    st.code(create_statement, language="sql")
                    st.success("Comando copiado para a área de transferência!")
            else:
                st.info("Não foi possível obter o comando CREATE TABLE")
            
            cursor.close()
        except Exception as e:
            st.error(f"Erro: {e}")
    
    # Consultas úteis
    st.markdown("#### 🛠️ Consultas Úteis")
    
    consultas = {
        "Selecionar todos os dados": f"SELECT * FROM `{tabela}`;",
        "Contar registros": f"SELECT COUNT(*) FROM `{tabela}`;",
        "Ver estrutura": f"DESCRIBE `{tabela}`;",
        "Ver índices": f"SHOW INDEX FROM `{tabela}`;",
        "Consultar informações": f"SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tabela}';"
    }
    
    for titulo, consulta in consultas.items():
        with st.expander(f"📌 {titulo}"):
            st.code(consulta, language="sql")
            if st.button("📋 Copiar", key=f"copy_{titulo}"):
                st.success("Copiado!")

# ============ FUNÇÃO PARA INTEGRAÇÃO COM APP.PY ============
def pagina_visualizar():
    """Função para ser chamada do app.py"""
    pagina_visualizar_tabela()

# Execução direta para testes
if __name__ == "__main__":
    st.set_page_config(page_title="Visualizador de Tabelas", layout="wide")
    pagina_visualizar_tabela()