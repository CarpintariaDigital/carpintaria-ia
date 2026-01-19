import streamlit as st
import os
import pandas as pd
import requests
import json
import base64
from bs4 import BeautifulSoup
from smolagents import CodeAgent, LiteLLMModel, tool

# ==========================================
# 📱 CONFIGURAÇÃO DOS SEUS APPS (VITRINE)
# ==========================================
MEUS_APPS = [
    {
        "nome": "Gestão de Estoque",
        "icone": "📦",
        "desc": "Controle de entrada e saída de madeira.",
        "link": "https://www.google.com" 
    },
    {
        "nome": "Catálogo Digital",
        "icone": "📖",
        "desc": "Vitrine de produtos para clientes.",
        "link": "https://www.google.com"
    },
    {
        "nome": "Orçamentos",
        "icone": "💰",
        "desc": "Calculadora rápida de projetos.",
        "link": "https://www.google.com"
    }
]

# --- 1. CONFIGURAÇÃO VISUAL & PWA ---
st.set_page_config(
    page_title="Carpintaria Digital",
    page_icon="🪚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS CUSTOMIZADO
st.markdown("""
<style>
    header[data-testid="stHeader"] {background-color: transparent;}
    .stApp {background-color: #f4f6f9;}
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        color: white;
    }
    .logo-box {
        background-color: #0f172a;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #334155;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        color: #e2e8f0 !important;
    }
    div[data-testid="stContainer"] {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SISTEMA DE LOGIN ---
def verificar_acesso():
    if "APP_PASSWORD" not in st.secrets: return True
    if "senha_correta" not in st.session_state: st.session_state["senha_correta"] = False
    
    if not st.session_state["senha_correta"]:
        st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            senha = st.text_input("Senha da Carpintaria:", type="password")
            if st.button("Destrancar Porta"):
                if senha == st.secrets["APP_PASSWORD"]:
                    st.session_state["senha_correta"] = True
                    st.rerun()
                else:
                    st.error("Chave incorreta.")
        return False
    return True

if not verificar_acesso(): st.stop()

# --- 3. FERRAMENTAS DA IA (CORRIGIDAS COM ARGS) ---
try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError: BUSCA_DISPONIVEL = False

try:
    import ollama
    ollama.list()
    OLLAMA_AVAILABLE = True
except: OLLAMA_AVAILABLE = False

from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# --- AQUI ESTAVA O ERRO: Adicionada a seção Args: em todas as tools ---

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
    if not BUSCA_DISPONIVEL: return "Erro: Busca indisponível."
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
        return f"Stats:\n{df.describe().to_string()}"
    except Exception as e: return f"Erro: {str(e)}"

# ==========================================
# 🧭 NAVEGAÇÃO E SIDEBAR
# ==========================================
with st.sidebar:
    # LOGO
    st.markdown(f"""
    <div class="logo-box">
        <img src="Carpintaria Digital Logo.png" width="80">
        <h3 style="color:white; margin:0; padding-top:10px;">Carpintaria OS</h3>
    </div>
    """, unsafe_allow_html=True)

    # MENU
    menu_selecionado = st.radio(
        "Navegação:",
        ["🚪 Entrada", "💼 Escritório (IA)", "🛒 Dumbanengue (Apps)"],
        index=1 
    )
    
    st.markdown("---")
    
    # CONFIGURAÇÕES IA
    with st.expander("⚙️ Cérebro & Ajustes", expanded=False):
        local_usuario = st.text_input("📍 Localização", value="Maputo, Moçambique")
        
        opcoes_modelos = {}
        opcoes_modelos["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
        opcoes_modelos["☁️ Gemini 2.5 Pro"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
        opcoes_modelos["🚀 Groq Llama 3.3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
        
        if OLLAMA_AVAILABLE:
            opcoes_modelos["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)

        nome_escolhido = st.selectbox("Modelo IA:", list(opcoes_modelos.keys()))
        model_id, api_env_var = opcoes_modelos[nome_escolhido]
        criatividade = st.slider("Criatividade", 0.0, 1.0, 0.2)

# ==========================================
# 🏠 PÁGINA 1: ENTRADA
# ==========================================
if menu_selecionado == "🚪 Entrada":
    st.title("Bem-vindo à Carpintaria Digital")
    st.markdown("### Painel de Controle")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"📱 **Apps no Dumbanengue**\n\n{len(MEUS_APPS)} Aplicativos Disponíveis")
    with col2:
        st.success("🧠 **Status da IA**\n\nOperacional e Pronta.")
    with col3:
        st.warning(f"📍 **Base**\n\n{local_usuario}")

    st.markdown("---")
    st.markdown("#### Acesso Rápido")
    st.caption("Use o menu lateral para acessar o Chat Inteligente ou a Vitrine de Apps.")

# ==========================================
# 💼 PÁGINA 2: ESCRITÓRIO (IA)
# ==========================================
elif menu_selecionado == "💼 Escritório (IA)":
    st.title("💼 Escritório Central")
    st.caption("Agente Especialista para suporte técnico e estratégico.")

    if "messages" not in st.session_state: st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Digite sua solicitação..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            status = st.status("🧠 Processando...", expanded=False)

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

                prompt_contexto = f"Contexto: Usuário em {local_usuario}. Responda como expert."
                response = agent.run(f"{prompt_contexto}\n\n{prompt}")
                
                status.update(label="✓", state="complete")
                placeholder.markdown(response)
                st.session_state["messages"].append({"role": "assistant", "content": response})
                
                if os.path.exists("chart.png"): st.image("chart.png")

            except Exception as e:
                status.update(label="Erro", state="error")
                st.error(f"Ocorreu um erro: {e}")

# ==========================================
# 🛒 PÁGINA 3: DUMBANENGUE (VITRINE DE APPS)
# ==========================================
elif menu_selecionado == "🛒 Dumbanengue (Apps)":
    st.title("🛒 Dumbanengue Digital")
    st.markdown("### Vitrine de Aplicativos & Ferramentas")
    st.markdown("Acesso direto às soluções da Carpintaria Digital.")
    st.markdown("---")
    
    colunas = st.columns(3)
    
    for index, app in enumerate(MEUS_APPS):
        coluna_atual = colunas[index % 3]
        
        with coluna_atual:
            with st.container(border=True):
                st.markdown(f"## {app['icone']}")
                st.markdown(f"**{app['nome']}**")
                st.caption(app['desc'])
                st.link_button(f"Abrir {app['nome']} ↗", app['link'], use_container_width=True)