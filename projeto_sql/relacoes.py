# relacoes_1.py - VERSÃO FINAL CORRIGIDA (PROBLEMA DE TABELAS COM MESMO NOME)
import streamlit as st
import pandas as pd
import mysql.connector
import networkx as nx
import matplotlib.pyplot as plt
import io

# ============ SISTEMA DE RESET AUTOMÁTICO ============
def reset_relacoes_state():
    """LIMPA COMPLETAMENTE todos os estados de relações"""
    keys_to_remove = [
        'relacoes_cache',
        'grafo_cache', 
        'tabelas_cache',
        'buscar_relacoes',
        'banco_anterior',
        'debug_data'
    ]
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

# ============ CONFIGURAÇÃO INICIAL ============
try:
    from config_global import (
        init_global_state, 
        get_banco_ativo, 
        set_banco_ativo, 
        listar_bancos_disponiveis, 
        get_conexao_global
    )
    
    init_global_state()
    CONFIG_GLOBAL_DISPONIVEL = True
except ImportError:
    CONFIG_GLOBAL_DISPONIVEL = False

# ============ SISTEMA DE CACHE POR BANCO ============
def get_cache_key(banco):
    """Gera chave única de cache para cada banco"""
    return f"relacoes_cache_{banco}"

def get_grafo_cache_key(banco):
    """Gera chave única para grafo de cada banco"""
    return f"grafo_cache_{banco}"

def get_tabelas_cache_key(banco):
    """Gera chave única para tabelas de cada banco"""
    return f"tabelas_cache_{banco}"

# ============ CONEXÃO LIMPA POR BANCO ============
def conectar_banco(database=None):
    """Sempre cria NOVA conexão para evitar cache"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=database,
            autocommit=True
        )
        return conexao
    except Exception as e:
        st.error(f"Erro ao conectar a '{database}': {e}")
        return None

# ============ LISTAGEM LIMPA DE TABELAS ============
def listar_tabelas_fresh(database):
    """Sempre busca tabelas FRESCAS do banco"""
    try:
        conexao = conectar_banco(database)
        if not conexao:
            return []
        
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")
        tabelas = [t[0] for t in cursor.fetchall()]
        cursor.close()
        conexao.close()
        
        return tabelas
    except Exception as e:
        return []

# ============ VERIFICAÇÃO DE TABELA POR BANCO ============
def verificar_tabela_pertence_ao_banco(tabela, database):
    """Verifica se uma tabela realmente pertence ao banco especificado"""
    try:
        conexao = conectar_banco(None)  # Conexão sem banco específico
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s
        """, (database, tabela))
        resultado = cursor.fetchone()[0]
        cursor.close()
        conexao.close()
        return resultado > 0
    except Exception as e:
        return False

# ============ BUSCA DE RELAÇÕES COMPLETAMENTE ISOLADA ============
def buscar_relacoes_fresh(database):
    """Busca relações APENAS do banco especificado - VERSÃO ULTRA-FILTRADA"""
    try:
        # Conectar SEM banco para acessar INFORMATION_SCHEMA
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conexao.cursor(dictionary=True)
        
        # CONSULTA ULTRA-FILTRADA: Isola completamente cada banco
        query = """
        SELECT 
            kcu.TABLE_NAME as tabela_origem,
            kcu.COLUMN_NAME as coluna_origem,
            kcu.REFERENCED_TABLE_NAME as tabela_destino,
            kcu.REFERENCED_COLUMN_NAME as coluna_destino
        FROM 
            INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        INNER JOIN INFORMATION_SCHEMA.TABLES t1 
            ON t1.TABLE_SCHEMA = kcu.TABLE_SCHEMA 
            AND t1.TABLE_NAME = kcu.TABLE_NAME
        INNER JOIN INFORMATION_SCHEMA.TABLES t2 
            ON t2.TABLE_SCHEMA = kcu.REFERENCED_TABLE_SCHEMA 
            AND t2.TABLE_NAME = kcu.REFERENCED_TABLE_NAME
        WHERE 
            kcu.TABLE_SCHEMA = %s  -- Banco da tabela de origem
            AND kcu.REFERENCED_TABLE_SCHEMA = %s  -- Banco da tabela referenciada
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL  -- É chave estrangeira
            AND t1.TABLE_SCHEMA = %s  -- Verificação extra
            AND t2.TABLE_SCHEMA = %s  -- Verificação extra
        ORDER BY 
            kcu.TABLE_NAME, kcu.COLUMN_NAME
        """
        
        cursor.execute(query, (database, database, database, database))
        relacoes = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        if not relacoes:
            return []
        
        # VERIFICAÇÃO EXTRA: garantir que NENHUMA relação venha de outro banco
        relacoes_validas = []
        for rel in relacoes:
            # Verificar AMBAS as tabelas pertencem ao banco
            origem_ok = verificar_tabela_pertence_ao_banco(rel['tabela_origem'], database)
            destino_ok = verificar_tabela_pertence_ao_banco(rel['tabela_destino'], database)
            
            if origem_ok and destino_ok:
                rel['banco'] = database
                relacoes_validas.append(rel)
            else:
                # DEBUG: Mostrar relações rejeitadas
                print(f"REJEITADO: {rel['tabela_origem']} -> {rel['tabela_destino']} "
                      f"(origem_ok={origem_ok}, destino_ok={destino_ok})")
        
        return relacoes_validas
        
    except Exception as e:
        st.error(f"Erro ao buscar relações de '{database}': {e}")
        return []

