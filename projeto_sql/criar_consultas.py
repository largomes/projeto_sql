import streamlit as st
import re
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
from modules.listar_banco import pagina_listar_bancos

# ============ SISTEMA DE CONEXÃO ============
def conectar_banco(database=None):
    """Conecta ao MySQL usando a conexão existente ou cria nova"""
    # Primeiro, tenta usar a conexão do app.py
    if "conexao_mysql" in st.session_state and st.session_state.conexao_mysql:
        conexao = st.session_state.conexao_mysql
        
        # Se pediu banco específico, tenta usar
        if database and database != conexao.database:
            try:
                cursor = conexao.cursor()
                cursor.execute(f"USE {database}")
                cursor.close()
                conexao.database = database
                return conexao
            except:
                pass
        return conexao
    
    # Se não tem conexão no session_state, cria nova
    try:
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=database
        )
        return conexao
    except Error as e:
        st.error(f"Erro: {e}")
        return None

def listar_bancos():
    """Lista todos os bancos disponíveis"""
    try:
        # Cria nova conexão sem banco específico para ver TODOS os bancos
        conexao_temp = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conexao_temp.cursor()
        cursor.execute("SHOW DATABASES")
        todos_bancos = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conexao_temp.close()
        
        # Filtra bancos de sistema
        bancos = [b for b in todos_bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
        
        return bancos
        
    except Exception as e:
        st.error(f"Erro ao listar bancos: {e}")
        return []

def listar_tabelas(banco):
    """Lista tabelas de um banco"""
    try:
        conexao = conectar_banco(banco)
        if not conexao:
            return []
        
        cursor = conexao.cursor()
        cursor.execute("SHOW TABLES")
        tabelas = [t[0] for t in cursor.fetchall()]
        cursor.close()
        return tabelas
    except:
        return []

def obter_colunas_tabela(conexao, tabela):
    """Obtém colunas de uma tabela"""
    try:
        cursor = conexao.cursor()
        cursor.execute(f"DESCRIBE {tabela}")
        colunas_info = cursor.fetchall()
        cursor.close()
        
        colunas = []
        tipos = {}
        
        for col in colunas_info:
            nome = col[0]
            tipo = col[1]
            colunas.append(nome)
            tipos[nome] = tipo
        
        return {
            'colunas': colunas,
            'tipos': tipos,
            'colunas_texto': [c for c in colunas if any(k in tipos[c].lower() for k in ['char', 'text', 'varchar'])],
            'colunas_numero': [c for c in colunas if any(k in tipos[c].lower() for k in ['int', 'decimal', 'float', 'double'])],
            'colunas_data': [c for c in colunas if any(k in tipos[c].lower() for k in ['date', 'time', 'timestamp'])]
        }
    except:
        return None

# ============ SISTEMA DE CONSULTAS VISUAIS ============

def gerar_consulta_sql(tabelas_selecionadas, campos_selecionados, criterios=None, ordenacao=None, limite=None, joins=None, agregacoes=None):
    """
    Gera SQL baseado nas seleções do usuário
    """
    
    # 1. SELECT com agregações
    if not campos_selecionados and not agregacoes:
        campos_select = ["*"]
    else:
        campos_select = []
        
        # Adiciona campos normais
        if campos_selecionados:
            campos_select.extend(campos_selecionados)
        
        # Adiciona campos com agregações
        if agregacoes:
            for agg in agregacoes:
                campo = agg['campo']
                funcao = agg['funcao']
                alias = agg.get('alias', f"{funcao}_{campo.split('.')[-1]}")
                
                if funcao == "COUNT(DISTINCT)":
                    campos_select.append(f"COUNT(DISTINCT {campo}) AS {alias}")
                else:
                    campos_select.append(f"{funcao}({campo}) AS {alias}")
    
    campos_str = ", ".join(campos_select)
    
    # 2. FROM com JOINs
    if len(tabelas_selecionadas) == 1:
        from_str = tabelas_selecionadas[0]
    else:
        if joins:
            # Construir JOINs
            from_str = tabelas_selecionadas[0]
            for join in joins:
                join_type = join.get('tipo', 'INNER JOIN')
                from_str += f" {join_type} {join['tabela2']} ON {join['tabela1']}.{join['coluna1']} = {join['tabela2']}.{join['coluna2']}"
        else:
            # JOIN simples (CROSS JOIN)
            from_str = ", ".join(tabelas_selecionadas)
    
    # 3. WHERE
    where_str = ""
    if criterios:
        where_conditions = []
        for i, criterio in enumerate(criterios):
            campo = criterio.get('campo')
            operador = criterio.get('operador', '=')
            valor = criterio.get('valor')
            
            # Formata valor baseado no tipo e operador
            if operador in ["IN", "NOT IN"] and valor:
                # Para IN, espera-se valores separados por vírgula
                valores = [v.strip() for v in valor.split(',')]
                valores_formatados = []
                for v in valores:
                    if isinstance(v, str) and not v.replace('.', '', 1).isdigit():
                        valores_formatados.append(f"'{v}'")
                    else:
                        valores_formatados.append(v)
                valor_str = f"({', '.join(valores_formatados)})"
                condition = f"{campo} {operador} {valor_str}"
            
            elif operador in ["IS NULL", "IS NOT NULL"]:
                condition = f"{campo} {operador}"
            
            else:
                # Formatação normal
                if isinstance(valor, str) and not valor.replace('.', '', 1).isdigit() and valor.lower() != 'null':
                    valor_str = f"'{valor}'"
                else:
                    valor_str = str(valor)
                
                if operador == "LIKE":
                    if not valor_str.startswith("'%"):
                        valor_str = f"'%{valor_str[1:-1]}%'"
                
                condition = f"{campo} {operador} {valor_str}"
            
            where_conditions.append(condition)
        
        if where_conditions:
            # Usa a lógica do primeiro critério para todos (simplificado)
            logica = criterios[0].get('logica', 'AND') if criterios else 'AND'
            where_str = "WHERE " + f" {logica} ".join(where_conditions)
    
    # 4. GROUP BY (se houver agregações)
    group_str = ""
    if agregacoes and campos_selecionados:
        # Agrupa por campos que não estão agregados
        campos_nao_agregados = [c for c in campos_selecionados 
                               if c not in [agg['campo'] for agg in agregacoes]]
        if campos_nao_agregados:
            group_str = "GROUP BY " + ", ".join(campos_nao_agregados)
    
    # 5. ORDER BY
    order_str = ""
    if ordenacao:
        orders = []
        for order in ordenacao:
            campo = order.get('campo')
            direcao = order.get('direcao', 'ASC')
            orders.append(f"{campo} {direcao}")
        order_str = "ORDER BY " + ", ".join(orders)
    
    # 6. LIMIT
    limit_str = ""
    if limite:
        limit_str = f"LIMIT {limite}"
    
    # Monta SQL final
    sql_parts = [f"SELECT {campos_str}", f"FROM {from_str}"]
    
    if where_str:
        sql_parts.append(where_str)
    if group_str:
        sql_parts.append(group_str)
    if order_str:
        sql_parts.append(order_str)
    if limit_str:
        sql_parts.append(limit_str)
    
    sql = " ".join(sql_parts)
    
    return sql

def obter_relacionamentos(conexao, tabelas):
    """Tenta inferir relacionamentos entre tabelas"""
    relacionamentos = []
    
    for tabela in tabelas:
        try:
            cursor = conexao.cursor()
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM 
                    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE 
                    TABLE_SCHEMA = '{conexao.database}' 
                    AND TABLE_NAME = '{tabela}'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            
            for col, ref_tab, ref_col in cursor.fetchall():
                if ref_tab in tabelas:
                    relacionamentos.append({
                        'tabela_origem': tabela,
                        'coluna_origem': col,
                        'tabela_destino': ref_tab,
                        'coluna_destino': ref_col
                    })
            
            cursor.close()
        except:
            continue
    
    return relacionamentos

# ============ INTERFACE STREAMLIT ============

def interface_consulta_visual():
    st.title("🔍 Construtor Visual de Consultas SQL")
    st.markdown("Crie consultas SQL sem escrever código!")
    
    # ============ ETAPA 0: VERIFICAR BANCO ATIVO DA BARRA LATERAL ============
    st.header("🎯 Banco de Dados")
    
    # Verifica se há banco ativo da barra lateral
    if "banco_ativo" in st.session_state and st.session_state.banco_ativo:
        banco_atual = st.session_state.banco_ativo
        
        # Mostrar banner com o banco ativo
        st.markdown(f"""
        <div style="background-color: #e3f2fd; padding: 12px 15px; border-radius: 8px; 
                    border-left: 4px solid #2196f3; margin-bottom: 20px;">
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
            bancos = listar_bancos()
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
        
        bancos = listar_bancos()
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
    
    # Inicializa session_state se necessário
    if 'consulta_config' not in st.session_state:
        st.session_state.consulta_config = {
            'banco_selecionado': banco_selecionado,
            'tabelas_selecionadas': [],
            'campos_selecionados': [],
            'criterios': [],
            'ordenacao': [],
            'limite': 100,
            'joins': [],
            'agregacoes': []
        }
    
    if 'campos_checkboxes' not in st.session_state:
        st.session_state.campos_checkboxes = {}
    
    # Atualiza o banco no config
    st.session_state.consulta_config['banco_selecionado'] = banco_selecionado
    
    # Conecta ao banco
    conexao = conectar_banco(banco_selecionado)
    if not conexao:
        st.error(f"Não foi possível conectar ao banco '{banco_selecionado}'!")
        return
    
    # ============ ETAPA 2: SELECIONAR TABELAS ============
    st.header("2️⃣ Selecione as Tabelas")
    
    tabelas = listar_tabelas(banco_selecionado)
    if not tabelas:
        st.warning("Nenhuma tabela encontrada!")
        return
    
    tabelas_selecionadas = st.multiselect(
        "Tabelas para consulta:",
        options=tabelas,
        default=st.session_state.consulta_config.get('tabelas_selecionadas', []),
        key="select_tabelas"
    )
    
    st.session_state.consulta_config['tabelas_selecionadas'] = tabelas_selecionadas
    
    if tabelas_selecionadas:
        # Mostra relacionamentos se houver múltiplas tabelas
        if len(tabelas_selecionadas) > 1:
            relacionamentos = obter_relacionamentos(conexao, tabelas_selecionadas)
            if relacionamentos:
                st.success("🔗 Relacionamentos encontrados:")
                for rel in relacionamentos:
                    st.write(f"{rel['tabela_origem']}.{rel['coluna_origem']} → {rel['tabela_destino']}.{rel['coluna_destino']}")
        
        # ============ ETAPA 3: DEFINIÇÃO DE JOINS ============
        if len(tabelas_selecionadas) > 1:
            st.header("3️⃣ Definir JOINs (Opcional)")
            
            if st.checkbox("Configurar JOINs entre tabelas"):
                joins = st.session_state.consulta_config.get('joins', [])
                
                st.markdown("Configure como as tabelas se relacionam:")
                
                for i in range(len(tabelas_selecionadas) - 1):
                    st.markdown(f"**JOIN {i+1}**")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        tabela1 = st.selectbox(
                            f"Tabela A",
                            tabelas_selecionadas,
                            index=min(i, len(tabelas_selecionadas)-1),
                            key=f"join_tab1_{i}"
                        )
                    
                    with col2:
                        info1 = obter_colunas_tabela(conexao, tabela1)
                        colunas1 = info1['colunas'] if info1 else []
                        col_tab1 = st.selectbox(
                            "Coluna A",
                            colunas1,
                            key=f"join_col1_{i}"
                        )
                    
                    with col3:
                        st.markdown("<div style='text-align: center; margin-top: 25px;'>→</div>", unsafe_allow_html=True)
                    
                    with col4:
                        tabelas_disponiveis = [t for t in tabelas_selecionadas if t != tabela1]
                        tabela2 = st.selectbox(
                            f"Tabela B",
                            tabelas_disponiveis,
                            key=f"join_tab2_{i}"
                        )
                    
                    with col5:
                        info2 = obter_colunas_tabela(conexao, tabela2)
                        colunas2 = info2['colunas'] if info2 else []
                        col_tab2 = st.selectbox(
                            "Coluna B",
                            colunas2,
                            key=f"join_col2_{i}"
                        )
                    
                    tipo_join = st.selectbox(
                        f"Tipo de JOIN",
                        ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN"],
                        key=f"join_type_{i}"
                    )
                    
                    if st.button(f"Adicionar JOIN {i+1}", key=f"btn_join_{i}"):
                        novo_join = {
                            'tabela1': tabela1,
                            'coluna1': col_tab1,
                            'tabela2': tabela2,
                            'coluna2': col_tab2,
                            'tipo': tipo_join
                        }
                        joins.append(novo_join)
                        st.session_state.consulta_config['joins'] = joins
                        st.success(f"JOIN {i+1} adicionado!")
                        st.rerun()
                
                # Mostra JOINs configurados
                if joins:
                    st.subheader("JOINs Configurados:")
                    for j, join in enumerate(joins):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.write(f"`{join['tabela1']}.{join['coluna1']} = {join['tabela2']}.{join['coluna2']}` ({join['tipo']})")
                        with col2:
                            if st.button("❌", key=f"del_join_{j}"):
                                joins.pop(j)
                                st.session_state.consulta_config['joins'] = joins
                                st.rerun()
        
        # ============ ETAPA 4: SELECIONAR CAMPOS ============
        st.header("4️⃣ Selecione os Campos")
        
        todas_colunas = []
        colunas_por_tabela = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Campos disponíveis:")
            campos_selecionados_local = []
            
            for tabela in tabelas_selecionadas:
                with st.expander(f"📊 {tabela}", expanded=True):
                    info_colunas = obter_colunas_tabela(conexao, tabela)
                    if info_colunas:
                        colunas_por_tabela[tabela] = info_colunas['colunas']
                        
                        for coluna in info_colunas['colunas']:
                            chave = f"{tabela}.{coluna}"
                            tipo = info_colunas['tipos'].get(coluna, '?')
                            
                            # Verifica se está selecionado no session_state
                            is_selected = chave in st.session_state.consulta_config.get('campos_selecionados', [])
                            
                            # Checkbox com estado persistente
                            if st.checkbox(f"{coluna} ({tipo})", 
                                          value=is_selected,
                                          key=f"campo_check_{chave}"):
                                campos_selecionados_local.append(chave)
        
        with col2:
            st.subheader("Campos selecionados:")
            
            # Atualiza campos selecionados no session_state
            st.session_state.consulta_config['campos_selecionados'] = campos_selecionados_local
            
            if campos_selecionados_local:
                # Multiselect para reordenar
                campos_ordenados = st.multiselect(
                    "Arraste para reordenar:",
                    options=campos_selecionados_local,
                    default=campos_selecionados_local,
                    key="reorder_campos"
                )
                
                st.session_state.consulta_config['campos_selecionados'] = campos_ordenados
                
                st.write("**Ordem atual:**")
                for i, campo in enumerate(campos_ordenados, 1):
                    st.write(f"{i}. {campo}")
            else:
                st.info("Nenhum campo selecionado. Use '*' para todos os campos.")
        
        # ============ ETAPA 5: FUNÇÕES DE AGREGAÇÃO ============
        if st.session_state.consulta_config['campos_selecionados']:
            st.header("5️⃣ Funções de Agregação (Opcional)")
            
            if st.checkbox("Adicionar funções de agregação"):
                agregacoes = st.session_state.consulta_config.get('agregacoes', [])
                
                st.markdown("**Selecione funções para os campos:**")
                
                for campo in st.session_state.consulta_config['campos_selecionados']:
                    col1, col2 = st.columns([3, 2])
                    
                    with col1:
                        st.write(f"`{campo}`")
                    
                    with col2:
                        funcao = st.selectbox(
                            "Função:",
                            ["Nenhuma", "COUNT", "SUM", "AVG", "MIN", "MAX", "COUNT(DISTINCT)"],
                            key=f"agg_select_{campo}"
                        )
                        
                        if funcao != "Nenhuma":
                            # Verifica se já existe agregação para este campo
                            existe = any(agg['campo'] == campo for agg in agregacoes)
                            
                            if not existe:
                                agregacoes.append({
                                    'campo': campo,
                                    'funcao': funcao,
                                    'alias': f"{funcao}_{campo.split('.')[-1]}"
                                })
                
                st.session_state.consulta_config['agregacoes'] = agregacoes
                
                if agregacoes:
                    st.subheader("Agregações configuradas:")
                    for agg in agregacoes:
                        st.write(f"`{agg['funcao']}({agg['campo']}) AS {agg['alias']}`")
        
        # ============ ETAPA 6: CRITÉRIOS (WHERE) ============
        st.header("6️⃣ Adicionar Critérios (Opcional)")
        
        if st.checkbox("Adicionar critérios WHERE"):
            criterios = st.session_state.consulta_config.get('criterios', [])
            
            st.markdown("**Novo critério:**")
            
            col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
            
            with col1:
                # Lista de campos para critérios
                todos_campos_criterio = []
                for tabela, cols in colunas_por_tabela.items():
                    for col in cols:
                        todos_campos_criterio.append(f"{tabela}.{col}")
                
                campo_criterio = st.selectbox(
                    "Campo:",
                    options=todos_campos_criterio,
                    key="campo_criterio"
                )
            
            with col2:
                operador = st.selectbox(
                    "Operador:",
                    options=["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "NOT IN", "IS NULL", "IS NOT NULL"],
                    key="operador_criterio"
                )
            
            with col3:
                if operador not in ["IS NULL", "IS NOT NULL"]:
                    valor_criterio = st.text_input("Valor:", key="valor_criterio")
                else:
                    valor_criterio = ""
            
            with col4:
                logica = st.selectbox(
                    "Lógica:",
                    options=["AND", "OR"],
                    key="logica_criterio"
                )
            
            if st.button("➕ Adicionar Critério", key="add_criterio"):
                if operador in ["IS NULL", "IS NOT NULL"] or valor_criterio:
                    novo_criterio = {
                        'campo': campo_criterio,
                        'operador': operador,
                        'valor': valor_criterio if valor_criterio else None,
                        'logica': logica
                    }
                    criterios.append(novo_criterio)
                    st.session_state.consulta_config['criterios'] = criterios
                    st.success("Critério adicionado!")
                    st.rerun()
                else:
                    st.warning("Por favor, insira um valor para o critério.")
            
            # Mostra critérios adicionados
            if criterios:
                st.subheader("Critérios atuais:")
                for i, crit in enumerate(criterios):
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        valor_display = crit.get('valor', '') if crit.get('valor') else ''
                        if crit['operador'] in ["IS NULL", "IS NOT NULL"]:
                            st.code(f"{crit['campo']} {crit['operador']}")
                        else:
                            st.code(f"{crit['campo']} {crit['operador']} {valor_display}")
                    with col2:
                        if i > 0:
                            st.write(f"({crit['logica']})")
                    with col3:
                        if st.button("❌", key=f"del_crit_{i}"):
                            criterios.pop(i)
                            st.session_state.consulta_config['criterios'] = criterios
                            st.rerun()
        
        # ============ ETAPA 7: ORDENAÇÃO (ORDER BY) ============
        st.header("7️⃣ Ordenação (Opcional)")
        
        if st.checkbox("Adicionar ordenação"):
            ordenacao = st.session_state.consulta_config.get('ordenacao', [])
            
            st.markdown("**Nova ordenação:**")
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                campos_para_order = st.session_state.consulta_config['campos_selecionados'].copy()
                if not campos_para_order:
                    campos_para_order = ["*"]
                
                campo_order = st.selectbox(
                    "Campo para ordenar:",
                    options=campos_para_order,
                    key="campo_order"
                )
            
            with col2:
                direcao = st.selectbox(
                    "Direção:",
                    options=["ASC", "DESC"],
                    key="direcao_order"
                )
            
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Adicionar", key="add_order"):
                    nova_ordenacao = {
                        'campo': campo_order,
                        'direcao': direcao
                    }
                    ordenacao.append(nova_ordenacao)
                    st.session_state.consulta_config['ordenacao'] = ordenacao
                    st.rerun()
            
            if ordenacao:
                st.subheader("Ordenação atual:")
                for i, order in enumerate(ordenacao):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{i+1}. `{order['campo']} {order['direcao']}`")
                    with col2:
                        if st.button("❌", key=f"del_order_{i}"):
                            ordenacao.pop(i)
                            st.session_state.consulta_config['ordenacao'] = ordenacao
                            st.rerun()
        
        # ============ ETAPA 8: LIMITE ============
        st.header("8️⃣ Limite de Linhas (Opcional)")
        
        limite = st.number_input(
            "Número máximo de linhas:",
            min_value=1,
            max_value=10000,
            value=st.session_state.consulta_config.get('limite', 100),
            key="input_limite"
        )
        st.session_state.consulta_config['limite'] = limite
        
        # ============ ETAPA 9: GERAR E EXECUTAR SQL ============
        st.header("9️⃣ Gerar e Executar Consulta")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✨ Gerar Consulta SQL", type="primary", use_container_width=True):
                # Obtém configuração atual
                config = st.session_state.consulta_config
                
                # Gera SQL
                sql = gerar_consulta_sql(
                    tabelas_selecionadas=config['tabelas_selecionadas'],
                    campos_selecionados=config['campos_selecionados'],
                    criterios=config.get('criterios', []),
                    ordenacao=config.get('ordenacao', []),
                    limite=config.get('limite'),
                    joins=config.get('joins', []),
                    agregacoes=config.get('agregacoes', [])
                )
                
                # Salva SQL no session_state
                st.session_state.sql_gerado = sql
                st.session_state.mostrar_sql = True
        
        with col2:
            if st.button("🔄 Nova Consulta", use_container_width=True):
                # Limpa configuração
                for key in ['tabelas_selecionadas', 'campos_selecionados', 'criterios', 
                           'ordenacao', 'joins', 'agregacoes']:
                    st.session_state.consulta_config[key] = []
                st.session_state.consulta_config['limite'] = 100
                st.rerun()
        
        # Mostra SQL gerado
        if st.session_state.get('mostrar_sql', False) and st.session_state.get('sql_gerado'):
            sql = st.session_state.sql_gerado
            
            st.subheader("📝 Consulta SQL Gerada:")
            
            # EDITÁVEL: Text area para editar o SQL
            sql_editavel = st.text_area(
                "Edite o SQL se necessário:",
                value=sql,
                height=150,
                key="sql_editavel"
            )
            
            # Atualiza o SQL se foi editado
            if sql_editavel != sql:
                st.session_state.sql_gerado = sql_editavel
                sql = sql_editavel
                st.info("✅ SQL atualizado com as tuas edições!")
            
            # Botões de ação
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Copiar SQL", use_container_width=True):
                    st.code(sql, language="sql")
                    st.toast("SQL copiado para a área de transferência!", icon="✅")
            
            with col2:
                if st.button("💾 Salvar SQL", use_container_width=True):
                    st.session_state.sql_salvo = sql
                    st.toast("SQL guardado no sistema!", icon="💾")
            
            with col3:
                if st.button("🔄 Restaurar Original", use_container_width=True):
                    # Gera SQL original novamente
                    config = st.session_state.consulta_config
                    sql_original = gerar_consulta_sql(
                        tabelas_selecionadas=config['tabelas_selecionadas'],
                        campos_selecionados=config['campos_selecionados'],
                        criterios=config.get('criterios', []),
                        ordenacao=config.get('ordenacao', []),
                        limite=config.get('limite'),
                        joins=config.get('joins', []),
                        agregacoes=config.get('agregacoes', [])
                    )
                    st.session_state.sql_gerado = sql_original
                    st.rerun()
            
            # Separador
            st.divider()
            
            # Executa consulta
            if st.button("▶️ Executar Consulta SQL", type="primary", use_container_width=True):
                try:
                    cursor = conexao.cursor(dictionary=True)
                    cursor.execute(sql)
                    resultados = cursor.fetchall()
                    cursor.close()
                    
                    if resultados:
                        df = pd.DataFrame(resultados)
                        st.subheader("📊 Resultados:")
                        st.dataframe(df, use_container_width=True)
                        
                        # Estatísticas
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Linhas", len(df))
                        with col2:
                            st.metric("Colunas", len(df.columns))
                        with col3:
                            tamanho_kb = df.memory_usage().sum() / 1024
                            st.metric("Tamanho", f"{tamanho_kb:.1f} KB")
                        with col4:
                            st.metric("Tipo", "SELECT")
                        
                        # Opções para exportar
                        st.subheader("📤 Exportar Resultados:")
                        col_exp1, col_exp2, col_exp3 = st.columns(3)
                        
                        with col_exp1:
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"consulta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        with col_exp2:
                            # Exportar para Excel
                            import io
                            from openpyxl import Workbook
                            
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Consulta')
                            
                            st.download_button(
                                label="📊 Download Excel",
                                data=output.getvalue(),
                                file_name=f"consulta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        with col_exp3:
                            json_str = df.to_json(orient='records', indent=2)
                            st.download_button(
                                label="📄 Download JSON",
                                data=json_str,
                                file_name=f"consulta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                    else:
                        st.info("✅ Consulta executada com sucesso, mas sem resultados.")
                        
                except Error as e:
                    st.error(f"❌ Erro ao executar consulta: {e}")
                    st.error(f"SQL problemático: ```{sql}```")

# ============ EXECUÇÃO PRINCIPAL ============
if __name__ == "__main__":
    interface_consulta_visual()