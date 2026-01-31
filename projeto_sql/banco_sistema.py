# banco_sistema.py
import streamlit as st

def get_banco_trabalho():
    """Retorna o banco de trabalho atual"""
    return st.session_state.get("banco_ativo")

def set_banco_trabalho(nome_banco):
    """Define o banco de trabalho"""
    st.session_state.banco_ativo = nome_banco
    return nome_banco

def verificar_banco_necessario():
    """Verifica se há banco selecionado, mostra seletor se não houver"""
    banco_atual = get_banco_trabalho()
    
    if banco_atual:
        # Mostrar banner com o banco
        st.markdown(f"""
        <div style="background-color: #e3f2fd; padding: 12px; border-radius: 8px; 
                    border-left: 4px solid #2196f3; margin: 10px 0 20px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #1565c0;">🎯 Banco Ativo:</strong>
                    <span style="color: #0d47a1; font-weight: bold; margin-left: 10px;">
                        {banco_atual}
                    </span>
                </div>
                <button onclick="window.location.reload()" 
                        style="background-color: #bbdefb; border: 1px solid #90caf9; 
                               padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                    🔄 Trocar
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return banco_atual
    
    # Se não tem banco, mostrar seletor
    st.warning("⚠️ Selecione um banco de dados para continuar")
    return None