# ============ BUSCA ALTERNATIVA: USANDO SHOW CREATE TABLE ============
def buscar_relacoes_via_show_create(database):
    """Busca relações usando SHOW CREATE TABLE - método mais direto e seguro"""
    try:
        conexao = conectar_banco(database)
        if not conexao:
            return []
        
        cursor = conexao.cursor(dictionary=True)
        
        # Primeiro, pegar todas as tabelas do banco
        cursor.execute("SHOW TABLES")
        tabelas = [t[0] for t in cursor.fetchall()]
        
        relacoes = []
        
        # Para cada tabela, verificar suas chaves estrangeiras
        for tabela in tabelas:
            cursor.execute(f"SHOW CREATE TABLE `{tabela}`")
            create_stmt = cursor.fetchone()
            
            if create_stmt and 'Create Table' in create_stmt:
                create_sql = create_stmt['Create Table']
                
                # Analisar o SQL para encontrar FOREIGN KEY
                lines = create_sql.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('CONSTRAINT') and 'FOREIGN KEY' in line:
                        # Extrair informações da chave estrangeira
                        # Exemplo: CONSTRAINT `fk_cliente_pessoa` FOREIGN KEY (`id_pessoa`) REFERENCES `pessoa` (`id`)
                        
                        # Procurar REFERENCES
                        if 'REFERENCES' in line:
                            parts = line.split('REFERENCES')
                            if len(parts) == 2:
                                ref_part = parts[1].strip()
                                
                                # Extrair tabela e coluna de destino
                                # Formato: `pessoa` (`id`)
                                ref_part = ref_part.replace('`', '')
                                destino_parts = ref_part.split('(')
                                
                                if len(destino_parts) == 2:
                                    tabela_destino = destino_parts[0].strip()
                                    coluna_destino = destino_parts[1].replace(')', '').strip()
                                    
                                    # Procurar coluna de origem
                                    if 'FOREIGN KEY' in line:
                                        fk_part = line.split('FOREIGN KEY')[1].split('REFERENCES')[0]
                                        fk_part = fk_part.replace('`', '').replace('(', '').replace(')', '').strip()
                                        coluna_origem = fk_part
                                        
                                        # Adicionar relação
                                        relacoes.append({
                                            'tabela_origem': tabela,
                                            'coluna_origem': coluna_origem,
                                            'tabela_destino': tabela_destino,
                                            'coluna_destino': coluna_destino,
                                            'banco': database
                                        })
        
        cursor.close()
        conexao.close()
        
        return relacoes
        
    except Exception as e:
        st.error(f"Erro na busca via SHOW CREATE: {e}")
        return []

