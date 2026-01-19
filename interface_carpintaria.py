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
# 🚀 NOVAS FERRAMENTAS (AGORA COM LOCALIZAÇÃO)
# ==========================================

@tool
def obter_localizacao() -> str:
    """
    Identifica a localização atual do usuário (Cidade, Região, País) baseada no IP da internet.
    Use isso se o usuário perguntar 'onde estou' ou pedir informações locais.
    """
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        cidade = data.get("city", "Desconhecida")
        pais = data.get("country", "Desconhecido")
        return f"Localização Atual detectada: {cidade}, {pais}"
    except Exception as e:
        return f"Não foi possível obter a localização: {str(e)}"

@tool
def scraper_web(url: str) -> str:
    """
    Entra em um site e copia o texto principal.
    Args:
        url: O endereço do site (http://...).
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
    Pesquisa no DuckDuckGo para informações em tempo real.
    Args:
        termo: O que você quer pesquisar.
    """
    if not BUSCA_DISPONIVEL: return "Erro: Modulo de busca ausente."
    try:
        # Tenta usar o DDGS diretamente
        results = DDGS().text(termo, max_results=3)
        return str(results) if results else "Nada encontrado."
    except Exception as e:
        return f"Erro na busca: {str(e)}"

@tool
def analisar_dados_csv(caminho_arquivo: str) -> str:
    """
    Lê um arquivo CSV/Excel e retorna estatísticas.
    Args:
        caminho_arquivo: O caminho do arquivo.
    """
    try:
        if caminho_arquivo.endswith('.csv'): df = pd.read_csv(caminho_arquivo)
        elif caminho_arquivo.endswith('.xlsx'): df = pd.read_excel(caminho_arquivo)
        else: return "Formato inválido."
        return f"Colunas: {list(df.columns)}\nEstatísticas:\n{df.describe().to_string()}"
    except Exception as e: return f"Erro: {str(e)}"

# ==========================================
# ⚙️ CONFIGURAÇÕES (SIDEBAR)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=50)
    st.markdown("### Painel de Controle")
    
    with st.expander("🧠 Configuração do Cérebro", expanded=True):
        opcoes_modelos = {}
        
        # Google (Gemini 2.5 e Pro)
        opcoes_modelos["☁️ Gemini 2.5 Flash (Rápido)"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
        opcoes_modelos["☁️ Gemini 2.5 Pro (Potente)"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
        
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

    with st.expander("🧰 Status das Ferramentas", expanded=False):
        st.caption("✅ Localização (IP)")
        st.caption("✅ Busca Web")
        st.caption("✅ Leitura de Docs")
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

if prompt := st.chat_input("Ex: Onde eu estou? Qual o preço da madeira hoje?"):
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

            # LISTA DE FERRAMENTAS COM LOCALIZAÇÃO
            tools_list = [consultar_documentos, salvar_arquivo, ler_arquivo, analisar_dados_csv, scraper_web, obter_localizacao]
            if BUSCA_DISPONIVEL: tools_list.append(buscar_na_web)

            agent = CodeAgent(
                tools=tools_list, model=modelo, add_base_tools=True,
                additional_authorized_imports=['datetime', 'numpy', 'pandas', 'matplotlib', 'plt', 'requests', 'bs4', 'json', 'os']
            )

            # INSTRUÇÃO PARA USAR A LOCALIZAÇÃO SE NECESSÁRIO
            prompt_contexto = f"USUÁRIO: {prompt}\n\nNota: Se o usuário perguntar sobre localização ou 'aqui', use a ferramenta 'obter_localizacao'."
            
            response = agent.run(prompt_contexto)
            
            status.update(label="✅ Feito", state="complete")
            placeholder.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})
            
            if os.path.exists("chart.png"): st.image("chart.png")

        except Exception as e:
            status.update(label="❌ Erro", state="error")
            st.error(f"Erro: {e}")
