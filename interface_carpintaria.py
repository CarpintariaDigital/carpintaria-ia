import streamlit as st
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from smolagents import CodeAgent, LiteLLMModel, tool

# --- 1. CONFIGURAÇÃO PWA & VISUAL ---
st.set_page_config(
    page_title="Carpintaria OS", 
    page_icon="🛠️", 
    layout="wide",
    initial_sidebar_state="collapsed" # Começa fechado para parecer app mobile
)

# CSS HACK PARA PARECER UM APP (Remove cabeçalhos padrão do Streamlit)
st.markdown("""
<style>
    /* Esconde o menu hamburger do Streamlit e rodapé */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Estilo de App Moderno */
    .stApp {
        background-color: #f8f9fa;
    }
    .stChatInput {
        border-radius: 25px !important;
        border: 1px solid #ddd;
    }
    h1 {
        color: #2c3e50;
        font-size: 1.8rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛠️ Carpintaria OS")

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

from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# ==========================================
# 🚀 FERRAMENTAS
# ==========================================

@tool
def scraper_web(url: str) -> str:
    """
    Lê o texto de um site (Notícias, Manuais, Artigos).
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
    Pesquisa no DuckDuckGo. Use para preços e dados atuais.
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
# ⚙️ CONFIGURAÇÕES (SIDEBAR)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=50)
    st.markdown("### Configurações")
    
    # LOCALIZAÇÃO MANUAL (CORREÇÃO DO PROBLEMA DE IP)
    local_usuario = st.text_input("📍 Sua Cidade/País", value="Maputo, Moçambique")
    
    with st.expander("🧠 Cérebro da IA", expanded=False):
        opcoes_modelos = {}
        opcoes_modelos["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
        opcoes_modelos["☁️ Gemini 2.5 Pro"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
        opcoes_modelos["🚀 Groq Llama 3.3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
        opcoes_modelos["🌐 OpenRouter (DeepSeek)"] = ("openrouter/deepseek/deepseek-r1:free", "OPENROUTER_API_KEY")

        if OLLAMA_AVAILABLE:
            opcoes_modelos["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)
            opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)

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

if prompt := st.chat_input("Digite aqui..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        # Status menor e mais discreto para mobile
        status = st.status("⚙️", expanded=False)

        try:
            api_key = os.environ.get(api_env_var) if api_env_var else None
            base_url = "http://localhost:11434" if "ollama" in model_id else None

            modelo = LiteLLMModel(
                model_id=model_id, api_key=api_key, api_base=base_url,
                max_tokens=4000, temperature=criatividade
            )

            tools_list = [consultar_documentos, salvar_arquivo, ler_arquivo, analisar_dados_csv, scraper_web]
            if BUSCA_DISPONIVEL: tools_list.append(buscar_na_web)

            # AGENTE (Sem 'plt' nos imports para não dar erro)
            agent = CodeAgent(
                tools=tools_list, model=modelo, add_base_tools=True,
                additional_authorized_imports=['datetime', 'numpy', 'pandas', 'requests', 'bs4', 'json', 'os']
            )

            # INJETANDO A LOCALIZAÇÃO CORRETA NO CONTEXTO
            prompt_contexto = f"""
            CONTEXTO DO USUÁRIO:
            - Localização Real: {local_usuario}
            - Solicitação: {prompt}
            
            DIRETRIZES:
            - Se precisar buscar preços ou clima, use a localização '{local_usuario}'.
            - Responda de forma direta e profissional.
            """
            
            response = agent.run(prompt_contexto)
            
            status.update(label="✓", state="complete")
            placeholder.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})
            
            if os.path.exists("chart.png"): st.image("chart.png")

        except Exception as e:
            status.update(label="Erro", state="error")
            st.error(f"Erro: {e}")