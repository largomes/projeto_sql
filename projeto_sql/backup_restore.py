import streamlit as st
import os
import subprocess
import pandas as pd
from datetime import datetime
import zipfile
import shutil
from io import BytesIO

# Tentar importar módulos personalizados
try:
    from modules.backup_utils import backup_key, generate_unique_id
    USE_BACKUP_UTILS = True
except ImportError:
    # Fallback se o módulo não estiver disponível
    USE_BACKUP_UTILS = False
    import random
    import time
    
    def backup_key(base_name):
        """Fallback function"""
        return f"{base_name}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    def generate_unique_id(prefix=""):
        """Fallback function"""
        timestamp = str(time.time())
        return f"{prefix}_{hash(timestamp) % 10000}"

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    problemas = []
    # Se estamos no modo alternativo, não verificar executáveis
    if hasattr(st.session_state, 'usar_modo_alternativo') and st.session_state.usar_modo_alternativo:
        return problemas  # Retorna vazio = sem problemas
    
    # Caminhos específicos para XAMPP
    caminhos_xampp = [
        # Windows - XAMPP
        "C:\\xampp\\mysql\\bin\\mysqldump.exe",
        "C:\\xampp\\mysql\\bin\\mysql.exe",
        # Linux/Mac - XAMPP
        "/opt/lampp/bin/mysqldump",
        "/opt/lampp/bin/mysql",
        "/Applications/XAMPP/bin/mysqldump",  # macOS
        "/Applications/XAMPP/bin/mysql",      # macOS
        # Linux - padrão
        "/usr/bin/mysqldump",
        "/usr/bin/mysql",
        # Windows - padrão
        "mysqldump",
        "mysql"
    ]
    
    # Verificar mysqldump
    mysqldump_encontrado = False
    for caminho in caminhos_xampp:
        if "mysqldump" in caminho:
            if os.path.exists(caminho):
                mysqldump_encontrado = True
                break
            elif caminho == "mysqldump":
                try:
                    subprocess.run([caminho, "--version"], 
                                 capture_output=True, 
                                 timeout=2)
                    mysqldump_encontrado = True
                    break
                except:
                    continue
    
    if not mysqldump_encontrado:
        problemas.append("mysqldump")
    
    # Verificar mysql
    mysql_encontrado = False
    for caminho in caminhos_xampp:
        if "mysql" in caminho and "mysqldump" not in caminho:
            if os.path.exists(caminho):
                mysql_encontrado = True
                break
            elif caminho == "mysql":
                try:
                    subprocess.run([caminho, "--version"], 
                                 capture_output=True, 
                                 timeout=2)
                    mysql_encontrado = True
                    break
                except:
                    continue
    
    if not mysql_encontrado:
        problemas.append("mysql")
    
    return problemas

def encontrar_caminho_xampp(comando):
    """Encontra o caminho do executável no XAMPP"""
    # Lista de possíveis caminhos do XAMPP
    caminhos_base = [
        # Windows
        "C:\\xampp",
        "D:\\xampp",
        "E:\\xampp",
        # Linux
        "/opt/lampp",
        # macOS
        "/Applications/XAMPP",
    ]
    
    # Extensões possíveis
    extensoes = [".exe", ""]  # .exe para Windows, vazio para Linux/Mac
    
    for base in caminhos_base:
        for ext in extensoes:
            caminho_mysql = os.path.join(base, "mysql", "bin", f"{comando}{ext}")
            caminho_bin = os.path.join(base, "bin", f"{comando}{ext}")
            
            if os.path.exists(caminho_mysql):
                return caminho_mysql
            elif os.path.exists(caminho_bin):
                return caminho_bin
    
    # Se não encontrar, retorna o comando padrão
    return comando

# Configurações
BACKUP_DIR = "backups"
AUTO_BACKUP_DIR = os.path.join(BACKUP_DIR, "automaticos")
MANUAL_BACKUP_DIR = os.path.join(BACKUP_DIR, "manuais")

