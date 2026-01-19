import streamlit as st
import os
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from smolagents import CodeAgent, LiteLLMModel, tool

# --- 1. CONFIGURAÇÃO VISUAL PROFISSIONAL ---
st.set_page_config(
    page_title="Carpintaria OS", 
    page_icon="🛠️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stChatInput {border-radius: 20px;}
    .block-container {padding-top: 2rem;}
    h1 {color: #2e4053;}
</style>
""", unsafe_allow_html=True)

st.title("🛠️ Carpintaria OS: Enterprise AI")
st.markdown("---")

# --- VERIFICAÇÕES DE SISTEMA ---
try:
    import ollama
    ollama.list()
    OLLAMA_AVAILABLE = True
except:
    OLLAMA_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError:
    BUSCA_DISPONIVEL = False

# --- IMPORTAÇÃO DE FERRAMENTAS EXISTENTES ---
from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# ==========================================
# 🚀 FERRAMENTAS
# ==========================================

@tool
def obter_localizacao() -> str:
    """
    Identifica a localização atual (Cidade, País) via IP.
    """
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return f"Localização: {data.get('city')}, {data.get('country')}"
    except Exception as e:
        return f"Erro localizacao: {str(e)}"

@tool
def scraper_web(url: str) -> str:
    """
    Lê o texto de um site.
    Args:
        url: O endereço do site.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text()[:4000]
    except Exception as e:
        return f"Erro ao ler site: {str(e)}"

@tool
def buscar_na_web(termo: str) -> str:
    """
    Pesquisa no DuckDuckGo.
    Args:
        termo: O que pesquisar.
    """
    if not BUSCA_DISPONIVEL: return "Erro: Modulo de busca ausente."
    try:
        results = DDGS().text(termo, max_results=3)
        return str(results) if results else "Nada encontrado."
    except Exception as e:
        return f"Erro na busca: {str(e)}"

@tool
def analisar_dados_csv(caminho_arquivo: str) -> str:
    """
    Lê CSV/Excel e retorna estatísticas.
    Args:
        caminho_arquivo: Caminho do arquivo.
    """
    try:
        if caminho_arquivo.endswith('.csv'): df = pd.read_csv(caminho_arquivo)
        elif caminho_arquivo.endswith('.xlsx'): df = pd.read_excel(caminho_arquivo)
        else: return "Formato inválido."
        return f"Colunas: {list(df.columns)}\nEstatísticas:\n{df.describe().to_string()}"
    except Exception as e: return f"Erro: {str(e)}"

# ==========================================
# ⚙️ CONFIGURAÇÕES
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=50)
    st.markdown("### Painel de Controle")
    
    with st.expander("🧠 Configuração do Cérebro", expanded=True):
        opcoes_modelos = {}
        
        # Google
        opcoes_modelos["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
        opcoes_modelos["☁️ Gemini 2.5 Pro"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
        
        # Groq
        opcoes_modelos["🚀 Groq Llama 3.3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
        
        # OpenRouter
        opcoes_modelos["🌐 OpenRouter (DeepSeek)"] = ("openrouter/deepseek/deepseek-r1:free", "OPENROUTER_API_KEY")

        if OLLAMA_AVAILABLE:
            opcoes_modelos["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)
            opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)

        nome_escolhido = st.selectbox("Modelo:", list(opcoes_modelos.keys()))
        model_id, api_env_var = opcoes_modelos[nome_escolhido]

        criatividade = st.slider("Criatividade", 0.0, 1.0, 0.2, 0.1)

    with st.expander("🧰 Ferramentas Ativas", expanded=False):
        st.caption("✅ Geolocalização")
        st.caption("✅ Web Scraping")
        st.caption("✅ Análise de Dados")

    if st.button("🗑️ Nova Conversa", type="primary"):
        st.session_state["messages"] = []
        st.rerun()

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Digite sua solicitação..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        status = st.status("🧠 Pensando...", expanded=False)

        try:
            api_key = os.environ.get(api_env_var) if api_env_var else None
            base_url = "http://localhost:11434" if "ollama" in model_id else None

            modelo = LiteLLMModel(
                model_id=model_id, api_key=api_key, api_base=base_url,
                max_tokens=4000, temperature=criatividade
            )

            tools_list = [consultar_documentos, salvar_arquivo, ler_arquivo, analisar_dados_csv, scraper_web, obter_localizacao]
            if BUSCA_DISPONIVEL: tools_list.append(buscar_na_web)

            # --- CORREÇÃO AQUI ---
            # Removemos 'plt' da lista abaixo
            agent = CodeAgent(
                tools=tools_list, model=modelo, add_base_tools=True,
                additional_authorized_imports=['datetime', 'numpy', 'pandas', 'matplotlib', 'requests', 'bs4', 'json', 'os']
            )

            prompt_contexto = f"USUÁRIO: {prompt}\n\nNota: Se perguntarem sobre localização, use 'obter_localizacao'."
            
            response = agent.run(prompt_contexto)
            
            status.update(label="✅ Feito", state="complete")
            placeholder.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})
            
            if os.path.exists("chart.png"): st.image("chart.png")

        except Exception as e:
            status.update(label="❌ Erro", state="error")
            st.error(f"Erro: {e}")
