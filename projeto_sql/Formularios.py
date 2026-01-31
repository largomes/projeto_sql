# Formularios.py - VERSÃO COMPLETA CORRIGIDA
import streamlit as st
import pandas as pd
from datetime import datetime
import mysql.connector
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# ============ FUNÇÕES DE CONEXÃO E AUXILIARES ============
def conectar_banco(banco=None):
    """Conecta ao banco de dados MariaDB/MySQL"""
    try:
        config = {
            "host": "localhost",
            "user": "root",
            "password": ""
        }
        
        if banco:
            config["database"] = banco
            
        conexao = mysql.connector.connect(**config)
        return conexao
    except mysql.connector.Error as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None

def listar_bancos_simples():
    """Função local para listar bancos"""
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexao.cursor()
        cursor.execute("SHOW DATABASES")
        bancos = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conexao.close()
        
        # Filtrar bancos do sistema
        return [b for b in bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
    except:
        return []

def listar_tabelas(conexao):
    """Lista todas as tabelas do banco"""
    try:
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")
        tabelas = [tabela[0] for tabela in cursor.fetchall()]
        cursor.close()
        return tabelas
    except Exception as e:
        st.error(f"Erro ao listar tabelas: {e}")
        return []

def obter_estrutura_tabela(conexao, tabela):
    """Obtém estrutura completa da tabela"""
    try:
        cursor = conexao.cursor()
        cursor.execute(f"DESCRIBE `{tabela}`")
        estrutura = cursor.fetchall()
        cursor.close()
        
        # Converter para DataFrame
        colunas = ['Campo', 'Tipo', 'Nulo', 'Chave', 'Default', 'Extra']
        df = pd.DataFrame(estrutura, columns=colunas)
        return df
    except Exception as e:
        st.error(f"Erro ao obter estrutura: {e}")
        return None

def encontrar_coluna_ordenacao(conexao, tabela):
    """Encontra a melhor coluna para ordenação (PK, chave única, ou primeira coluna)"""
    try:
        # Obter estrutura da tabela
        estrutura = obter_estrutura_tabela(conexao, tabela)
        
        if estrutura is not None:
            # 1. Primeiro tentar encontrar PRIMARY KEY
            pk_cols = estrutura[estrutura['Chave'] == 'PRI']
            if not pk_cols.empty:
                return pk_cols.iloc[0]['Campo']
            
            # 2. Tentar encontrar UNIQUE KEY
            uni_cols = estrutura[estrutura['Chave'] == 'UNI']
            if not uni_cols.empty:
                return uni_cols.iloc[0]['Campo']
            
            # 3. Tentar encontrar coluna com 'id' no nome
            colunas_id = [col for col in estrutura['Campo'].tolist() 
                         if 'id' in col.lower() or 'cod' in col.lower()]
            if colunas_id:
                return colunas_id[0]
            
            # 4. Tentar coluna de data/criação
            colunas_data = [col for col in estrutura['Campo'].tolist() 
                           if 'data' in col.lower() or 'created' in col.lower() 
                           or 'timestamp' in col.lower()]
            if colunas_data:
                return colunas_data[0]
            
            # 5. Usar a primeira coluna
            return estrutura.iloc[0]['Campo']
        
        return "id"  # Fallback
        
    except Exception as e:
        return "id"  # Fallback

def mostrar_resumo_tabela(conexao, tabela):
    """Versão corrigida"""
    try:
        cursor = conexao.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{tabela}`")
        total = cursor.fetchone()[0]
        
        cursor.execute(f"DESCRIBE `{tabela}`")
        colunas_info = cursor.fetchall()
        
        cursor.close()
        
        # Criar DataFrame corrigido
        colunas = ['Campo', 'Tipo', 'Nulo', 'Chave', 'Default', 'Extra']
        df_estrutura = pd.DataFrame(colunas_info, columns=colunas)
        df_estrutura_corrigido = corrigir_tipos_dataframe(df_estrutura)
        
        st.markdown(f"""
        <div class='status-card'>
            <strong>📊 Resumo da Tabela <code>{tabela}</code></strong><br>
            • <strong>{total}</strong> registros totais<br>
            • <strong>{len(colunas_info)}</strong> colunas<br>
            • Última atualização: {datetime.now().strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar estrutura se clicar
        if st.checkbox("👁️ Mostrar estrutura da tabela"):
            st.dataframe(df_estrutura_corrigido, use_container_width=True)
        
    except Exception as e:
        st.warning(f"Não foi possível carregar resumo: {e}")

def corrigir_tipos_dataframe(df):
    """Corrige tipos misturados no DataFrame para evitar erros do PyArrow"""
    try:
        df_corrigido = df.copy()
        
        # Para cada coluna, verificar se há tipos misturados
        for coluna in df_corrigido.columns:
            # Verificar se a coluna tem tipos misturados
            tipos = set(type(x).__name__ for x in df_corrigido[coluna].dropna() if x is not None)
            
            if len(tipos) > 1:
                # Converter tudo para string para evitar erros
                df_corrigido[coluna] = df_corrigido[coluna].astype(str)
            elif df_corrigido[coluna].dtype == 'object':
                # Se é objeto, tentar converter para tipos apropriados
                try:
                    # Tentar converter para numérico
                    df_corrigido[coluna] = pd.to_numeric(df_corrigido[coluna])
                except (ValueError, TypeError):
                    # Se falhar, manter como string
                    df_corrigido[coluna] = df_corrigido[coluna].astype(str)
        
        return df_corrigido
    except Exception as e:
        # Se der erro, retornar o DataFrame original convertido para string
        try:
            return df.astype(str)
        except:
            return df

def paginacao_simples(df, chave_unica):
    """Páginação simples com setinhas"""
    items_per_page = st.selectbox("Registros por página:", [5, 10, 20, 50], key=f"items_{chave_unica}")
    
    if f'pagina_{chave_unica}' not in st.session_state:
        st.session_state[f'pagina_{chave_unica}'] = 1
    
    total_items = len(df)
    total_pages = max(1, (total_items - 1) // items_per_page + 1)
    current_page = st.session_state[f'pagina_{chave_unica}']
    
    # Navegação
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️", key=f"first_{chave_unica}", disabled=current_page == 1):
            st.session_state[f'pagina_{chave_unica}'] = 1
            st.rerun()
    
    with col2:
        if st.button("◀️", key=f"prev_{chave_unica}", disabled=current_page == 1):
            st.session_state[f'pagina_{chave_unica}'] -= 1
            st.rerun()
    
    with col3:
        st.write(f"**{current_page}/{total_pages}**")
    
    with col4:
        if st.button("▶️", key=f"next_{chave_unica}", disabled=current_page >= total_pages):
            st.session_state[f'pagina_{chave_unica}'] += 1
            st.rerun()
    
    with col5:
        if st.button("⏭️", key=f"last_{chave_unica}", disabled=current_page >= total_pages):
            st.session_state[f'pagina_{chave_unica}'] = total_pages
            st.rerun()
    
    # Mostrar dados da página atual
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    return df.iloc[start_idx:end_idx], current_page, total_pages

# ==================== 1. FUNÇÃO LISTAR (COMPLETA) ====================
def listar_registros(conexao, tabela):
    """Lista todos os registros da tabela - VERSÃO COM CORREÇÃO DE TIPOS"""
    st.subheader(f"📋 Listando Registros de '{tabela}'")
    
    try:
        # Obter estrutura da tabela
        estrutura = obter_estrutura_tabela(conexao, tabela)
        
        if estrutura is not None:
            # Opções de filtro
            with st.expander("🔍 Filtros Avançados"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Filtro por coluna
                    colunas_filtro = ['Todas'] + estrutura['Campo'].tolist()
                    coluna_filtro = st.selectbox("Filtrar por coluna:", colunas_filtro)
                
                with col2:
                    # Ordenação
                    colunas_ordenacao = estrutura['Campo'].tolist()
                    ordenar_por = st.selectbox("Ordenar por:", colunas_ordenacao)
                    ordem = st.radio("Ordem:", ["Ascendente", "Descendente"], horizontal=True)
            
            # Construir query
            query = f"SELECT * FROM `{tabela}`"
            
            # Adicionar ORDER BY se selecionado
            if ordenar_por != colunas_ordenacao[0]:
                ordem_sql = "ASC" if ordem == "Ascendente" else "DESC"
                query += f" ORDER BY `{ordenar_por}` {ordem_sql}"
            
            # Executar query
            cursor = conexao.cursor()
            cursor.execute(query)
            registros = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            cursor.close()
            
            if registros:
                st.success(f"✅ Encontrados {len(registros)} registros")
                
                # Converter para DataFrame
                df = pd.DataFrame(registros, columns=colunas)
                
                # CORREÇÃO: Garantir que não há valores None problemáticos
                df = df.fillna('NULL')  # Preencher None com string
                
                # Aplicar filtro se selecionado
                if coluna_filtro != 'Todas' and coluna_filtro in df.columns:
                    valor_filtro = st.text_input(f"Valor para filtrar na coluna '{coluna_filtro}':")
                    if valor_filtro:
                        df = df[df[coluna_filtro].astype(str).str.contains(valor_filtro, case=False, na=False)]
                        st.info(f"Filtrado: {len(df)} registros contendo '{valor_filtro}'")
                
                # ========== PAGINAÇÃO ==========
                st.write("---")
                st.write("### 📄 Navegação entre Registros")
                
                # Usar paginação
                df_paginado, pagina_atual, total_paginas = paginacao_simples(df, tabela)
                
                # CORREÇÃO: Aplicar correção de tipos antes de mostrar
                df_paginado_corrigido = corrigir_tipos_dataframe(df_paginado)
                
                # Mostrar estatísticas de navegação
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    inicio = (pagina_atual - 1) * st.session_state.get(f'items_{tabela}', 10) + 1
                    fim = min(inicio + st.session_state.get(f'items_{tabela}', 10) - 1, len(df))
                    st.info(f"**Mostrando:** {inicio} a {fim} de {len(df)}")
                
                with col_info2:
                    st.info(f"**Página:** {pagina_atual} de {total_paginas}")
                
                # Mostrar dados COM CORREÇÃO
                st.dataframe(df_paginado_corrigido, use_container_width=True)
                
                # ========== BOTÕES DE AÇÃO ==========
                st.write("---")
                col_export, col_stats, col_refresh = st.columns(3)
                
                with col_export:
                    if st.button("📥 Exportar para CSV", use_container_width=True):
                        # Para exportar, usar DataFrame original
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Baixar CSV",
                            data=csv,
                            file_name=f"{tabela}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col_stats:
                    if st.button("📊 Estatísticas", use_container_width=True):
                        with st.expander("📈 Estatísticas Detalhadas"):
                            st.write("**Tipos de dados:**")
                            st.write(df.dtypes)
                            
                            st.write("**Resumo estatístico:**")
                            # Tentar converter colunas numéricas
                            df_numerico = df.copy()
                            for col in df_numerico.columns:
                                try:
                                    df_numerico[col] = pd.to_numeric(df_numerico[col])
                                except (ValueError, TypeError):
                                    # Manter como está se não for numérico
                                    continue
                            
                            # Mostrar describe apenas para colunas numéricas
                            colunas_numericas = df_numerico.select_dtypes(include=['number']).columns
                            if len(colunas_numericas) > 0:
                                st.write(df_numerico[colunas_numericas].describe())
                            else:
                                st.info("Nenhuma coluna numérica para análise estatística.")
                
                with col_refresh:
                    if st.button("🔄 Atualizar Dados", use_container_width=True):
                        st.rerun()
                
            else:
                st.info(f"ℹ️ A tabela '{tabela}' está vazia.")
        else:
            st.error("Não foi possível obter a estrutura da tabela.")
            
    except Exception as e:
        st.error(f"❌ Erro ao listar registros: {e}")

# ==================== 2. FUNÇÃO CRIAR (COMPLETA) ====================
def operacao_create_ui(conexao, tabela):
    """Interface para criar novo registro"""
    st.subheader(f"➕ Criar Registros em '{tabela}'")
    
    # Session state para controle
    if f'form_cleared_{tabela}' not in st.session_state:
        st.session_state[f'form_cleared_{tabela}'] = False
    if f'last_success_{tabela}' not in st.session_state:
        st.session_state[f'last_success_{tabela}'] = None
    
    # Botão para limpar TUDO
    col_clear_all, col_new_mode = st.columns(2)
    with col_clear_all:
        if st.button("🧹 Novo Registo ", use_container_width=True, key=f"clear_all_{tabela}"):
            # Limpar TODOS os estados relacionados a esta tabela
            keys_to_remove = [k for k in st.session_state.keys() 
                            if tabela in k or 'form_data' in k]
            for key in keys_to_remove:
                try:
                    del st.session_state[key]
                except:
                    pass
            st.session_state[f'form_cleared_{tabela}'] = True
            st.rerun()
    
    with col_new_mode:
        modo = st.radio(
            "Modo:",
            ["➕ Único", "📚 Em Lote"],
            horizontal=True,
            key=f"modo_{tabela}"
        )
    
    # Se o formulário foi limpo, mostrar mensagem
    if st.session_state[f'form_cleared_{tabela}']:
        st.success("✅ Formulário limpo! Pode inserir novo registro.")
        st.session_state[f'form_cleared_{tabela}'] = False
    
    # Mostrar último sucesso
    if st.session_state[f'last_success_{tabela}']:
        st.info(f"✅ Último registro criado: {st.session_state[f'last_success_{tabela}']}")
    
    try:
        # Obter estrutura da tabela
        estrutura = obter_estrutura_tabela(conexao, tabela)
        
        if estrutura is not None:
            if modo == "➕ Único":
                # ========== FORMULÁRIO ÚNICO ==========
                st.write("### 📝 Preencha os dados:")
                
                # Criar um container para o formulário
                form_container = st.container()
                
                with form_container:
                    dados_form = {}
                    
                    for _, row in estrutura.iterrows():
                        campo = row['Campo']
                        tipo = row['Tipo']
                        nulo = row['Nulo']
                        default = row['Default']
                        extra = row['Extra']
                        
                        # Pular auto_increment
                        if 'auto_increment' in extra.lower():
                            continue
                        
                        # Criar chave única para cada campo
                        field_key = f"{tabela}_{campo}_create"
                        
                        # Se o formulário foi limpo, usar valor vazio
                        if st.session_state.get(f'form_cleared_{tabela}', False):
                            current_value = ""
                        else:
                            # Tentar obter valor salvo ou usar default
                            current_value = st.session_state.get(field_key, 
                                                               default if default and default != 'NULL' else "")
                        
                        col_label, col_input = st.columns([1, 3])
                        
                        with col_label:
                            obrigatorio = "🔴" if nulo == 'NO' and default is None else "🔵"
                            st.write(f"{obrigatorio} **{campo}**")
                            st.caption(tipo)
                        
                        with col_input:
                            tipo_lower = tipo.lower()
                            
                            if 'int' in tipo_lower:
                                try:
                                    val = int(current_value) if current_value and current_value != "" else 0
                                    valor = st.number_input(
                                        "",
                                        value=val,
                                        step=1,
                                        format="%d",
                                        key=field_key,
                                        label_visibility="collapsed"
                                    )
                                except:
                                    valor = st.number_input(
                                        "",
                                        value=0,
                                        step=1,
                                        key=field_key,
                                        label_visibility="collapsed"
                                    )
                            
                            elif 'decimal' in tipo_lower or 'float' in tipo_lower:
                                try:
                                    val = float(current_value) if current_value and current_value != "" else 0.0
                                    valor = st.number_input(
                                        "",
                                        value=val,
                                        step=0.01,
                                        format="%.2f",
                                        key=field_key,
                                        label_visibility="collapsed"
                                    )
                                except:
                                    valor = st.number_input(
                                        "",
                                        value=0.0,
                                        step=0.01,
                                        key=field_key,
                                        label_visibility="collapsed"
                                    )
                            
                            elif 'date' in tipo_lower:
                                try:
                                    if current_value and current_value != "":
                                        val = datetime.strptime(str(current_value), '%Y-%m-%d').date()
                                    else:
                                        val = datetime.now().date()
                                except:
                                    val = datetime.now().date()
                                
                                valor = st.date_input(
                                    "",
                                    value=val,
                                    key=field_key,
                                    label_visibility="collapsed"
                                )
                            
                            elif 'datetime' in tipo_lower or 'timestamp' in tipo_lower:
                                if default == 'CURRENT_TIMESTAMP':
                                    st.info("⏰ Auto")
                                    valor = None
                                else:
                                    valor = st.text_input(
                                        "",
                                        value=current_value,
                                        key=field_key,
                                        label_visibility="collapsed",
                                        placeholder="YYYY-MM-DD HH:MM:SS"
                                    )
                            
                            elif 'text' in tipo_lower or 'blob' in tipo_lower:
                                valor = st.text_area(
                                    "",
                                    value=current_value,
                                    height=80,
                                    key=field_key,
                                    label_visibility="collapsed",
                                    placeholder=f"Digite texto para {campo}..."
                                )
                            
                            else:  # varchar, char, etc.
                                valor = st.text_input(
                                    "",
                                    value=current_value,
                                    key=field_key,
                                    label_visibility="collapsed",
                                    placeholder=f"Digite valor para {campo}..."
                                )
                        
                        # Armazenar valor
                        if valor is not None and str(valor).strip() != "":
                            dados_form[campo] = valor
                
                # ========== BOTÕES DE AÇÃO ==========
                st.write("---")
                col_save, col_clear, col_view = st.columns(3)
                
                with col_save:
                    save_pressed = st.button("💾 Salvar Registro", 
                                           type="primary", 
                                           use_container_width=True,
                                           key=f"save_{tabela}")
                
                with col_clear:
                    clear_pressed = st.button("🧹 Limpar Campos", 
                                            use_container_width=True,
                                            key=f"clear_{tabela}")
                
                with col_view:
                    view_pressed = st.button("👁️ Ver Últimos", 
                                           use_container_width=True,
                                           key=f"view_{tabela}")
                
                # ========== PROCESSAR AÇÕES ==========
                # 1. Se clicar em SALVAR
                if save_pressed:
                    if dados_form:
                        try:
                            cursor = conexao.cursor()
                            
                            # Construir query
                            campos = [f"`{campo}`" for campo in dados_form.keys()]
                            valores = list(dados_form.values())
                            placeholders = ["%s"] * len(valores)
                            
                            query = f"INSERT INTO `{tabela}` ({', '.join(campos)}) VALUES ({', '.join(placeholders)})"
                            
                            cursor.execute(query, valores)
                            conexao.commit()
                            
                            id_inserido = cursor.lastrowid
                            cursor.close()
                            
                            # Salvar informação do sucesso
                            st.session_state[f'last_success_{tabela}'] = f"ID: {id_inserido}"
                            
                            st.success(f"✅ Registro criado com sucesso! **ID: {id_inserido}**")
                            st.balloons()
                            
                            # Opção para limpar após salvar
                            if st.button("➕ Inserir Outro (Limpar)", 
                                       use_container_width=True,
                                       key=f"another_{tabela}"):
                                # Limpar os campos desta tabela
                                for _, row in estrutura.iterrows():
                                    campo = row['Campo']
                                    field_key = f"{tabela}_{campo}_create"
                                    if field_key in st.session_state:
                                        del st.session_state[field_key]
                                st.session_state[f'form_cleared_{tabela}'] = True
                                st.rerun()
                            
                        except Exception as e:
                            conexao.rollback()
                            st.error(f"❌ Erro ao criar registro: {e}")
                    else:
                        st.warning("⚠️ Preencha pelo menos um campo!")
                
                # 2. Se clicar em LIMPAR
                if clear_pressed:
                    # Limpar apenas os campos desta tabela
                    for _, row in estrutura.iterrows():
                        campo = row['Campo']
                        field_key = f"{tabela}_{campo}_create"
                        if field_key in st.session_state:
                            del st.session_state[field_key]
                    st.session_state[f'form_cleared_{tabela}'] = True
                    st.rerun()
                
                # 3. Se clicar em VER ÚLTIMOS
                if view_pressed:
                    mostrar_ultimos_registros(conexao, tabela, limite=5)
            
            else:
                # ========== MODO EM LOTE ==========
                st.info("📚 **Modo em Lote:** Insira vários registros (um por linha)")
                
                # Usar text_area para múltiplos registros
                dados_lote = st.text_area(
                    "Dados (um registro por linha, campos separados por vírgula):",
                    height=200,
                    placeholder=f"Exemplo:\nnome,email,idade\nJoão,joao@email.com,30\nMaria,maria@email.com,25",
                    key=f"lote_{tabela}"
                )
                
                if st.button("💾 Inserir Todos", type="primary", key=f"lote_save_{tabela}"):
                    if dados_lote:
                        processar_lote(conexao, tabela, dados_lote, estrutura)
                    else:
                        st.warning("Digite dados para inserir.")
        
        else:
            st.error("Não foi possível obter a estrutura da tabela.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar formulário: {e}")

def processar_lote(conexao, tabela, dados_lote, estrutura):
    """Processa e insere múltiplos registros de uma vez"""
    try:
        # Extrair campos (ignorar auto_increment)
        campos = []
        for _, row in estrutura.iterrows():
            campo = row['Campo']
            if 'auto_increment' not in row['Extra'].lower():
                campos.append(campo)
        
        linhas = [linha.strip() for linha in dados_lote.split('\n') if linha.strip()]
        inseridos = 0
        erros = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, linha in enumerate(linhas):
            status_text.text(f"Processando linha {i+1}/{len(linhas)}")
            
            try:
                valores = [v.strip() for v in linha.split(',')]
                if len(valores) == len(campos):
                    cursor = conexao.cursor()
                    placeholders = ', '.join(['%s'] * len(campos))
                    query = f"INSERT INTO `{tabela}` ({', '.join([f'`{c}`' for c in campos])}) VALUES ({placeholders})"
                    cursor.execute(query, valores)
                    inseridos += 1
                else:
                    erros.append(f"Linha {i+1}: Esperados {len(campos)} campos, recebidos {len(valores)}")
            except Exception as e:
                erros.append(f"Linha {i+1}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(linhas))
        
        conexao.commit()
        status_text.empty()
        
        if inseridos > 0:
            st.success(f"✅ {inseridos} registro(s) inserido(s) com sucesso!")
            # Limpar o text_area após sucesso
            st.session_state[f'lote_{tabela}'] = ""
            st.rerun()
        
        if erros:
            st.warning(f"⚠️ {len(erros)} erro(s):")
            for erro in erros[:5]:
                st.write(f"- {erro}")
        
    except Exception as e:
        st.error(f"❌ Erro ao processar lote: {e}")

def mostrar_ultimos_registros(conexao, tabela, limite=5):
    """Mostra os últimos registros da tabela"""
    try:
        cursor = conexao.cursor()
        
        # Tentar encontrar coluna para ordenação
        estrutura = obter_estrutura_tabela(conexao, tabela)
        coluna_ordenacao = "1"  # Default
        
        if estrutura is not None:
            # Procurar coluna com ID ou usar primeira
            colunas_id = [c for c in estrutura['Campo'].tolist() 
                         if 'id' in c.lower() or 'cod' in c.lower()]
            if colunas_id:
                coluna_ordenacao = colunas_id[0]
            else:
                coluna_ordenacao = estrutura.iloc[0]['Campo']
        
        # Buscar registros
        try:
            cursor.execute(f"SELECT * FROM `{tabela}` ORDER BY `{coluna_ordenacao}` DESC LIMIT {limite}")
        except:
            cursor.execute(f"SELECT * FROM `{tabela}` LIMIT {limite}")
        
        registros = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        
        if registros:
            st.write(f"**Últimos {limite} registros:**")
            
            # Converter para string para evitar erros
            dados = []
            for reg in registros:
                linha = []
                for val in reg:
                    if val is None:
                        linha.append("NULL")
                    elif isinstance(val, (bytes, bytearray)):
                        linha.append(f"[BLOB {len(val)} bytes]")
                    else:
                        linha.append(str(val))
                dados.append(linha)
            
            df = pd.DataFrame(dados, columns=colunas)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("📭 Nenhum registro na tabela.")
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar registros: {e}")

# ==================== 3. FUNÇÃO BUSCAR (COMPLETA) ====================
def operacao_read_ui(conexao, tabela):
    """Interface para buscar registros"""
    st.subheader(f"🔍 Buscar Registros em '{tabela}'")
    
    try:
        # Obter estrutura da tabela
        estrutura = obter_estrutura_tabela(conexao, tabela)
        
        if estrutura is not None:
            # Interface de busca
            st.write("**Opções de busca:**")
            
            tab1, tab2, tab3 = st.tabs(["🔎 Busca Simples", "🎯 Busca Avançada", "📊 Busca com Filtros"])
            
            with tab1:
                # Busca simples
                coluna_busca = st.selectbox(
                    "Buscar na coluna:",
                    estrutura['Campo'].tolist(),
                    key="busca_simples_col"
                )
                
                termo_busca = st.text_input("Termo para buscar:", key="busca_simples_termo")
                
                if st.button("🔍 Buscar", key="btn_busca_simples"):
                    if termo_busca:
                        try:
                            cursor = conexao.cursor()
                            query = f"SELECT * FROM `{tabela}` WHERE `{coluna_busca}` LIKE %s LIMIT 100"
                            cursor.execute(query, (f"%{termo_busca}%",))
                            resultados = cursor.fetchall()
                            colunas = [desc[0] for desc in cursor.description]
                            cursor.close()
                            
                            if resultados:
                                st.success(f"✅ Encontrados {len(resultados)} registros")
                                df = pd.DataFrame(resultados, columns=colunas)
                                st.dataframe(df, use_container_width=True)
                                
                                # Exportar resultados
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Exportar Resultados",
                                    data=csv,
                                    file_name=f"{tabela}_busca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.info("Nenhum registro encontrado.")
                                
                        except Exception as e:
                            st.error(f"Erro na busca: {e}")
                    else:
                        st.warning("Digite um termo para buscar.")
            
            with tab2:
                # Busca avançada
                st.write("**Criar condição personalizada:**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    campo = st.selectbox("Campo:", estrutura['Campo'].tolist(), key="avancado_campo")
                
                with col2:
                    operador = st.selectbox("Operador:", 
                                          ["=", "!=", ">", "<", ">=", "<=", "LIKE", "NOT LIKE", "IS NULL", "IS NOT NULL"])
                
                with col3:
                    if operador not in ["IS NULL", "IS NOT NULL"]:
                        valor = st.text_input("Valor:", key="avancado_valor")
                    else:
                        valor = ""
                
                # Adicionar múltiplas condições
                st.write("---")
                st.write("**Adicionar mais condições:**")
                
                condicoes_extra = st.number_input("Número de condições adicionais:", 0, 5, 0)
                
                condicoes = [{"campo": campo, "operador": operador, "valor": valor}]
                
                for i in range(condicoes_extra):
                    col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                    
                    with col1:
                        conector = st.selectbox(f"Conector {i+1}:", ["AND", "OR"], key=f"conector_{i}")
                    
                    with col2:
                        campo_extra = st.selectbox(f"Campo {i+1}:", 
                                                 estrutura['Campo'].tolist(), 
                                                 key=f"campo_extra_{i}")
                    
                    with col3:
                        operador_extra = st.selectbox(f"Operador {i+1}:", 
                                                    ["=", "!=", ">", "<", ">=", "<=", "LIKE", "NOT LIKE"],
                                                    key=f"operador_extra_{i}")
                        
                        if operador_extra not in ["IS NULL", "IS NOT NULL"]:
                            valor_extra = st.text_input(f"Valor {i+1}:", key=f"valor_extra_{i}")
                        else:
                            valor_extra = ""
                    
                    condicoes.append({
                        "conector": conector,
                        "campo": campo_extra,
                        "operador": operador_extra,
                        "valor": valor_extra
                    })
                
                if st.button("🔍 Executar Busca Avançada", key="btn_busca_avancada"):
                    try:
                        # Construir query
                        where_clauses = []
                        valores = []
                        
                        for cond in condicoes:
                            if 'conector' in cond:
                                where_clauses.append(f" {cond['conector']} ")
                            
                            campo = cond['campo']
                            operador = cond['operador']
                            valor = cond['valor']
                            
                            if operador in ["LIKE", "NOT LIKE"] and valor:
                                where_clauses.append(f"`{campo}` {operador} %s")
                                valores.append(f"%{valor}%")
                            elif operador in ["IS NULL", "IS NOT NULL"]:
                                where_clauses.append(f"`{campo}` {operador}")
                            elif valor:
                                where_clauses.append(f"`{campo}` {operador} %s")
                                valores.append(valor)
                        
                        query = f"SELECT * FROM `{tabela}`"
                        if where_clauses:
                            query += " WHERE " + "".join(where_clauses)
                        
                        query += " LIMIT 100"
                        
                        cursor = conexao.cursor()
                        cursor.execute(query, valores)
                        resultados = cursor.fetchall()
                        colunas = [desc[0] for desc in cursor.description]
                        cursor.close()
                        
                        if resultados:
                            st.success(f"✅ Encontrados {len(resultados)} registros")
                            df = pd.DataFrame(resultados, columns=colunas)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("Nenhum registro encontrado.")
                            
                    except Exception as e:
                        st.error(f"Erro na busca avançada: {e}")
            
            with tab3:
                # Busca com filtros múltiplos
                st.write("**Filtrar por múltiplos campos:**")
                
                campos_filtro = st.multiselect(
                    "Selecione os campos para filtrar:",
                    estrutura['Campo'].tolist(),
                    default=estrutura['Campo'].tolist()[:3]
                )
                
                filtros = {}
                for campo in campos_filtro:
                    valor_filtro = st.text_input(f"Valor para '{campo}' (deixe vazio para ignorar):", key=f"filtro_{campo}")
                    if valor_filtro:
                        filtros[campo] = valor_filtro
                
                if st.button("🔍 Aplicar Filtros", key="btn_filtros"):
                    if filtros:
                        try:
                            where_clauses = []
                            valores = []
                            
                            for campo, valor in filtros.items():
                                where_clauses.append(f"`{campo}` LIKE %s")
                                valores.append(f"%{valor}%")
                            
                            query = f"SELECT * FROM `{tabela}` WHERE " + " AND ".join(where_clauses) + " LIMIT 100"
                            
                            cursor = conexao.cursor()
                            cursor.execute(query, valores)
                            resultados = cursor.fetchall()
                            colunas = [desc[0] for desc in cursor.description]
                            cursor.close()
                            
                            if resultados:
                                st.success(f"✅ Encontrados {len(resultados)} registros")
                                df = pd.DataFrame(resultados, columns=colunas)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("Nenhum registro encontrado com os filtros aplicados.")
                        except Exception as e:
                            st.error(f"Erro ao aplicar filtros: {e}")
                    else:
                        st.warning("Selecione pelo menos um campo para filtrar.")
        
        else:
            st.error("Não foi possível obter a estrutura da tabela.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar busca: {e}")

# ==================== 4. FUNÇÃO ATUALIZAR (COMPLETA) ====================
def operacao_update_ui(conexao, tabela):
    """Interface para atualizar registros"""
    st.subheader(f"🔄 Atualizar Registro em '{tabela}'")
    
    try:
        # Primeiro, listar alguns registros
        cursor = conexao.cursor()
        cursor.execute(f"SELECT * FROM `{tabela}` LIMIT 20")
        registros = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        
        if registros:
            st.write(f"**Últimos 20 registros de '{tabela}':**")
            df = pd.DataFrame(registros, columns=colunas)
            st.dataframe(df, use_container_width=True)
            
            st.write("---")
            st.write("**Selecionar registro para atualizar:**")
            
            # Encontrar coluna chave primária
            estrutura = obter_estrutura_tabela(conexao, tabela)
            coluna_id = None
            
            if estrutura is not None:
                # Procurar por PRIMARY KEY ou UNIQUE
                pk_cols = estrutura[estrutura['Chave'].str.contains('PRI|UNI', na=False)]
                if not pk_cols.empty:
                    coluna_id = pk_cols.iloc[0]['Campo']
                else:
                    coluna_id = colunas[0]  # Primeira coluna como fallback
            
            if coluna_id:
                # Selecionar ID específico
                valores_disponiveis = df[coluna_id].astype(str).tolist()
                id_selecionado = st.selectbox(
                    f"Selecione o valor de '{coluna_id}' para editar:",
                    valores_disponiveis
                )
                
                if id_selecionado:
                    # Buscar registro completo
                    cursor = conexao.cursor()
                    query = f"SELECT * FROM `{tabela}` WHERE `{coluna_id}` = %s"
                    cursor.execute(query, (id_selecionado,))
                    registro = cursor.fetchone()
                    cursor.close()
                    
                    if registro:
                        st.success(f"✅ Registro encontrado!")
                        
                        # Mostrar valores atuais
                        st.write("**Valores atuais:**")
                        valores_atuais = {}
                        for i, (col, val) in enumerate(zip(colunas, registro)):
                            valores_atuais[col] = val
                            st.write(f"- **{col}**: `{val}`")
                        
                        st.write("---")
                        st.write("**Editar valores:**")
                        
                        # Formulário de edição
                        novos_valores = {}
                        
                        for col in colunas:
                            if col != coluna_id:  # Não editar a chave primária
                                valor_atual = valores_atuais[col]
                                
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    st.write(f"**{col}**")
                                with col2:
                                    # Determinar tipo de input
                                    if valor_atual is None:
                                        novo_valor = st.text_input(f"Novo valor:", key=f"update_{col}")
                                    elif isinstance(valor_atual, (int, float)):
                                        novo_valor = st.number_input(f"Novo valor:", 
                                                                   value=float(valor_atual), 
                                                                   key=f"update_{col}")
                                    else:
                                        novo_valor = st.text_input(f"Novo valor:", 
                                                                 value=str(valor_atual), 
                                                                 key=f"update_{col}")
                                    
                                    if novo_valor != str(valor_atual):
                                        novos_valores[col] = novo_valor
                        
                        # Botões de ação
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("✅ Salvar Alterações", type="primary"):
                                if novos_valores:
                                    try:
                                        cursor = conexao.cursor()
                                        
                                        # Construir query UPDATE
                                        set_clause = ", ".join([f"`{col}` = %s" for col in novos_valores.keys()])
                                        valores = list(novos_valores.values()) + [id_selecionado]
                                        
                                        query = f"UPDATE `{tabela}` SET {set_clause} WHERE `{coluna_id}` = %s"
                                        cursor.execute(query, valores)
                                        conexao.commit()
                                        
                                        linhas_afetadas = cursor.rowcount
                                        cursor.close()
                                        
                                        if linhas_afetadas > 0:
                                            st.success(f"✅ Registro atualizado com sucesso!")
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            st.warning("Nenhuma alteração foi feita.")
                                            
                                    except Exception as e:
                                        conexao.rollback()
                                        st.error(f"❌ Erro ao atualizar: {e}")
                                else:
                                    st.warning("Nenhuma alteração foi feita.")
                        
                        with col2:
                            if st.button("🔄 Cancelar e Recarregar"):
                                st.rerun()
                        
                        # Mostrar preview das alterações
                        if novos_valores:
                            st.write("---")
                            st.write("**Resumo das alterações:**")
                            
                            preview_df = pd.DataFrame({
                                'Campo': list(novos_valores.keys()),
                                'Valor Antigo': [str(valores_atuais[col]) for col in novos_valores.keys()],
                                'Valor Novo': list(novos_valores.values())
                            })
                            st.dataframe(preview_df, use_container_width=True)
                    else:
                        st.error("Registro não encontrado!")
            else:
                st.error("Não foi possível identificar a coluna chave.")
        else:
            st.info(f"ℹ️ A tabela '{tabela}' está vazia.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados para atualização: {e}")

# ==================== 5. FUNÇÃO EXCLUIR (COMPLETA) ====================
def operacao_delete_ui(conexao, tabela):
    """Interface para excluir registros"""
    st.subheader(f"🗑️ Excluir Registro de '{tabela}'")
    
    try:
        # Primeiro, listar registros
        cursor = conexao.cursor()
        cursor.execute(f"SELECT * FROM `{tabela}` LIMIT 30")
        registros = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        
        if registros:
            st.warning("⚠️ **ATENÇÃO:** Esta operação é irreversível!")
            st.info("Selecione os registros que deseja excluir:")
            
            # Converter para DataFrame
            df = pd.DataFrame(registros, columns=colunas)
            
            # Adicionar coluna de seleção
            df['Selecionar'] = False
            
            # Mostrar tabela com checkbox
            edited_df = st.data_editor(
                df,
                column_config={
                    "Selecionar": st.column_config.CheckboxColumn(
                        "Selecionar",
                        help="Marque os registros para excluir",
                        default=False,
                    )
                },
                disabled=colunas,
                hide_index=True,
                use_container_width=True
            )
            
            # Identificar registros selecionados
            registros_selecionados = edited_df[edited_df['Selecionar']]
            
            if not registros_selecionados.empty:
                st.write(f"**📋 {len(registros_selecionados)} registro(s) selecionado(s) para exclusão:**")
                st.dataframe(registros_selecionados[colunas], use_container_width=True)
                
                # Encontrar coluna chave primária
                estrutura = obter_estrutura_tabela(conexao, tabela)
                coluna_id = None
                
                if estrutura is not None:
                    pk_cols = estrutura[estrutura['Chave'].str.contains('PRI|UNI', na=False)]
                    if not pk_cols.empty:
                        coluna_id = pk_cols.iloc[0]['Campo']
                    else:
                        coluna_id = colunas[0]
                
                if coluna_id and coluna_id in registros_selecionados.columns:
                    # Preparar confirmação
                    st.error("⚠️ **CONFIRMAÇÃO DE EXCLUSÃO**")
                    
                    # Listar IDs que serão excluídos
                    ids_para_excluir = registros_selecionados[coluna_id].tolist()
                    st.write(f"**Serão excluídos os registros com {coluna_id}:**")
                    for id_val in ids_para_excluir:
                        st.write(f"- `{id_val}`")
                    
                    # Campo de confirmação
                    confirmacao = st.text_input(
                        f"Digite 'EXCLUIR' para confirmar a exclusão de {len(ids_para_excluir)} registro(s):"
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🗑️ Confirmar Exclusão", type="primary", disabled=(confirmacao != "EXCLUIR")):
                            try:
                                cursor = conexao.cursor()
                                
                                # Excluir cada registro
                                excluidos = 0
                                for id_val in ids_para_excluir:
                                    query = f"DELETE FROM `{tabela}` WHERE `{coluna_id}` = %s"
                                    cursor.execute(query, (id_val,))
                                    excluidos += cursor.rowcount
                                
                                conexao.commit()
                                cursor.close()
                                
                                st.success(f"✅ {excluidos} registro(s) excluído(s) com sucesso!")
                                st.rerun()
                                
                            except Exception as e:
                                conexao.rollback()
                                st.error(f"❌ Erro ao excluir registros: {e}")
                    
                    with col2:
                        if st.button("↩️ Cancelar Seleção"):
                            st.rerun()
                    
                    with col3:
                        if st.button("🔄 Ver Todos os Registros"):
                            # Mostrar todos os registros restantes
                            cursor = conexao.cursor()
                            cursor.execute(f"SELECT COUNT(*) as total, COUNT(*) - {len(ids_para_excluir)} as restantes FROM `{tabela}`")
                            counts = cursor.fetchone()
                            cursor.close()
                            
                            st.info(f"Total na tabela: {counts[0]} | Restarão: {counts[1]}")
                else:
                    st.error("Não foi possível identificar a coluna chave para exclusão.")
            else:
                st.info("Nenhum registro selecionado para exclusão.")
                
                # Opção de exclusão por ID
                st.write("---")
                st.write("**Ou excluir por ID específico:**")
                
                estrutura = obter_estrutura_tabela(conexao, tabela)
                if estrutura is not None:
                    pk_cols = estrutura[estrutura['Chave'].str.contains('PRI|UNI', na=False)]
                    if not pk_cols.empty:
                        coluna_id = pk_cols.iloc[0]['Campo']
                        
                        id_para_excluir = st.text_input(f"Digite o {coluna_id} do registro a excluir:")
                        
                        if id_para_excluir:
                            # Verificar se existe
                            cursor = conexao.cursor()
                            query = f"SELECT * FROM `{tabela}` WHERE `{coluna_id}` = %s"
                            cursor.execute(query, (id_para_excluir,))
                            registro = cursor.fetchone()
                            cursor.close()
                            
                            if registro:
                                st.write("**Registro encontrado:**")
                                reg_df = pd.DataFrame([registro], columns=colunas)
                                st.dataframe(reg_df, use_container_width=True)
                                
                                confirmacao = st.text_input(
                                    f"Digite 'EXCLUIR' para confirmar a exclusão do registro {coluna_id}={id_para_excluir}:",
                                    key="confirm_excluir_id"
                                )
                                
                                if st.button("🗑️ Excluir Este Registro", disabled=(confirmacao != "EXCLUIR")):
                                    try:
                                        cursor = conexao.cursor()
                                        query = f"DELETE FROM `{tabela}` WHERE `{coluna_id}` = %s"
                                        cursor.execute(query, (id_para_excluir,))
                                        conexao.commit()
                                        cursor.close()
                                        
                                        st.success("✅ Registro excluído com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        conexao.rollback()
                                        st.error(f"❌ Erro ao excluir: {e}")
                            else:
                                st.warning(f"Registro com {coluna_id}={id_para_excluir} não encontrado.")
        else:
            st.info(f"ℹ️ A tabela '{tabela}' está vazia.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados para exclusão: {e}")

# ==================== 6. FUNÇÃO ESTATÍSTICAS (COMPLETA) ====================
def mostrar_estatisticas(conexao, tabela):
    """Mostra estatísticas detalhadas da tabela"""
    st.subheader(f"📊 Estatísticas da Tabela '{tabela}'")
    
    try:
        # Obter estrutura da tabela
        estrutura = obter_estrutura_tabela(conexao, tabela)
        
        if estrutura is not None:
            # Contagem total
            cursor = conexao.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM `{tabela}`")
            total = cursor.fetchone()[0]
            
            # Informações básicas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📈 Total de Registros", f"{total:,}")
            
            with col2:
                st.metric("🔧 Total de Colunas", len(estrutura))
            
            with col3:
                # Tamanho da tabela
                cursor.execute(f"""
                    SELECT 
                        ROUND(((data_length + index_length) / 1024 / 1024), 2) as tamanho_mb
                    FROM information_schema.TABLES 
                    WHERE table_schema = DATABASE()
                    AND table_name = %s
                """, (tabela,))
                
                tamanho = cursor.fetchone()
                if tamanho and tamanho[0]:
                    st.metric("💾 Tamanho Aprox.", f"{tamanho[0]} MB")
                else:
                    st.metric("💾 Tamanho Aprox.", "N/A")
            
            st.write("---")
            
            # Abas para diferentes tipos de estatísticas
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Estrutura", "📈 Análise de Dados", "🎯 Chaves e Índices", "⚡ Performance"])
            
            with tab1:
                st.write("**Estrutura Completa da Tabela:**")
                st.dataframe(estrutura, use_container_width=True)
                
                # Resumo por tipo de dado
                st.write("**Resumo por Tipo de Dado:**")
                tipo_contagem = estrutura['Tipo'].value_counts()
                st.bar_chart(tipo_contagem)
            
            with tab2:
                st.write("**Análise de Dados por Coluna:**")
                
                # Para cada coluna, mostrar estatísticas básicas
                for _, row in estrutura.iterrows():
                    campo = row['Campo']
                    tipo = row['Tipo']
                    
                    with st.expander(f"📊 {campo} ({tipo})"):
                        try:
                            # Estatísticas básicas
                            if 'int' in tipo.lower() or 'decimal' in tipo.lower() or 'float' in tipo.lower():
                                # Colunas numéricas
                                cursor.execute(f"""
                                    SELECT 
                                        COUNT(*) as total,
                                        COUNT(DISTINCT `{campo}`) as distintos,
                                        MIN(`{campo}`) as minimo,
                                        MAX(`{campo}`) as maximo,
                                        AVG(`{campo}`) as media,
                                        STD(`{campo}`) as desvio_padrao
                                    FROM `{tabela}`
                                """)
                            else:
                                # Colunas de texto/data
                                cursor.execute(f"""
                                    SELECT 
                                        COUNT(*) as total,
                                        COUNT(DISTINCT `{campo}`) as distintos,
                                        MIN(`{campo}`) as minimo,
                                        MAX(`{campo}`) as maximo
                                    FROM `{tabela}`
                                """)
                            
                            stats = cursor.fetchone()
                            
                            if stats:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("Total", stats[0])
                                    st.metric("Valores Distintos", stats[1])
                                
                                with col2:
                                    st.metric("Mínimo", stats[2])
                                    st.metric("Máximo", stats[3])
                                
                                if len(stats) > 4:
                                    st.metric("Média", f"{stats[4]:.2f}")
                                    st.metric("Desvio Padrão", f"{stats[5]:.2f}")
                            
                            # Valores NULL
                            cursor.execute(f"SELECT COUNT(*) FROM `{tabela}` WHERE `{campo}` IS NULL")
                            null_count = cursor.fetchone()[0]
                            
                            if null_count > 0:
                                st.warning(f"⚠️ {null_count} valores NULL ({null_count/total*100:.1f}%)")
                            else:
                                st.success("✅ Sem valores NULL")
                                
                        except Exception as e:
                            st.info(f"Não foi possível analisar esta coluna: {e}")
            
            with tab3:
                st.write("**Chaves e Índices:**")
                
                # Informações de chaves
                chaves_primarias = estrutura[estrutura['Chave'] == 'PRI']
                chaves_unicas = estrutura[estrutura['Chave'] == 'UNI']
                chaves_multiplas = estrutura[estrutura['Chave'].str.contains('MUL', na=False)]
                
                if not chaves_primarias.empty:
                    st.success("**Chave Primária:**")
                    st.dataframe(chaves_primarias[['Campo', 'Tipo', 'Extra']], use_container_width=True)
                else:
                    st.warning("⚠️ Nenhuma chave primária definida")
                
                if not chaves_unicas.empty:
                    st.info("**Chaves Únicas:**")
                    st.dataframe(chaves_unicas[['Campo', 'Tipo', 'Extra']], use_container_width=True)
                
                if not chaves_multiplas.empty:
                    st.info("**Chaves Estrangeiras/Índices:**")
                    st.dataframe(chaves_multiplas[['Campo', 'Tipo', 'Extra']], use_container_width=True)
            
            with tab4:
                st.write("**Métricas de Performance:**")
                
                try:
                    # Informações de performance
                    cursor.execute(f"""
                        SELECT 
                            ENGINE as motor,
                            ROW_FORMAT as formato_linha,
                            TABLE_ROWS as linhas_estimadas,
                            AVG_ROW_LENGTH as tamanho_medio_linha,
                            DATA_LENGTH as tamanho_dados,
                            INDEX_LENGTH as tamanho_indices,
                            CREATE_TIME as criada_em,
                            UPDATE_TIME as atualizada_em
                        FROM information_schema.TABLES 
                        WHERE table_schema = DATABASE()
                        AND table_name = %s
                    """, (tabela,))
                    
                    perf_info = cursor.fetchone()
                    descricao = cursor.description
                    
                    if perf_info:
                        perf_dict = {}
                        for i, col in enumerate(descricao):
                            perf_dict[col[0]] = perf_info[i]
                        
                        perf_df = pd.DataFrame([perf_dict])
                        st.dataframe(perf_df.T.rename(columns={0: 'Valor'}), use_container_width=True)
                        
                        # Gráfico de tamanhos
                        if perf_dict['tamanho_dados'] and perf_dict['tamanho_indices']:
                            tamanhos = {
                                'Dados': perf_dict['tamanho_dados'],
                                'Índices': perf_dict['tamanho_indices']
                            }
                            st.bar_chart(tamanhos)
                    
                except Exception as e:
                    st.info(f"Não foi possível obter métricas de performance: {e}")
            
            cursor.close()
        
        else:
            st.error("Não foi possível obter a estrutura da tabela.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar estatísticas: {e}")

# ==================== FUNÇÃO PRINCIPAL (ÚNICA) ====================
def pagina_formularios():
    """Função principal da página de formulários"""
    
    # ============ ETAPA 0: VERIFICAR BANCO ATIVO ============
    st.title("📋 Sistema de Gerenciamento de Banco de Dados")
    
    # Adicionar CSS
    st.markdown("""
    <style>
    .status-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
    }
    .banco-ativo {
        background-color: #e3f2fd;
        padding: 12px 15px;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Verifica se há banco ativo da barra lateral
    if "banco_ativo" in st.session_state and st.session_state.banco_ativo:
        banco_atual = st.session_state.banco_ativo
        
        # Mostrar banner com o banco ativo
        st.markdown(f"""
        <div class="banco-ativo">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #1565c0;">🎯 Banco Ativo:</strong>
                    <span style="color: #0d47a1; font-weight: bold; margin-left: 10px; font-size: 18px;">
                        {banco_atual}
                    </span>
                </div>
                <div>
                    <button onclick="window.location.reload()" 
                            style="background-color: #bbdefb; border: 1px solid #90caf9; 
                                   padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                        🔄 Trocar
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Opção para trocar de banco
        with st.expander("🔁 Usar outro banco", expanded=False):
            bancos = listar_bancos_simples()
            if bancos:
                novo_banco = st.selectbox(
                    "Selecione outro banco:",
                    options=bancos,
                    index=bancos.index(banco_atual) if banco_atual in bancos else 0,
                    key="select_banco_trocar"
                )
                
                if novo_banco != banco_atual:
                    if st.button("✅ Mudar para este banco"):
                        st.session_state.banco_ativo = novo_banco
                        st.rerun()
        
        banco_selecionado = banco_atual
        
    else:
        # Se não tem banco ativo, mostrar seletor
        st.warning("⚠️ Nenhum banco selecionado na barra lateral")
        st.info("Selecione um banco abaixo ou na barra lateral")
        
        bancos = listar_bancos_simples()
        if not bancos:
            st.warning("Nenhum banco de dados encontrado!")
            return
        
        banco_selecionado = st.selectbox(
            "Banco de dados:",
            options=bancos,
            key="select_banco_fallback"
        )
        
        if st.button("✅ Usar este banco", type="primary"):
            st.session_state.banco_ativo = banco_selecionado
            st.rerun()
            return
    
    # ========== CONEXÃO COM BANCO SELECIONADO ==========
    try:
        conexao = conectar_banco(banco_selecionado)
        
        if conexao is None:
            st.error(f"❌ Não foi possível conectar ao banco '{banco_selecionado}'")
            return
        
        st.success(f"✅ Conectado ao banco: **{banco_selecionado}**")
        
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco: {e}")
        return
    
    # ========== ETAPA 1: LISTAR TABELAS ==========
    tabelas = listar_tabelas(conexao)
    
    if not tabelas:
        st.warning(f"⚠️ Nenhuma tabela encontrada no banco '{banco_selecionado}'")
        
        # Opção para criar tabela de exemplo
        if st.button("📝 Criar Tabela de Exemplo"):
            try:
                cursor = conexao.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS clientes (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        nome VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE,
                        idade INT,
                        cidade VARCHAR(50),
                        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Inserir alguns dados de exemplo
                cursor.execute("""
                    INSERT IGNORE INTO clientes (nome, email, idade, cidade) VALUES
                    ('João Silva', 'joao@email.com', 30, 'São Paulo'),
                    ('Maria Santos', 'maria@email.com', 25, 'Rio de Janeiro'),
                    ('Pedro Oliveira', 'pedro@email.com', 35, 'Belo Horizonte')
                """)
                
                conexao.commit()
                cursor.close()
                
                st.success("✅ Tabela 'clientes' criada com dados de exemplo!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao criar tabela: {e}")
        
        conexao.close()
        return
    
    # ========== ETAPA 2: SELEÇÃO DE TABELA ==========
    st.write("### 1. Selecione uma Tabela")
    
    tabela_selecionada = st.selectbox(
        "📊 Tabela:",
        tabelas,
        key="tabela_selector"
    )
    
    if tabela_selecionada:
        # Mostrar resumo
        mostrar_resumo_tabela(conexao, tabela_selecionada)
        
        # ========== ETAPA 3: SELEÇÃO DE OPERAÇÃO ==========
        st.write("### 2. Selecione uma Operação")
        
        operacao = st.radio(
            "🔧 Operação:",
            ["📋 Listar Registros", "➕ Criar Registro", "🔍 Buscar Registros", 
             "🔄 Atualizar Registro", "🗑️ Excluir Registro", "📊 Estatísticas"],
            horizontal=True
        )
        
        st.write("---")
        
        if operacao == "📋 Listar Registros":
            listar_registros(conexao, tabela_selecionada)
            
        elif operacao == "➕ Criar Registro":
            operacao_create_ui(conexao, tabela_selecionada)
            
        elif operacao == "🔍 Buscar Registros":
            operacao_read_ui(conexao, tabela_selecionada)
            
        elif operacao == "🔄 Atualizar Registro":
            operacao_update_ui(conexao, tabela_selecionada)
            
        elif operacao == "🗑️ Excluir Registro":
            operacao_delete_ui(conexao, tabela_selecionada)
            
        elif operacao == "📊 Estatísticas":
            mostrar_estatisticas(conexao, tabela_selecionada)
    
    # Fechar conexão
    conexao.close()

# ============ EXECUÇÃO PRINCIPAL ============
if __name__ == "__main__":
    pagina_formularios()