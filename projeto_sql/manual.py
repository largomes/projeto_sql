# manual.py - Guia MySQL
import streamlit as st

def pagina_guia():
    st.title("📚 Guia MySQL")
    
    # Configurar estado da seção se não existir
    if "guia_secao" not in st.session_state:
        st.session_state.guia_secao = "basico"
    
    # Menu do guia
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        if st.button("🗄️ Básico", use_container_width=True):
            st.session_state.guia_secao = "basico"
            st.rerun()
    with col_g2:
        if st.button("🔍 Consultas", use_container_width=True):
            st.session_state.guia_secao = "consultas"
            st.rerun()
    with col_g3:
        if st.button("🏗️ Tabelas", use_container_width=True):
            st.session_state.guia_secao = "tabelas"
            st.rerun()
    with col_g4:
        if st.button("⚡ Avançado", use_container_width=True):
            st.session_state.guia_secao = "avancado"
            st.rerun()
    
    st.markdown("---")
    
    # Conteúdo baseado na seção
    secao = st.session_state.guia_secao
    
    if secao == "basico":
        st.subheader("🗄️ Conceitos Básicos")
        st.write("""
        **MySQL** é um sistema de gerenciamento de banco de dados relacional.
        
        **Exemplo de criação:**
        """)
        st.code("""
CREATE DATABASE meu_banco;
USE meu_banco;

CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100),
    email VARCHAR(150) UNIQUE
);
        """, language="sql")
        
        st.write("""
        **Comandos básicos:**
        - `SHOW DATABASES;` - Lista todos os bancos
        - `USE nome_banco;` - Seleciona um banco
        - `SHOW TABLES;` - Mostra tabelas do banco atual
        """)
    
    elif secao == "consultas":
        st.subheader("🔍 Consultas SQL")
        st.code("""
-- SELECT básico
SELECT * FROM tabela;

-- SELECT com filtro
SELECT nome, email 
FROM usuarios 
WHERE ativo = 1;

-- SELECT com ordenação
SELECT * FROM produtos 
ORDER BY preco DESC;

-- SELECT com agregação
SELECT categoria, COUNT(*) as total
FROM produtos
GROUP BY categoria;
        """, language="sql")
    
    elif secao == "tabelas":
        st.subheader("🏗️ Estrutura de Tabelas")
        st.code("""
-- Criar tabela com chaves
CREATE TABLE pedidos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT,
    data_pedido DATE DEFAULT CURRENT_DATE,
    valor DECIMAL(10, 2),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Alterar tabela
ALTER TABLE usuarios 
ADD COLUMN data_cadastro DATE;

-- Excluir tabela
DROP TABLE nome_tabela;
        """, language="sql")
    
    elif secao == "avancado":
        st.subheader("⚡ Tópicos Avançados")
        st.code("""
-- JOIN entre tabelas
SELECT u.nome, p.valor, p.data_pedido
FROM usuarios u
JOIN pedidos p ON u.id = p.usuario_id;

-- Subquery
SELECT nome FROM usuarios 
WHERE id IN (
    SELECT usuario_id FROM pedidos 
    WHERE valor > 1000
);

-- Views
CREATE VIEW vista_usuarios_ativos AS
SELECT * FROM usuarios WHERE ativo = 1;
        """, language="sql")
    
    # Botão de voltar para home
    st.markdown("---")
    if st.button("🏠 Voltar para Página Inicial"):
        st.session_state.pagina = "home"
        st.rerun()