# ============ SELEÇÃO DE BANCO COM LIMPEZA AUTOMÁTICA ============
def componente_selecao_banco_com_limpeza():
    """Componente que LIMPA tudo ao mudar de banco"""
    
    # Usar config_global se disponível
    if CONFIG_GLOBAL_DISPONIVEL:
        bancos = listar_bancos_disponiveis()
        banco_atual = get_banco_ativo()
    else:
        bancos = listar_bancos_local()
        banco_atual = st.session_state.get("banco_selecionado_relacoes")
    
    if not bancos:
        st.error("❌ Nenhum banco encontrado!")
        return None
    
    # Verificar se mudou de banco
    banco_anterior = st.session_state.get("banco_anterior_relacoes")
    
    # Container para seleção
    with st.container(border=True):
        st.markdown("### 🏦 Selecione um Banco de Dados")
        
        col_selecao, col_acao, col_status = st.columns([3, 1, 2])
        
        with col_selecao:
            banco_selecionado = st.selectbox(
                "Escolha o banco:",
                bancos,
                index=bancos.index(banco_atual) if banco_atual in bancos else 0,
                label_visibility="collapsed",
                key="select_banco_com_limpeza"
            )
        
        with col_acao:
            st.write("⠀")
            aplicar = st.button("✅ Aplicar", type="primary", use_container_width=True,
                              help="Limpa cache anterior e busca dados novos")
        
        with col_status:
            if banco_anterior and banco_selecionado != banco_anterior:
                st.warning("⚠️ Banco alterado - Cache será limpo!")
        
        # Aplicar seleção COM LIMPEZA
        if aplicar:
            # Se mudou de banco, LIMPAR TUDO
            if banco_selecionado != banco_anterior:
                reset_relacoes_state()
            
            # Atualizar banco
            if CONFIG_GLOBAL_DISPONIVEL:
                if banco_selecionado != get_banco_ativo():
                    set_banco_ativo(banco_selecionado)
            else:
                st.session_state.banco_selecionado_relacoes = banco_selecionado
            
            # Salvar banco anterior para comparação futura
            st.session_state.banco_anterior_relacoes = banco_selecionado
            
            # Forçar busca nova
            st.session_state.buscar_relacoes = False
            
            st.rerun()
    
    # Retornar banco atual
    if CONFIG_GLOBAL_DISPONIVEL:
        banco_ativo = get_banco_ativo()
    else:
        banco_ativo = st.session_state.get("banco_selecionado_relacoes")
    
    if banco_ativo:
        st.info(f"**Banco ativo:** **{banco_ativo}**")
        
        # Mostrar contagem de tabelas FRESCA
        tabelas = listar_tabelas_fresh(banco_ativo)
        if tabelas:
            st.success(f"📊 {len(tabelas)} tabelas encontradas")
    
    return banco_ativo

