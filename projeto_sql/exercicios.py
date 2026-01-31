# exercicios.py - Exercícios MySQL
import streamlit as st

def pagina_exercicios():
    st.title("🎯 Exercícios MySQL")
    
    # Seletor de nível
    st.subheader("Escolha o nível de dificuldade:")
    nivel = st.radio(
        "Nível:",
        ["🥉 Iniciante", "🥈 Intermediário", "🥇 Avançado"],
        horizontal=True,
        key="nivel_exercicio"
    )
    
    st.markdown("---")
    
    # Container para exercício
    with st.container(border=True):
        # Exercício baseado no nível
        if "Iniciante" in nivel:
            st.markdown("### Exercício 1 - SELECT básico")
            st.write("""
            **Contexto:** Você tem uma tabela `produtos` com as colunas:
            - `id` (INT)
            - `nome` (VARCHAR)
            - `preco` (DECIMAL)
            - `categoria` (VARCHAR)
            
            **Desafio:** Escreva uma query para selecionar todos os produtos 
            da categoria 'Eletrônicos' com preço maior que 1000.
            """)
            
            resposta = st.text_area(
                "Sua query:",
                height=100,
                placeholder="Escreva sua query SQL aqui...",
                key="resposta_iniciante"
            )
        
        elif "Intermediário" in nivel:
            st.markdown("### Exercício 2 - JOIN entre tabelas")
            st.write("""
            **Contexto:** Você tem duas tabelas:
            
            1. `clientes` (id, nome, email)
            2. `pedidos` (id, cliente_id, valor, data)
            
            **Desafio:** Escreva uma query para listar o nome do cliente 
            e o total gasto por cada um em pedidos.
            """)
            
            resposta = st.text_area(
                "Sua query:",
                height=100,
                placeholder="Escreva sua query SQL aqui...",
                key="resposta_intermediario"
            )
        
        else:  # Avançado
            st.markdown("### Exercício 3 - Subquery complexa")
            st.write("""
            **Contexto:** Tabela `vendas` (id, produto_id, quantidade, data)
            
            **Desafio:** Escreva uma query para encontrar os produtos 
            que tiveram vendas acima da média de vendas de todos os produtos.
            """)
            
            resposta = st.text_area(
                "Sua query:",
                height=100,
                placeholder="Escreva sua query SQL aqui...",
                key="resposta_avancado"
            )
        
        # Botões de ação
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            verificar = st.button("✅ Verificar Resposta", type="primary")
        
        with col2:
            dica = st.button("💡 Ver Dica")
        
        with col3:
            solucao = st.button("📖 Ver Solução")
        
        # Ações dos botões
        if verificar and resposta.strip():
            st.success("✅ Resposta recebida! Em um sistema completo, esta query seria validada automaticamente.")
            
            # Verificação básica
            if "SELECT" not in resposta.upper():
                st.warning("⚠️ Sua query deve começar com SELECT")
            else:
                st.info("📊 Query válida! Tente executá-la no Query Editor.")
        
        elif verificar and not resposta.strip():
            st.error("❌ Por favor, escreva sua resposta primeiro!")
        
        if dica:
            with st.expander("💡 Dica:", expanded=True):
                if "Iniciante" in nivel:
                    st.write("Use: `SELECT * FROM produtos WHERE categoria = 'Eletrônicos' AND preco > 1000`")
                elif "Intermediário" in nivel:
                    st.write("Você precisará usar `JOIN` e `GROUP BY` com `SUM()`")
                else:
                    st.write("Use uma subquery para calcular a média primeiro")
        
        if solucao:
            with st.expander("📖 Solução:", expanded=True):
                if "Iniciante" in nivel:
                    st.code("SELECT * FROM produtos WHERE categoria = 'Eletrônicos' AND preco > 1000;", 
                           language="sql")
                elif "Intermediário" in nivel:
                    st.code("""SELECT c.nome, SUM(p.valor) as total_gasto
FROM clientes c
JOIN pedidos p ON c.id = p.cliente_id
GROUP BY c.id, c.nome;""", language="sql")
                else:
                    st.code("""SELECT produto_id, SUM(quantidade) as total_vendido
FROM vendas
GROUP BY produto_id
HAVING SUM(quantidade) > (
    SELECT AVG(total) FROM (
        SELECT SUM(quantidade) as total
        FROM vendas
        GROUP BY produto_id
    ) as media_vendas
);""", language="sql")
    
    # Botão de voltar para home
    st.markdown("---")
    if st.button("🏠 Voltar para Página Inicial"):
        st.session_state.pagina = "home"
        st.rerun()