# Criar diretórios se não existirem
for dir_path in [BACKUP_DIR, AUTO_BACKUP_DIR, MANUAL_BACKUP_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Funções auxiliares
def listar_bancos():
    """Lista todos os bancos disponíveis"""
    try:
        import mysql.connector
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
        
        bancos = [b for b in todos_bancos if b not in [
            'information_schema', 'mysql', 'performance_schema', 'sys'
        ]]
        
        return bancos
        
    except Exception as e:
        st.error(f"Erro ao listar bancos: {e}")
        return []

def executar_backup_python(banco_nome, destino_dir, tipo="manual"):
    """Executa backup usando apenas Python (sem mysqldump)"""
    try:
        st.write(f"🔍 DEBUG: Iniciando backup do banco '{banco_nome}'...")
        import mysql.connector
        from mysql.connector import errors
        
        st.write(f"🔍 DEBUG: Conectando ao MySQL...")
        
        # Conectar ao banco
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=banco_nome
        )
        cursor = conexao.cursor(dictionary=True)
        
        st.write(f"✅ DEBUG: Conexão estabelecida!")
        
        # Nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{banco_nome}_{timestamp}.sql"
        caminho_completo = os.path.join(destino_dir, nome_arquivo)
        
        # Começar arquivo SQL
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup do banco: {banco_nome}\n")
            f.write(f"-- Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"SET FOREIGN_KEY_CHECKS=0;\n\n")
            f.write(f"CREATE DATABASE IF NOT EXISTS `{banco_nome}`;\n")
            f.write(f"USE `{banco_nome}`;\n\n")
            
            # 1. Listar todas as tabelas
            cursor.execute("SHOW TABLES")
            tabelas = [list(t.values())[0] for t in cursor.fetchall()]
            
            for tabela in tabelas:
                # 2. Obter estrutura da tabela (CREATE TABLE)
                cursor.execute(f"SHOW CREATE TABLE `{tabela}`")
                create_table = cursor.fetchone()
                f.write(f"--\n-- Estrutura para tabela `{tabela}`\n--\n")
                f.write(f"{create_table['Create Table']};\n\n")
                
                # 3. Obter dados da tabela
                cursor.execute(f"SELECT * FROM `{tabela}`")
                dados = cursor.fetchall()
                
                if dados:
                    f.write(f"--\n-- Dump de dados para tabela `{tabela}`\n--\n")
                    
                    # Obter nomes das colunas
                    colunas = list(dados[0].keys())
                    colunas_str = ", ".join([f"`{c}`" for c in colunas])
                    
                    f.write(f"INSERT INTO `{tabela}` ({colunas_str}) VALUES\n")
                    
                    valores_linhas = []
                    for linha in dados:
                        valores = []
                        for valor in linha.values():
                            if valor is None:
                                valores.append("NULL")
                            elif isinstance(valor, (int, float)):
                                valores.append(str(valor))
                            else:
                                # Escapar aspas simples
                                valor_str = str(valor).replace("'", "''").replace("\\", "\\\\")
                                valores.append(f"'{valor_str}'")
                        
                        valores_str = ", ".join(valores)
                        valores_linhas.append(f"({valores_str})")
                    
                    # Escrever em lotes para melhor performance
                    for i in range(0, len(valores_linhas), 100):
                        batch = valores_linhas[i:i+100]
                        f.write(",\n".join(batch))
                        if i + 100 < len(valores_linhas):
                            f.write(",\n")
                    
                    f.write(";\n\n")
            
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        
        cursor.close()
        conexao.close()
        
        # Compactar
        caminho_zip = caminho_completo.replace('.sql', '.zip')
        with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(caminho_completo, nome_arquivo)
        
        os.remove(caminho_completo)
        tamanho_mb = os.path.getsize(caminho_zip) / (1024 * 1024)
        
        registrar_log_backup(banco_nome, nome_arquivo.replace('.sql', '.zip'), 
                           tipo, tamanho_mb)
        
        return {
            "sucesso": True,
            "arquivo": caminho_zip,
            "tamanho_mb": round(tamanho_mb, 2),
            "mensagem": f"✅ Backup de '{banco_nome}' criado com sucesso (método Python)!"
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"❌ Erro no backup Python: {e}"
        }

def executar_backup(banco_nome, destino_dir, tipo="manual"):
    """Executa backup de um banco específico"""
    try:
        # Verificar se estamos em modo alternativo
        if hasattr(st.session_state, 'usar_modo_alternativo') and st.session_state.usar_modo_alternativo:
            return executar_backup_python(banco_nome, destino_dir, tipo)
        
        # Encontrar caminho do mysqldump no XAMPP
        mysqldump_path = encontrar_caminho_xampp("mysqldump")
        
        # Verificar se o executável realmente existe
        if mysqldump_path in ["mysqldump", "mysql"]:
            # Se for apenas o nome, verificar se está no PATH
            try:
                resultado = subprocess.run([mysqldump_path, "--version"], 
                                         capture_output=True, 
                                         text=True,
                                         timeout=3)
                if resultado.returncode != 0:
                    st.info("ℹ️ mysqldump não encontrado no PATH, usando método Python...")
                    return executar_backup_python(banco_nome, destino_dir, tipo)
            except:
                st.info("ℹ️ mysqldump não encontrado, usando método Python...")
                return executar_backup_python(banco_nome, destino_dir, tipo)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{banco_nome}_{timestamp}.sql"
        caminho_completo = os.path.join(destino_dir, nome_arquivo)
        
        # Comando mysqldump para XAMPP
        comando = [
            mysqldump_path,
            "-h", "localhost",
            "-u", "root",
            "--skip-comments",
            "--complete-insert",
            "--single-transaction",
            banco_nome
        ]
        
        # Executar e capturar output
        with open(caminho_completo, 'w', encoding='utf-8') as arquivo:
            resultado = subprocess.run(
                comando,
                stdout=arquivo,
                stderr=subprocess.PIPE,
                text=True
            )
        
        if resultado.returncode == 0:
            # Compactar o arquivo para economizar espaço
            caminho_zip = caminho_completo.replace('.sql', '.zip')
            with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(caminho_completo, nome_arquivo)
            
            # Remover arquivo SQL original
            os.remove(caminho_completo)
            
            tamanho_mb = os.path.getsize(caminho_zip) / (1024 * 1024)
            
            # Registrar no log
            registrar_log_backup(banco_nome, nome_arquivo.replace('.sql', '.zip'), 
                               tipo, tamanho_mb)
            
            return {
                "sucesso": True,
                "arquivo": caminho_zip,
                "tamanho_mb": round(tamanho_mb, 2),
                "mensagem": f"✅ Backup de '{banco_nome}' criado com sucesso!"
            }
        else:
            # Se mysqldump falhar, verificar erro
            erro_msg = resultado.stderr.lower()
            
            # Verificar se é problema de senha
            if "using password" in erro_msg or "access denied" in erro_msg:
                # Tentar novamente sem especificar senha
                comando_sem_pass = comando.copy()
                
                with open(caminho_completo, 'w', encoding='utf-8') as arquivo:
                    resultado = subprocess.run(
                        comando_sem_pass,
                        stdout=arquivo,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                
                if resultado.returncode == 0:
                    # Compactar...
                    caminho_zip = caminho_completo.replace('.sql', '.zip')
                    with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(caminho_completo, nome_arquivo)
                    
                    os.remove(caminho_completo)
                    tamanho_mb = os.path.getsize(caminho_zip) / (1024 * 1024)
                    
                    registrar_log_backup(banco_nome, nome_arquivo.replace('.sql', '.zip'), 
                                       tipo, tamanho_mb)
                    
                    return {
                        "sucesso": True,
                        "arquivo": caminho_zip,
                        "tamanho_mb": round(tamanho_mb, 2),
                        "mensagem": f"✅ Backup de '{banco_nome}' criado com sucesso!"
                    }
            
            # Se ainda falhar, usar método Python
            st.warning(f"⚠️ mysqldump falhou: {erro_msg[:100]}... usando método Python")
            return executar_backup_python(banco_nome, destino_dir, tipo)
            
    except FileNotFoundError:
        # Se não encontrar mysqldump, usar método Python
        return executar_backup_python(banco_nome, destino_dir, tipo)
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"❌ Erro inesperado: {e}"
        }

def executar_restore(arquivo_backup, banco_destino):
    """Restaura um banco a partir de um arquivo de backup"""
    try:
        # Verificar se estamos em modo alternativo
        if hasattr(st.session_state, 'usar_modo_alternativo') and st.session_state.usar_modo_alternativo:
            # Usar método Python para restore
            return executar_restore_python(arquivo_backup, banco_destino)
        
        # Encontrar caminho do mysql no XAMPP
        mysql_path = encontrar_caminho_xampp("mysql")
        
        # Verificar se o executável existe
        if mysql_path in ["mysql", "mysqldump"]:
            try:
                resultado = subprocess.run([mysql_path, "--version"], 
                                         capture_output=True, 
                                         text=True,
                                         timeout=3)
                if resultado.returncode != 0:
                    # Usar método Python
                    return executar_restore_python(arquivo_backup, banco_destino)
            except:
                # Usar método Python
                return executar_restore_python(arquivo_backup, banco_destino)
        
        # Extrair arquivo ZIP se necessário
        if arquivo_backup.endswith('.zip'):
            with zipfile.ZipFile(arquivo_backup, 'r') as zipf:
                # Extrair o arquivo SQL
                sql_files = [f for f in zipf.namelist() if f.endswith('.sql')]
                if not sql_files:
                    return {"sucesso": False, "mensagem": "❌ Nenhum arquivo SQL no ZIP"}
                
                arquivo_sql = sql_files[0]
                zipf.extract(arquivo_sql, os.path.dirname(arquivo_backup))
                caminho_sql = os.path.join(os.path.dirname(arquivo_backup), arquivo_sql)
        else:
            caminho_sql = arquivo_backup
        
        # Verificar se banco existe, se não, criar
        import mysql.connector
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""  # XAMPP geralmente não tem senha
        )
        cursor = conexao.cursor()
        
        # Criar banco se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{banco_destino}`")
        
        # Comando mysql para restaurar
        comando = [
            mysql_path,
            "-h", "localhost",
            "-u", "root",
            banco_destino
        ]
        
        with open(caminho_sql, 'r', encoding='utf-8') as arquivo:
            resultado = subprocess.run(
                comando,
                stdin=arquivo,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Limpar arquivo SQL temporário
        if arquivo_backup.endswith('.zip'):
            os.remove(caminho_sql)
        
        cursor.close()
        conexao.close()
        
        if resultado.returncode == 0:
            return {
                "sucesso": True,
                "mensagem": f"✅ Banco '{banco_destino}' restaurado com sucesso!"
            }
        else:
            # Tentar sem especificar senha
            comando_sem_pass = [c for c in comando if c != "-p" and not c.startswith("--password")]
            
            with open(caminho_sql, 'r', encoding='utf-8') as arquivo:
                resultado = subprocess.run(
                    comando_sem_pass,
                    stdin=arquivo,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if resultado.returncode == 0:
                return {
                    "sucesso": True,
                    "mensagem": f"✅ Banco '{banco_destino}' restaurado com sucesso!"
                }
            else:
                # Usar método Python como fallback
                return executar_restore_python(arquivo_backup, banco_destino)
            
    except Exception as e:
        # Usar método Python como fallback
        return executar_restore_python(arquivo_backup, banco_destino)

def executar_restore_python(arquivo_backup, banco_destino):
    """Restaura banco usando apenas Python (sem mysql command)"""
    try:
        import mysql.connector
        
        # Extrair arquivo ZIP se necessário
        if arquivo_backup.endswith('.zip'):
            with zipfile.ZipFile(arquivo_backup, 'r') as zipf:
                sql_files = [f for f in zipf.namelist() if f.endswith('.sql')]
                if not sql_files:
                    return {"sucesso": False, "mensagem": "❌ Nenhum arquivo SQL no ZIP"}
                
                arquivo_sql = sql_files[0]
                zipf.extract(arquivo_sql, os.path.dirname(arquivo_backup))
                caminho_sql = os.path.join(os.path.dirname(arquivo_backup), arquivo_sql)
        else:
            caminho_sql = arquivo_backup
        
        # Ler conteúdo do arquivo SQL
        with open(caminho_sql, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Conectar ao MySQL
        conexao = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexao.cursor()
        
        # Criar banco se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{banco_destino}`")
        cursor.execute(f"USE `{banco_destino}`")
        
        # Executar comandos SQL em lotes
        commands = sql_content.split(';')
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, cmd in enumerate(commands):
            cmd = cmd.strip()
            if cmd:
                try:
                    cursor.execute(cmd)
                except mysql.connector.Error as err:
                    # Ignorar alguns erros comuns
                    if "already exists" not in str(err).lower():
                        st.warning(f"Aviso no comando {i+1}: {err}")
            
            # Atualizar progresso
            if i % 10 == 0:
                progress = (i + 1) / len(commands)
                progress_bar.progress(progress)
                status_text.text(f"Executando comando {i+1}/{len(commands)}")
        
        progress_bar.progress(1.0)
        status_text.empty()
        
        conexao.commit()
        
        # Limpar arquivo temporário
        if arquivo_backup.endswith('.zip'):
            os.remove(caminho_sql)
        
        cursor.close()
        conexao.close()
        
        return {
            "sucesso": True,
            "mensagem": f"✅ Banco '{banco_destino}' restaurado com sucesso (método Python)!"
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"❌ Erro no restore Python: {e}"
        }

def registrar_log_backup(banco, arquivo, tipo, tamanho_mb):
    """Registra backup em arquivo de log"""
    log_path = os.path.join(BACKUP_DIR, "backup_log.csv")
    log_entry = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "banco": banco,
        "arquivo": arquivo,
        "tipo": tipo,
        "tamanho_mb": tamanho_mb
    }
    
    # Criar ou atualizar log
    if os.path.exists(log_path):
        df_log = pd.read_csv(log_path)
        df_log = pd.concat([df_log, pd.DataFrame([log_entry])], ignore_index=True)
    else:
        df_log = pd.DataFrame([log_entry])
    
    df_log.to_csv(log_path, index=False)

def listar_backups_disponiveis():
    """Lista todos os backups disponíveis"""
    backups = []
    
    for root, dirs, files in os.walk(BACKUP_DIR):
        for file in files:
            if file.endswith(('.sql', '.zip')):
                caminho = os.path.join(root, file)
                tamanho_mb = os.path.getsize(caminho) / (1024 * 1024)
                data_criacao = datetime.fromtimestamp(os.path.getctime(caminho))
                
                backups.append({
                    "nome": file,
                    "caminho": caminho,
                    "tamanho_mb": round(tamanho_mb, 2),
                    "data": data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
                    "tipo": "automático" if "automaticos" in caminho else "manual"
                })
    
    return sorted(backups, key=lambda x: x["data"], reverse=True)

def backup_todos_bancos():
    """Realiza backup de todos os bancos de uma vez"""
    bancos = listar_bancos()
    resultados = []
    
    if not bancos:
        return {"sucesso": False, "mensagem": "❌ Nenhum banco encontrado para backup"}
    
    progresso = st.progress(0)
    status_text = st.empty()
    
    for i, banco in enumerate(bancos):
        status_text.text(f"Backup do banco: {banco} ({i+1}/{len(bancos)})")
        resultado = executar_backup(banco, AUTO_BACKUP_DIR, "automático")
        resultados.append((banco, resultado["sucesso"]))
        progresso.progress((i + 1) / len(bancos))
    
    status_text.empty()
    
    sucessos = sum(1 for _, sucesso in resultados if sucesso)
    return {
        "sucesso": sucessos == len(bancos),
        "mensagem": f"✅ {sucessos}/{len(bancos)} bancos backupados com sucesso!",
        "detalhes": resultados
    }

# ============ INTERFACE STREAMLIT ============
def main():
    st.title("💾 Sistema de Backup & Restauração - XAMPP")
    
    # FORÇAR MODO PYTHON (adicione estas 2 linhas)
    st.session_state.usar_modo_alternativo = True
    # Inicializar session state se não existir
    if 'usar_modo_alternativo' not in st.session_state:
        st.session_state.usar_modo_alternativo = False
    if 'caminho_xampp' not in st.session_state:
        st.session_state.caminho_xampp = "C:\\xampp"
    
    # Seção de configuração do XAMPP
    with st.sidebar.expander("⚙️ Configuração XAMPP", expanded=True):
        st.info("Configure o caminho do seu XAMPP")
        
        caminho_xampp = st.text_input(
            "Caminho do XAMPP:",
            value=st.session_state.caminho_xampp,
            help="Exemplo: C:\\xampp ou /opt/lampp"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Detectar", use_container_width=True):
                # Tentar detectar XAMPP
                caminhos_teste = [
                    "C:\\xampp",
                    "D:\\xampp",
                    "/opt/lampp",
                    "/Applications/XAMPP"
                ]
                
                detectado = False
                for caminho in caminhos_teste:
                    mysql_bin = os.path.join(caminho, "mysql", "bin")
                    if os.path.exists(mysql_bin):
                        st.session_state.caminho_xampp = caminho
                        st.success(f"✅ XAMPP detectado em: {caminho}")
                        detectado = True
                        st.rerun()
                        break
                
                if not detectado:
                    st.error("❌ XAMPP não detectado automaticamente")
        
        with col2:
            if st.button("✅ Salvar", use_container_width=True):
                st.session_state.caminho_xampp = caminho_xampp
                st.success("Configurações salvas!")
                st.rerun()
        
        senha_mysql = st.text_input(
            "Senha do MySQL (se houver):",
            type="password",
            help="Deixe vazio se não tiver senha (padrão XAMPP)"
        )
    
    # Verificar dependências
    with st.expander("🔧 Status do Sistema", expanded=True):
        problemas = verificar_dependencias()
        
        if problemas:
            st.error("⚠️ **Aviso:** Algumas ferramentas não foram encontradas!")
            
            for problema in problemas:
                st.write(f"❌ **{problema}**")
            
            st.markdown("""
            ### Para XAMPP no Windows:
            
            1. **Caminho padrão:** `C:\\xampp\\mysql\\bin\\`
            2. **Solução:** O sistema usará automaticamente métodos alternativos em Python
            
            ### Modo de operação atual:
            - ✅ **Backups:** Funcionam com método Python
            - ✅ **Restauração:** Funcionam com método Python
            - ⚠️ **Performance:** Pode ser mais lento para bancos grandes
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Verificar novamente", use_container_width=True):
                    st.rerun()
            
            with col2:
                if not st.session_state.usar_modo_alternativo:
                    if st.button("🚀 Ativar modo Python", use_container_width=True):
                        st.session_state.usar_modo_alternativo = True
                        st.success("Modo Python ativado!")
                        st.rerun()
                else:
                    st.success("✅ Modo Python já está ativo")
            
            st.info("💡 **Dica:** Se quiser usar mysqldump, adicione `C:\\xampp\\mysql\\bin` ao PATH do Windows e reinicie o aplicativo.")
        else:
            st.success("✅ Todas ferramentas encontradas!")
            st.info("O sistema pode usar tanto mysqldump quanto métodos Python.")
            
            if st.session_state.usar_modo_alternativo:
                if st.button("🔙 Voltar para modo normal", use_container_width=True):
                    st.session_state.usar_modo_alternativo = False
                    st.success("Modo normal ativado!")
                    st.rerun()
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Backup Individual", 
        "🚀 Backup Completo", 
        "🔄 Restaurar", 
        "📊 Histórico"
    ])
    
    with tab1:
        st.subheader("Backup de Banco Individual")
        
        bancos = listar_bancos()
        if bancos:
            banco_selecionado = st.selectbox(
                "Selecione o banco para backup:",
                bancos,
                key=backup_key("backup_select")
            )
            
            nome_personalizado = st.text_input(
                "Nome personalizado (opcional):",
                placeholder="meu_backup_importante",
                help="Deixe em branco para usar nome automático"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Criar Backup", use_container_width=True):
                        # Container para feedback
                        feedback_container = st.empty()
                        feedback_container.info("🔄 Iniciando backup...")
                        
                        with st.spinner(f"Criando backup de '{banco_selecionado}'..."):
                            resultado = executar_backup(
                                banco_selecionado, 
                                MANUAL_BACKUP_DIR,
                                "manual"
                            )
                        
                        feedback_container.empty()  # Limpa a mensagem
                        
                        if resultado["sucesso"]:
                            st.success(resultado["mensagem"])
                            st.toast("✅ Backup criado com sucesso!", icon="✅")
                            
                            # Mostrar detalhes em um expander
                            with st.expander("📋 Detalhes do Backup"):
                                st.info(f"📁 Arquivo: {os.path.basename(resultado['arquivo'])}")
                                st.info(f"📏 Tamanho: {resultado['tamanho_mb']} MB")
                                st.info(f"📍 Local: {os.path.dirname(resultado['arquivo'])}")
                                
                                # Botão para download
                                with open(resultado['arquivo'], "rb") as f:
                                    st.download_button(
                                        label="⬇️ Baixar Backup Agora",
                                        data=f,
                                        file_name=os.path.basename(resultado['arquivo']),
                                        mime="application/zip",
                                        use_container_width=True
                                    )
                        else:
                            st.error(resultado["mensagem"])
                            st.toast("❌ Erro no backup", icon="❌")
            
            with col2:
                if st.button("📥 Ver Backups Criados ", use_container_width=True):
                    backups = listar_backups_disponiveis()
                    backups_banco = [b for b in backups if banco_selecionado in b["nome"]]
                    
                    if backups_banco:
                        st.subheader(f"Backups de '{banco_selecionado}':")
                        
                        # Criar selectbox para escolher backup
                        opcoes = [f"{b['nome']} ({b['data']})" for b in backups_banco]
                        selecao = st.selectbox("Escolha um backup:", opcoes)
                        
                        if selecao:
                            idx = opcoes.index(selecao)
                            backup = backups_banco[idx]
                            
                            # Botão de download
                            with open(backup['caminho'], "rb") as f:
                                st.download_button(
                                    label=f"⬇️ Baixar {backup['nome']}",
                                    data=f,
                                    file_name=backup["nome"],
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            
                            # Informações
                            st.info(f"**Tamanho:** {backup['tamanho_mb']} MB")
                            st.info(f"**Data:** {backup['data']}")
                            st.info(f"**Tipo:** {backup['tipo']}")
                    else:
                        st.warning("Nenhum backup encontrado para este banco.")
        else:
            st.info("📭 Nenhum banco de dados encontrado.")
            st.info("Verifique se o MySQL do XAMPP está rodando.")
    
    with tab2:
        st.subheader("Backup de Todos os Bancos")
        st.warning("⚠️ Esta operação pode demorar dependendo do tamanho dos bancos.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Backup Total Agora", use_container_width=True, key=generate_unique_id("btn_backup_total")):
                resultado = backup_todos_bancos()
                if resultado["sucesso"]:
                    st.success(resultado["mensagem"])
                else:
                    st.error(resultado["mensagem"])
                
                # Mostrar detalhes
                with st.expander("Ver detalhes"):
                    for banco, sucesso in resultado.get("detalhes", []):
                        status = "✅" if sucesso else "❌"
                        st.write(f"{status} {banco}")
        
        with col2:
            # Agendamento simples
            st.markdown("#### ⏰ Agendamento")
            intervalo = st.selectbox(
                "Backup automático a cada:",
                ["Desativado", "Diariamente", "Semanalmente", "Mensalmente"],
                key=backup_key("agendamento")
            )
            
            if intervalo != "Desativado":
                st.info(f"Backups automáticos serão executados {intervalo.lower()}")
                st.caption("Os backups automáticos são salvos em backups/automaticos/")
    
    with tab3:
        st.subheader("Restaurar Banco de Dados")
        
        # Listar backups disponíveis
        backups = listar_backups_disponiveis()
        
        if backups:
            # Criar lista para selectbox
            opcoes_backup = [
                f"{b['nome']} ({b['tipo']}, {b['data']}, {b['tamanho_mb']}MB)" 
                for b in backups
            ]
            
            backup_selecionado_idx = st.selectbox(
                "Selecione o backup para restaurar:",
                range(len(opcoes_backup)),
                format_func=lambda x: opcoes_backup[x],
                key=backup_key("restore_select")
            )
            
            backup_info = backups[backup_selecionado_idx]
            
            # Nome do banco de destino
            nome_arquivo = backup_info["nome"]
            if "_" in nome_arquivo:
                nome_base = nome_arquivo.split("_")[0]
            else:
                nome_base = nome_arquivo.split(".")[0]
            
            banco_destino = st.text_input(
                "Nome do banco de destino:",
                value=nome_base,
                help="Pode ser um novo nome ou substituir um banco existente"
            )
            
            st.warning(f"⚠️ **Atenção:** O banco '{banco_destino}' será criado/substituído!")
            
            if st.button("🔄 Restaurar Banco", type="primary", use_container_width=True, key=generate_unique_id("btn_restaurar")):
                with st.spinner(f"Restaurando banco '{banco_destino}'..."):
                    resultado = executar_restore(backup_info["caminho"], banco_destino)
                    
                    if resultado["sucesso"]:
                        st.success(resultado["mensagem"])
                        st.balloons()
                    else:
                        st.error(resultado["mensagem"])
        else:
            st.info("📭 Nenhum backup disponível para restauração.")
            
        # Upload de arquivo externo
        st.markdown("---")
        st.subheader("📤 Restaurar de Arquivo Externo")
        
        arquivo_upload = st.file_uploader(
            "Carregue seu arquivo .sql ou .zip:",
            type=["sql", "zip"]
        )
        
        if arquivo_upload:
            # Salvar arquivo temporariamente
            temp_dir = "temp_upload"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, arquivo_upload.name)
            
            with open(temp_path, "wb") as f:
                f.write(arquivo_upload.getbuffer())
            
            nome_restore = st.text_input(
                "Nome para o banco restaurado:",
                value=arquivo_upload.name.split(".")[0]
            )
            
            if st.button("🔄 Restaurar do Upload", use_container_width=True, key=generate_unique_id("btn_restaurar_upload")):
                with st.spinner("Restaurando..."):
                    resultado = executar_restore(temp_path, nome_restore)
                    
                    if resultado["sucesso"]:
                        st.success(resultado["mensagem"])
                        # Limpar arquivo temporário
                        os.remove(temp_path)
                    else:
                        st.error(resultado["mensagem"])
    
    with tab4:
        st.subheader("Histórico de Backups")
        
        backups = listar_backups_disponiveis()
        
        if backups:
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Backups", len(backups))
            with col2:
                tamanho_total = sum(b["tamanho_mb"] for b in backups)
                st.metric("Espaço Total", f"{round(tamanho_total, 1)} MB")
            with col3:
                manuais = sum(1 for b in backups if b["tipo"] == "manual")
                st.metric("Backups Manuais", manuais)
            
            # Tabela de backups
            df_backups = pd.DataFrame(backups)
            st.dataframe(
                df_backups[["nome", "tipo", "tamanho_mb", "data"]],
                use_container_width=True,
                column_config={
                    "nome": "Arquivo",
                    "tipo": "Tipo",
                    "tamanho_mb": st.column_config.NumberColumn(
                        "Tamanho (MB)",
                        format="%.2f MB"
                    ),
                    "data": "Data"
                }
            )
            
            # Opção para limpar backups antigos
            with st.expander("🗑️ Gerenciar Espaço"):
                st.warning("Excluir backups antigos libera espaço em disco.")
                
                dias = st.slider("Excluir backups com mais de (dias):", 1, 365, 30)
                
                if st.button("Limpar Backups Antigos", type="secondary", key=generate_unique_id("btn_limpar_backups")):
                    # Implementar lógica de limpeza
                    st.info(f"Esta funcionalidade excluiria backups com mais de {dias} dias")
        else:
            st.info("📭 Nenhum backup registrado ainda.")
    
    # Rodapé
    st.markdown("---")
    st.caption(f"📁 Backups salvos em: `{os.path.abspath(BACKUP_DIR)}`")
    st.caption(f"🔧 Modo: {'Python' if st.session_state.usar_modo_alternativo else 'Normal'}")

if __name__ == "__main__":
    main()