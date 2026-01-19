import streamlit as st
import os
import pandas as pd
import requests
import json
import base64
from bs4 import BeautifulSoup
from smolagents import CodeAgent, LiteLLMModel, tool

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Carpintaria Digital", 
    page_icon="🪚", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🔒 SISTEMA DE SEGURANÇA (LOGIN) ---
def verificar_acesso():
    """Bloqueia o app até a senha correta ser inserida."""
    if "APP_PASSWORD" not in st.secrets:
        return True # Se não tiver senha configurada, libera.

    if "senha_correta" not in st.session_state:
        st.session_state["senha_correta"] = False

    if not st.session_state["senha_correta"]:
        st.markdown("## 🔒 Acesso Restrito - Carpintaria Digital")
        senha = st.text_input("Digite a senha de acesso:", type="password")
        if st.button("Entrar"):
            if senha == st.secrets["APP_PASSWORD"]:
                st.session_state["senha_correta"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        return False
    return True

if not verificar_acesso():
    st.stop()

# --- URL DO LOGOTIPO ---
LOGO_URL = "Carpintaria Digital Logo.png" 

# --- CONFIGURAÇÃO PWA (Visual de App) ---
def configurar_pwa():
    manifest = {
        "name": "Carpintaria Digital",
        "short_name": "Carpintaria",
        "description": "OS para Carpintaria.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#2c3e50",
        "theme_color": "#2c3e50",
        "icons": [
            {"src": LOGO_URL, "sizes": "192x192", "type": "image/png"},
            {"src": LOGO_URL, "sizes": "512x512", "type": "image/png"}
        ]
    }
    
    manifest_json = json.dumps(manifest)
    b64_manifest = base64.b64encode(manifest_json.encode()).decode()
    href_manifest = f'data:application/manifest+json;base64,{b64_manifest}'

    st.markdown(f"""
    <link rel="manifest" href="{href_manifest}" />
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stApp {{ background-color: #f8f9fa; }}
        .stChatInput textarea {{ border-radius: 20px; }}
        /* Ajuste para o logo ficar bonito */
        .logo-img {{ border-radius: 10px; margin-bottom: 10px; }}
    </style>
    """, unsafe_allow_html=True)

configurar_pwa()

# --- CABEÇALHO (Usando HTML para evitar erro de servidor) ---
col1, col2 = st.columns([1, 6])
with col1:
    # AQUI ESTAVA O ERRO: Trocamos st.image por HTML direto
    st.markdown(f'<img src="{LOGO_URL}" width="80" class="logo-img">', unsafe_allow_html=True)
with col2:
    st.title("Carpintaria Digital")

# --- VERIFICAÇÕES DE SISTEMA ---
try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError:
    BUSCA_DISPONIVEL = False

try:
    import ollama
    ollama.list() 
    OLLAMA_AVAILABLE = True
except:
    OLLAMA_AVAILABLE = False

from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# ==========================================
# 🚀 FERRAMENTAS
# ==========================================

@tool
def scraper_web(url: str) -> str:
    """
    Lê o conteúdo de texto de um site.
    
    Args:
        url: O endereço URL do site para ler.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for s in soup(["script", "style"]): s.extract()
        return soup.get_text()[:4000]
    except Exception as e: return f"Erro: {str(e)}"

@tool
def buscar_na_web(termo: str) -> str:
    """
    Pesquisa no DuckDuckGo (internet).
    
    Args:
        termo: O texto a ser pesquisado.
    """
    if not BUSCA_DISPONIVEL: return "Erro: Biblioteca de busca ausente."
    try:
        results = DDGS().text(termo, max_results=3)
        return str(results) if results else "Nada encontrado."
    except Exception as e: return f"Erro busca: {str(e)}"

@tool
def analisar_dados_csv(caminho_arquivo: str) -> str:
    """
    Lê CSV/Excel e retorna estatísticas.
    
    Args:
        caminho_arquivo: O caminho para o arquivo.
    """
    try:
        if caminho_arquivo.endswith('.csv'): df = pd.read_csv(caminho_arquivo)
        elif caminho_arquivo.endswith('.xlsx'): df = pd.read_excel(caminho_arquivo)
        else: return "Formato inválido."
        return f"Colunas: {list(df.columns)}\nStats:\n{df.describe().to_string()}"
    except Exception as e: return f"Erro: {str(e)}"

# ==========================================
# ⚙️ SIDEBAR
# ==========================================
with st.sidebar:
    # Logo na sidebar via HTML também
    st.markdown(f'<img src="{LOGO_URL}" width="50" style="margin-bottom:15px">', unsafe_allow_html=True)
    st.markdown("### Configurações")
    
    local_usuario = st.text_input("📍 Localização", value="Maputo, Moçambique")
    
    with st.expander("🧠 Cérebro", expanded=False):
        opcoes_modelos = {}
        opcoes_modelos["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
        opcoes_modelos["☁️ Gemini 2.5 Pro"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
        opcoes_modelos["🚀 Groq Llama 3.3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
        opcoes_modelos["🌐 OpenRouter"] = ("openrouter/deepseek/deepseek-r1:free", "OPENROUTER_API_KEY")

        if OLLAMA_AVAILABLE:
            opcoes_modelos["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)

        nome_escolhido = st.selectbox("Modelo:", list(opcoes_modelos.keys()))
        model_id, api_env_var = opcoes_modelos[nome_escolhido]
        criatividade = st.slider("Criatividade", 0.0, 1.0, 0.2, 0.1)

    if st.button("🗑️ Limpar Chat"):
        st.session_state["messages"] = []
        st.rerun()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        status = st.status("⚙️", expanded=False)

        try:
            api_key = os.environ.get(api_env_var) if api_env_var else None
            if api_env_var and not api_key and api_env_var in st.secrets:
                api_key = st.secrets[api_env_var]

            base_url = "http://localhost:11434" if "ollama" in model_id else None

            modelo = LiteLLMModel(
                model_id=model_id, api_key=api_key, api_base=base_url,
                max_tokens=4000, temperature=criatividade
            )

            tools_list = [consultar_documentos, salvar_arquivo, ler_arquivo, analisar_dados_csv, scraper_web]
            if BUSCA_DISPONIVEL: tools_list.append(buscar_na_web)

            agent = CodeAgent(
                tools=tools_list, model=modelo, add_base_tools=True,
                additional_authorized_imports=['datetime', 'numpy', 'pandas', 'requests', 'bs4', 'json', 'os']
            )

            prompt_contexto = f"Local: {local_usuario}\nPergunta: {prompt}\nInstrução: Seja útil e direto."
            
            response = agent.run(prompt_contexto)
            
            status.update(label="✓", state="complete")
            placeholder.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})
            
            if os.path.exists("chart.png"): st.image("chart.png")

        except Exception as e:
            status.update(label="Erro", state="error")
            st.error(f"Erro: {e}")