def listar_bancos_local():
    """Lista bancos sem config_global"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        todos_bancos = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conexao.close()
        
        bancos = [b for b in todos_bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
        return bancos
    except:
        return []

# ============ GERAÇÃO DE GRAFO CORRIGIDO ============
def criar_grafo_limpo(database, relacoes):
    """Cria grafo APENAS com dados do banco atual - VERSÃO CORRIGIDA"""
    if not relacoes:
        return None, "Nenhuma relação encontrada"
    
    try:
        G = nx.DiGraph()
        G.name = f"Relações - {database}"
        
        # Buscar tabelas APENAS deste banco
        tabelas_do_banco = listar_tabelas_fresh(database)
        
        # Adicionar apenas tabelas DESTE banco
        for tabela in tabelas_do_banco:
            G.add_node(tabela, banco=database)
        
        # Adicionar apenas relações DESTE banco
        for rel in relacoes:
            origem = rel['tabela_origem']
            destino = rel['tabela_destino']
            
            # Verificar se AMBAS estão nas tabelas do banco
            if origem in tabelas_do_banco and destino in tabelas_do_banco:
                label = f"{rel['coluna_origem']} → {rel['coluna_destino']}"
                G.add_edge(origem, destino, label=label, banco=database)
        
        # Verificar integridade
        tabelas_no_grafo = list(G.nodes())
        relacoes_no_grafo = list(G.edges())
        
        if len(tabelas_no_grafo) == 0:
            return None, f"Nenhuma tabela válida encontrada em '{database}'"
        
        if len(relacoes_no_grafo) == 0:
            return None, f"Nenhuma relação válida encontrada em '{database}'"
        
        return G, None
        
    except Exception as e:
        return None, f"Erro ao criar grafo: {e}"

def plotar_grafo_limpo(G, database):
    """Plota grafo com título específico do banco"""
    try:
        fig, ax = plt.subplots(figsize=(12, 10))
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        nx.draw_networkx_nodes(G, pos, node_size=3000, 
                              node_color='lightblue', alpha=0.9, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='gray', 
                              arrows=True, arrowsize=20, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=10, 
                               font_weight='bold', ax=ax)
        
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                    font_size=8, ax=ax)
        
        ax.set_title(f"📊 Banco: {database} | Tabelas: {len(G.nodes())} | Relações: {len(G.edges())}", 
                    fontsize=16, fontweight='bold')
        ax.axis('off')
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
        
    except Exception as e:
        st.error(f"Erro ao plotar: {e}")
        return None

# ============ PÁGINA PRINCIPAL CORRIGIDA ============
def pagina_relacoes():
    """Página principal com métodos de busca alternativos"""
    
    st.title("🔗 Visualizador de Relações entre Tabelas")
    st.markdown("**CORRIGIDO:** Cada banco é completamente isolado - sem misturar tabelas com mesmo nome")
    
    # ========== BOTÃO DE LIMPEZA MANUAL ==========
    col_limpar, col_info = st.columns([1, 3])
    
    with col_limpar:
        if st.button("🧹 Limpar Todo o Cache", type="secondary", use_container_width=True):
            reset_relacoes_state()
            st.success("✅ Cache limpo! Selecione um banco novamente.")
            st.rerun()
    
    with col_info:
        st.info("💡 **Solução:** Usa SHOW CREATE TABLE para evitar problemas do INFORMATION_SCHEMA")
    
    # ========== SELEÇÃO DE BANCO COM LIMPEZA ==========
    st.markdown("---")
    banco = componente_selecao_banco_com_limpeza()
    
    if not banco:
        return
    
    st.markdown("---")
    
    # ========== MÉTODO DE BUSCA ==========
    st.markdown("### 🔧 Escolha o método de busca:")
    
    col_metodo1, col_metodo2 = st.columns(2)
    
    with col_metodo1:
        usar_infoschema = st.checkbox(
            "Usar INFORMATION_SCHEMA (rápido)", 
            value=True,
            help="Método tradicional, pode misturar bancos se tabelas tiverem nomes iguais"
        )
    
    with col_metodo2:
        usar_show_create = st.checkbox(
            "Usar SHOW CREATE TABLE (lento mas preciso)", 
            value=False,
            help="Método direto, isola completamente cada banco"
        )
    
    # Se ambos desmarcados, marcar o primeiro
    if not usar_infoschema and not usar_show_create:
        usar_infoschema = True
    
    # ========== VERIFICAR SE MUDOU DE BANCO ==========
    banco_anterior = st.session_state.get("banco_anterior_relacoes")
    
    # Se mudou de banco, forçar busca nova
    if banco_anterior != banco:
        st.warning(f"⚠️ Banco alterado de '{banco_anterior}' para '{banco}'. Buscando novos dados...")
        reset_relacoes_state()
        st.session_state.banco_anterior_relacoes = banco
        st.session_state.buscar_relacoes = False
        st.rerun()
    
    # ========== BUSCAR RELAÇÕES ==========
    if not st.session_state.get('buscar_relacoes', False):
        st.info(f"👆 Clique no botão abaixo para buscar relações no banco **{banco}**")
        
        if st.button("🔍 Buscar Relações Neste Banco", type="primary", use_container_width=True):
            st.session_state.buscar_relacoes = True
            st.rerun()
    else:
        # ========== PROCESSAR BANCO ATUAL ==========
        with st.spinner(f"Processando banco '{banco}'..."):
            
            # Mostrar tabelas do banco primeiro
            tabelas_do_banco = listar_tabelas_fresh(banco)
            
            with st.expander("📋 Tabelas encontradas no banco"):
                st.write(f"Total: {len(tabelas_do_banco)} tabelas")
                for tabela in sorted(tabelas_do_banco):
                    st.write(f"- `{tabela}`")
            
            # 1. ESCOLHER MÉTODO DE BUSCA
            relacoes = []
            
            if usar_show_create:
                st.info("🔄 Usando método SHOW CREATE TABLE... (pode ser mais lento)")
                relacoes = buscar_relacoes_via_show_create(banco)
            else:
                st.info("⚡ Usando método INFORMATION_SCHEMA...")
                relacoes = buscar_relacoes_fresh(banco)
            
            if not relacoes:
                st.warning(f"⚠️ Nenhuma relação encontrada no banco '{banco}'")
                
                st.metric("Total de Tabelas", len(tabelas_do_banco))
                
                # Botão para tentar novamente
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Tentar com outro método", use_container_width=True):
                        st.session_state.buscar_relacoes = False
                        st.rerun()
                with col2:
                    if st.button("↩️ Voltar", use_container_width=True):
                        reset_relacoes_state()
                        st.rerun()
                return
            
            # 2. MOSTRAR RESUMO
            st.success(f"✅ {len(relacoes)} relação(ões) encontrada(s) em '{banco}'")
            
            # Verificar se há tabelas de outros bancos
            tabelas_outros_bancos = []
            for rel in relacoes:
                origem = rel['tabela_origem']
                destino = rel['tabela_destino']
                
                if origem not in tabelas_do_banco:
                    tabelas_outros_bancos.append(origem)
                if destino not in tabelas_do_banco:
                    tabelas_outros_bancos.append(destino)
            
            if tabelas_outros_bancos:
                st.error(f"❌ **ATENÇÃO:** Encontradas {len(set(tabelas_outros_bancos))} tabelas "
                        f"que NÃO pertencem ao banco '{banco}': {set(tabelas_outros_bancos)}")
                
                # Filtrar APENAS relações com tabelas do banco atual
                relacoes_filtradas = []
                for rel in relacoes:
                    if (rel['tabela_origem'] in tabelas_do_banco and 
                        rel['tabela_destino'] in tabelas_do_banco):
                        relacoes_filtradas.append(rel)
                
                st.warning(f"Filtradas {len(relacoes) - len(relacoes_filtradas)} relações inválidas")
                relacoes = relacoes_filtradas
            
            # Mostrar tabela de relações
            df_relacoes = pd.DataFrame(relacoes)
            st.dataframe(df_relacoes[['tabela_origem', 'coluna_origem', 
                                    'tabela_destino', 'coluna_destino']], 
                       use_container_width=True, hide_index=True)
            
            # 3. CRIAR E MOSTRAR GRAFO
            G, erro = criar_grafo_limpo(banco, relacoes)
            
            if erro:
                st.error(erro)
            elif G:
                st.subheader("🎯 Diagrama de Relações")
                
                # Estatísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tabelas no diagrama", len(G.nodes()))
                with col2:
                    st.metric("Relações", len(G.edges()))
                with col3:
                    try:
                        densidade = nx.density(G)
                        st.metric("Densidade", f"{densidade:.3f}")
                    except:
                        st.metric("Densidade", "N/A")
                
                # Mostrar tabelas no grafo
                with st.expander("📋 Ver tabelas incluídas no diagrama"):
                    tabelas_no_grafo = sorted(list(G.nodes()))
                    st.write(f"Tabelas no diagrama ({len(tabelas_no_grafo)}):")
                    for tabela in tabelas_no_grafo:
                        st.write(f"- `{tabela}`")
                
                # Plotar
                buf = plotar_grafo_limpo(G, banco)
                if buf:
                    st.image(buf, use_container_width=True)
                
                # Exportar
                st.subheader("📝 Exportar")
                
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    # Exportar CSV
                    csv_data = df_relacoes.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Relações (CSV)",
                        data=csv_data,
                        file_name=f"relacoes_{banco}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_exp2:
                    # Gerar SQL
                    sql_relacoes = f"-- RELAÇÕES DO BANCO: {banco}\n\n"
                    for rel in relacoes:
                        sql_relacoes += f"ALTER TABLE `{rel['tabela_origem']}` "
                        sql_relacoes += f"ADD FOREIGN KEY (`{rel['coluna_origem']}`) "
                        sql_relacoes += f"REFERENCES `{rel['tabela_destino']}`(`{rel['coluna_destino']}`);\n"
                    
                    st.download_button(
                        label="📄 Baixar SQL",
                        data=sql_relacoes,
                        file_name=f"relacoes_{banco}.sql",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            # 4. BOTÕES DE AÇÃO
            st.markdown("---")
            col_acao1, col_acao2, col_acao3 = st.columns(3)
            
            with col_acao1:
                if st.button("🔄 Buscar Outro Banco", type="secondary", use_container_width=True):
                    reset_relacoes_state()
                    st.rerun()
            
            with col_acao2:
                if st.button("🔄 Alterar Método de Busca", use_container_width=True):
                    st.session_state.buscar_relacoes = False
                    st.rerun()
            
            with col_acao3:
                if st.button("🔍 Nova Busca", use_container_width=True):
                    st.session_state.buscar_relacoes = False
                    st.rerun()
    
    # ========== BOTÕES DE NAVEGAÇÃO ==========
    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    
    with col_nav1:
        if st.button("🏠 Voltar para Página Principal", use_container_width=True):
            reset_relacoes_state()
            st.session_state.pagina = "home"
            st.rerun()
    
    with col_nav2:
        if st.button("📊 Ir para Criar Tabelas", use_container_width=True):
            reset_relacoes_state()
            st.session_state.pagina = "criar_tabelas"
            st.rerun()

# ============ INICIALIZAÇÃO ============
if __name__ == "__main__":
    st.set_page_config(
        page_title="Visualizador de Relações SQL", 
        layout="wide",
        page_icon="🔗"
    )
    
    # Inicializar estados
    if 'buscar_relacoes' not in st.session_state:
        st.session_state.buscar_relacoes = False
    
    if 'banco_anterior_relacoes' not in st.session_state:
        st.session_state.banco_anterior_relacoes = None
    
    # Verificar dependências
    try:
        import networkx
        import matplotlib
    except ImportError:
        st.error("⚠️ Instale: pip install networkx matplotlib")
        st.stop()
    
    pagina_relacoes()