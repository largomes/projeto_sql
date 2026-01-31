# verificar_docker.py - Execute ANTES do app.py
import streamlit as st
import subprocess
import time
import os

st.set_page_config(page_title="Verificador Docker", layout="wide")
st.title("🔍 Verificação do Sistema")

# ============ VERIFICAÇÕES ============
st.header("1. 🐳 Status do Docker")

try:
    # Verificar se Docker está instalado
    result = subprocess.run(["docker", "--version"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        st.success(f"✅ Docker instalado: {result.stdout.strip()}")
        
        # Verificar se Docker está rodando
        result = subprocess.run(["docker", "info"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            st.success("✅ Docker Engine está rodando")
            
            # Verificar imagens MySQL disponíveis
            result = subprocess.run(["docker", "images", "mysql"], 
                                  capture_output=True, text=True)
            
            if "mysql" in result.stdout:
                st.success("✅ Imagem MySQL disponível")
            else:
                st.warning("⚠️ Imagem MySQL não encontrada")
                st.info("Baixando automaticamente quando iniciar...")
                
        else:
            st.error("❌ Docker Engine não está rodando")
            st.info("""
            **Soluções:**
            1. **Windows/Mac:** Abra o Docker Desktop
            2. **Linux:** `sudo systemctl start docker`
            3. Aguarde o ícone do Docker ficar verde
            """)
            
    else:
        st.error("❌ Docker não está instalado")
        st.markdown("""
        **Baixe e instale:**
        - **Windows:** https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
        - **Mac:** https://desktop.docker.com/mac/main/amd64/Docker.dmg
        - **Linux:** `sudo apt-get install docker.io`
        """)
        
except Exception as e:
    st.error(f"❌ Erro ao verificar Docker: {e}")

st.markdown("---")

# ============ TESTE MYSQL DOCKER ============
st.header("2. 🗄️ Teste MySQL Docker")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Testar Inicialização MySQL Docker", type="primary"):
        with st.spinner("Iniciando MySQL Docker..."):
            try:
                # Parar container existente
                subprocess.run(["docker", "stop", "test_mysql"], 
                             capture_output=True)
                subprocess.run(["docker", "rm", "test_mysql"], 
                             capture_output=True)
                
                # Iniciar novo container
                cmd = [
                    "docker", "run", "-d",
                    "--name", "test_mysql",
                    "-p", "3307:3306",  # Porta diferente para teste
                    "-e", "MYSQL_ROOT_PASSWORD=test123",
                    "mysql:8.0"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    st.success("✅ Container MySQL criado!")
                    
                    # Aguardar inicialização
                    time.sleep(10)
                    
                    # Verificar se está rodando
                    result = subprocess.run(
                        ["docker", "ps", "--filter", "name=test_mysql"],
                        capture_output=True, text=True
                    )
                    
                    if "Up" in result.stdout:
                        st.success("✅ MySQL Docker está rodando!")
                        st.code("""
                        Conexão de teste:
                        Host: localhost
                        Porta: 3307
                        Usuário: root
                        Senha: test123
                        """)
                    else:
                        st.error("❌ Container não iniciou")
                        
                else:
                    st.error(f"❌ Erro: {result.stderr}")
                    
            except Exception as e:
                st.error(f"❌ Exception: {e}")

with col2:
    if st.button("🛑 Parar Teste MySQL"):
        result = subprocess.run(["docker", "stop", "test_mysql"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            st.success("✅ Container parado")
        else:
            st.info("Container já estava parado")

st.markdown("---")

# ============ VERIFICAÇÃO DE MÓDULOS ============
st.header("3. 📁 Seus Módulos")

# Listar arquivos .py no diretório
arquivos_py = [f for f in os.listdir(".") if f.endswith('.py') and f != "verificar_docker.py"]

st.write(f"**{len(arquivos_py)} arquivos Python encontrados:**")

# Mostrar em colunas
cols = st.columns(3)
for idx, arquivo in enumerate(sorted(arquivos_py)):
    with cols[idx % 3]:
        tamanho = os.path.getsize(arquivo)
        emoji = "✅" if tamanho > 100 else "⚠️"
        st.write(f"{emoji} {arquivo} ({tamanho} bytes)")

st.markdown("---")

# ============ CONFIGURAÇÃO FINAL ============
st.header("4. 🎯 Próximos Passos")

st.markdown("""
### **Se Docker funcionou:**
1. **Copie o novo `app.py`** que lhe enviei
2. **Execute:** `streamlit run app.py`
3. **Clique em "🐳 Iniciar Docker"** na sidebar

### **Se Docker falhou:**
1. **Reinicie o computador**
2. **Abra Docker Desktop** (Windows/Mac)
3. **Execute este script novamente**

### **Arquivos essenciais que deve ter:**
- ✅ `app.py` (principal)
- ✅ `Formularios.py` (seus formulários)
- ✅ Pelo menos 5-6 módulos funcionais

### **Comando rápido para limpar:**
```bash
# Parar todos containers Docker
docker stop $(docker ps -q)

# Limpar containers parados
docker system prune -f
""")