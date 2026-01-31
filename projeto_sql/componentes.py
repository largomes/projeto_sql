# modules/listar_banco.py - NOVA VERSÃO
"""
Módulo para listar e gerenciar bancos de dados
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from config_global import (
    listar_bancos_disponiveis, get_banco_ativo, set_banco_ativo,
    obter_info_banco, criar_novo_banco, limpar_cache_banco
)
from componentes import componente_selecao_banco, componente_resumo_banco

def pagina_listar_bancos():
    """Página principal para listar e gerenciar bancos de dados"""
    st.title("🗄️ Gerenciador de Bancos de Dados")
    
    # Menu de opções
    st.markdown("### 📊 Menu de Operações")
    
    col_op1, col_op2, col_op3, col_op4 = st.columns(4)
    
    with col_op1:
        if st.button("🔄 Atualizar Lista", use_container_width=True, type="primary"):
            listar_bancos_disponiveis(forcar_atualizacao=True)
            st.rerun()
    
    with col_op2:
        if st.button("➕ Criar Novo", use_container_width=True):
            st.session_state.criando_novo_banco = True
            st.rerun()
    
    with col_op3:
        if st.button("🧹 Limpar Cache", use_container_width=True):
            limpar_cache_banco()
            st.success("✅ Cache limpo!")
            st.rerun()
    
    with col_op4:
        if st.button("📊 Estatísticas", use_container_width=True):
            st.session_state.mostrar_stats = True
            st.rerun()
    
    st.markdown("---")
    
    # Seção 1: Seleção rápida de banco
    st.markdown("### 🎯 Seleção Rápida")
    
    banco_ativo, acao = componente_selecao_banco(
        titulo="🏦 Banco Ativo",
        mostrar_status=True,
        permitir_criar=False,
        chave_unica="listar_bancos_seletor"
    )
    
    if banco_ativo:
        st.success(f"✅ Trabalhando com: **{banco_ativo}**")
    
    st.markdown("---")
    
    # Seção 2: Lista completa de bancos
    st.markdown("### 📋 Todos os Bancos de Dados")
    
    bancos = listar_bancos_disponiveis()
    
    if not bancos:
        st.info("📭 Nenhum banco de dados encontrado.")
        st.markdown("""
        **Dicas:**
        1. Verifique se o MySQL está rodando
        2. Clique em **➕ Criar Novo** para criar seu primeiro banco
        3. Ou use o XAMPP/Docker para gerenciar bancos existentes
        """)
        return
    
    # Opções de visualização
    view_mode = st.radio(
        "Modo de visualização:",
        ["📊 Cards", "📋 Lista", "📈 Detalhado"],
        horizontal=True,
        key="view_mode_bancos"
    )
    
    if view_mode == "📊 Cards":
        mostrar_bancos_cards(bancos)
    elif view_mode == "📋 Lista":
        mostrar_bancos_lista(bancos)
    else:
        mostrar_bancos_detalhado(bancos)
    
    # Seção 3: Criar novo banco (se ativado)
    if st.session_state.get("criando_novo_banco", False):
        st.markdown("---")
        st.markdown("### ➕ Criar Novo Banco de Dados")
        
        with st.form("form_criar_banco"):
            col_nome, col_charset = st.columns(2)
            
            with col_nome:
                novo_nome = st.text_input(
                    "Nome do Banco*",
                    placeholder="ex: projeto_final",
                    help="Use apenas letras, números e underscores"
                )
            
            with col_charset:
                charset = st.selectbox(
                    "Charset",
                    ["utf8mb4", "utf8", "latin1"],
                    index=0,
                    help="Recomendado: utf8mb4 (suporta emojis)"
                )
            
            collation = st.selectbox(
                "Collation",
                ["utf8mb4_unicode_ci", "utf8_general_ci", "latin1_swedish_ci"],
                index=0
            )
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit = st.form_submit_button(
                    "✅ Criar Banco",
                    type="primary",
                    use_container_width=True
                )
            
            with col_cancel:
                cancel = st.form_submit_button(
                    "❌ Cancelar",
                    use_container_width=True
                )
            
            if submit:
                if not novo_nome:
                    st.error("❌ Digite um nome para o banco")
                elif novo_nome in bancos:
                    st.error(f"❌ Banco '{novo_nome}' já existe")
                else:
                    if criar_novo_banco(novo_nome):
                        st.success(f"✅ Banco '{novo_nome}' criado com sucesso!")
                        st.session_state.criando_novo_banco = False
                        set_banco_ativo(novo_nome)
                        st.rerun()
            
            if cancel:
                st.session_state.criando_novo_banco = False
                st.rerun()
    
    # Seção 4: Estatísticas (se ativado)
    if st.session_state.get("mostrar_stats", False):
        st.markdown("---")
        st.markdown("### 📈 Estatísticas do Sistema")
        
        mostrar_estatisticas_sistema(bancos)

# ============ FUNÇÕES AUXILIARES ============

def mostrar_bancos_cards(bancos):
    """Mostra bancos em cards visuais"""
    # Agrupar em linhas de 3
    for i in range(0, len(bancos), 3):
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(bancos):
                banco = bancos[i + j]
                with cols[j]:
                    mostrar_card_banco(banco)

def mostrar_card_banco(banco_nome):
    """Mostra um card individual para o banco"""
    info = obter_info_banco(banco_nome)
    banco_ativo = get_banco_ativo()
    
    with st.container(border=True, height=180):
        # Cabeçalho do card
        if banco_nome == banco_ativo:
            st.markdown(f"### 🎯 {banco_nome}")
            st.success("✅ **ATIVO**")
        else:
            st.markdown(f"### 📁 {banco_nome}")
        
        # Informações
        st.write(f"**Tabelas:** {info['tabelas']}")
        st.write(f"**Tamanho:** {info['tamanho']}")
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if banco_nome != banco_ativo:
                if st.button("🎯 Usar", key=f"usar_{banco_nome}", use_container_width=True):
                    set_banco_ativo(banco_nome)
                    st.rerun()
            else:
                st.button("✅ Ativo", disabled=True, use_container_width=True)
        
        with col_btn2:
            if st.button("🔍 Ver", key=f"ver_{banco_nome}", use_container_width=True):
                st.session_state.banco_detalhe = banco_nome
                st.rerun()

def mostrar_bancos_lista(bancos):
    """Mostra bancos em lista de tabela"""
    dados = []
    
    for banco in bancos:
        info = obter_info_banco(banco)
        dados.append({
            'Nome': banco,
            'Tabelas': info['tabelas'],
            'Tamanho': info['tamanho'],
            'Status': info['status'],
            'Ativo': '✅' if banco == get_banco_ativo() else ''
        })
    
    df = pd.DataFrame(dados)
    
    # Configurar exibição
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nome": st.column_config.TextColumn("Banco", width="medium"),
            "Tabelas": st.column_config.NumberColumn("Tabelas", format="%d"),
            "Tamanho": st.column_config.TextColumn("Tamanho"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Ativo": st.column_config.TextColumn("Ativo", width="small")
        }
    )
    
    # Botões de ação abaixo da tabela
    if not df.empty:
        banco_selecionado = st.selectbox(
            "Selecione um banco para ação:",
            bancos,
            key="select_banco_acao"
        )
        
        col_acao1, col_acao2, col_acao3 = st.columns(3)
        
        with col_acao1:
            if st.button("🎯 Tornar Ativo", use_container_width=True):
                set_banco_ativo(banco_selecionado)
                st.rerun()
        
        with col_acao2:
            if st.button("🔍 Ver Detalhes", use_container_width=True):
                st.session_state.banco_detalhe = banco_selecionado
                st.rerun()
        
        with col_acao3:
            if st.button("📊 Ver Tabelas", use_container_width=True):
                st.session_state.pagina = "criar_tabelas"
                set_banco_ativo(banco_selecionado)
                st.rerun()

def mostrar_bancos_detalhado(bancos):
    """Mostra informações detalhadas de cada banco"""
    for banco in bancos:
        with st.expander(f"📁 {banco}", expanded=(banco == get_banco_ativo())):
            info = obter_info_banco(banco)
            
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.metric("Tabelas", info['tabelas'])
            
            with col_info2:
                st.metric("Tamanho", info['tamanho'])
            
            with col_info3:
                if banco == get_banco_ativo():
                    st.success("✅ ATIVO")
                else:
                    if st.button("🎯 Usar Este", key=f"usar_det_{banco}"):
                        set_banco_ativo(banco)
                        st.rerun()
            
            # Ações adicionais
            st.markdown("##### 🔧 Ações")
            
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                if st.button("📋 Ver Tabelas", key=f"tabelas_{banco}"):
                    from config_global import listar_tabelas_banco
                    tabelas = listar_tabelas_banco(banco)
                    
                    if tabelas:
                        st.write("**Tabelas encontradas:**")
                        for tabela in tabelas:
                            st.write(f"• `{tabela}`")
                    else:
                        st.info("Nenhuma tabela encontrada")
            
            with col_act2:
                if st.button("📊 Backup", key=f"backup_{banco}"):
                    st.info(f"Backup do banco '{banco}' - Use a página de Backup")
                    st.session_state.pagina = "backup"
                    st.rerun()
            
            with col_act3:
                if st.button("🧪 Testar Conexão", key=f"test_{banco}"):
                    from config_global import conectar_banco_especifico
                    conexao = conectar_banco_especifico(banco)
                    if conexao and conexao.is_connected():
                        st.success("✅ Conexão estabelecida!")
                        conexao.close()
                    else:
                        st.error("❌ Falha na conexão")

def mostrar_estatisticas_sistema(bancos):
    """Mostra estatísticas do sistema"""
    total_tabelas = 0
    total_bancos = len(bancos)
    bancos_com_tabelas = 0
    
    # Coletar dados
    for banco in bancos:
        info = obter_info_banco(banco)
        total_tabelas += info['tabelas']
        if info['tabelas'] > 0:
            bancos_com_tabelas += 1
    
    # Métricas principais
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.metric("Total de Bancos", total_bancos)
    
    with col_stat2:
        st.metric("Total de Tabelas", total_tabelas)
    
    with col_stat3:
        if total_bancos > 0:
            media = total_tabelas / total_bancos
            st.metric("Média Tabelas/Banco", f"{media:.1f}")
        else:
            st.metric("Média Tabelas/Banco", "0")
    
    # Distribuição
    st.markdown("##### 📊 Distribuição de Tabelas")
    
    dados_dist = []
    for banco in bancos[:10]:  # Limitar a 10 para o gráfico
        info = obter_info_banco(banco)
        dados_dist.append({
            'Banco': banco,
            'Tabelas': info['tabelas']
        })
    
    if dados_dist:
        df_dist = pd.DataFrame(dados_dist)
        st.bar_chart(df_dist.set_index('Banco'))
    
    # Banco ativo
    banco_ativo = get_banco_ativo()
    if banco_ativo:
        st.markdown(f"##### 🎯 Banco Ativo: **{banco_ativo}**")
        info_ativo = obter_info_banco(banco_ativo)
        
        col_ativo1, col_ativo2 = st.columns(2)
        
        with col_ativo1:
            st.write(f"**Tabelas:** {info_ativo['tabelas']}")
            st.write(f"**Tamanho:** {info_ativo['tamanho']}")
        
        with col_ativo2:
            if info_ativo['tabelas'] > 0:
                st.success("✅ Pronto para uso")
            else:
                st.warning("⚠️ Banco vazio - crie tabelas")

# ============ PÁGINA DE DETALHES DO BANCO ============
def pagina_detalhes_banco():
    """Página de detalhes de um banco específico"""
    banco_nome = st.session_state.get("banco_detalhe")
    
    if not banco_nome:
        st.error("❌ Nenhum banco selecionado para detalhes")
        if st.button("← Voltar para Lista"):
            st.session_state.pagina = "listar_bancos"
            st.rerun()
        return
    
    st.title(f"📊 Detalhes do Banco: **{banco_nome}**")
    
    # Botão voltar
    if st.button("← Voltar para Lista"):
        st.session_state.pagina = "listar_bancos"
        st.rerun()
    
    st.markdown("---")
    
    # Resumo completo
    componente_resumo_banco(banco_nome)
    
    # Informações detalhadas
    st.markdown("### 🔍 Informações Técnicas")
    
    try:
        import mysql.connector
        
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=banco_nome,
            port=3306
        )
        
        cursor = conexao.cursor()
        
        # Informações do banco
        cursor.execute("SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s", (banco_nome,))
        charset_info = cursor.fetchone()
        
        # Tabelas com detalhes
        cursor.execute("""
            SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH, 
                   CREATE_TIME, UPDATE_TIME, TABLE_COLLATION
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
        """, (banco_nome,))
        
        tabelas_detalhes = cursor.fetchall()
        
        cursor.close()
        conexao.close()
        
        # Mostrar informações
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            if charset_info:
                st.write(f"**Charset padrão:** {charset_info[0]}")
                st.write(f"**Collation padrão:** {charset_info[1]}")
        
        with col_info2:
            st.write(f"**Total de tabelas:** {len(tabelas_detalhes)}")
            if tabelas_detalhes:
                total_rows = sum(t[1] or 0 for t in tabelas_detalhes)
                st.write(f"**Total de registros:** {total_rows:,}")
        
        # Tabela detalhada
        if tabelas_detalhes:
            st.markdown("### 📋 Tabelas (Detalhado)")
            
            dados_tabelas = []
            for tabela in tabelas_detalhes:
                tamanho_mb = ((tabela[2] or 0) + (tabela[3] or 0)) / (1024*1024)
                dados_tabelas.append({
                    'Tabela': tabela[0],
                    'Registros': tabela[1] or 0,
                    'Tamanho (MB)': f"{tamanho_mb:.2f}" if tamanho_mb > 0 else "0",
                    'Collation': tabela[6],
                    'Criada em': tabela[4].strftime('%Y-%m-%d') if tabela[4] else '-'
                })
            
            df_tabelas = pd.DataFrame(dados_tabelas)
            st.dataframe(df_tabelas, use_container_width=True)
        
        # Ações específicas
        st.markdown("### ⚡ Ações Rápidas")
        
        col_act1, col_act2, col_act3 = st.columns(3)
        
        with col_act1:
            if st.button("🎯 Tornar Banco Ativo", use_container_width=True):
                set_banco_ativo(banco_nome)
                st.success(f"✅ Banco '{banco_nome}' agora é o ativo!")
                st.rerun()
        
        with col_act2:
            if st.button("📝 Abrir no Editor SQL", use_container_width=True):
                st.session_state.pagina = "query_editor"
                set_banco_ativo(banco_nome)
                st.rerun()
        
        with col_act3:
            if st.button("🏗️ Gerenciar Tabelas", use_container_width=True):
                st.session_state.pagina = "criar_tabelas"
                set_banco_ativo(banco_nome)
                st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro ao obter detalhes: {e}")

# ============ PONTO DE ENTRADA ============
def main():
    """Função principal do módulo"""
    if st.session_state.get("banco_detalhe"):
        pagina_detalhes_banco()
    else:
        pagina_listar_bancos()