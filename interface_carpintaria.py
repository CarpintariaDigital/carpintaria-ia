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

# Estilo CSS para deixar mais 'Enterprise'
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
# 🚀 NOVAS FERRAMENTAS (ADAPTADAS DO SEU PEDIDO)
# ==========================================

@tool
def scraper_web(url: str) -> str:
    """
    Entra em um site e copia o texto principal. Ótimo para ler notícias ou documentação técnica.
    
    Args:
        url: O endereço do site (começando com http:// ou https://).
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts e estilos para limpar o texto
        for script in soup(["script", "style"]):
            script.extract()
            
        texto = soup.get_text()
        # Limpa espaços em branco excessivos
        lines = (line.strip() for line in texto.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        texto_limpo = '\n'.join(chunk for chunk in chunks if chunk)
        
        return texto_limpo[:4000] + "..." # Limita para não estourar a memória
    except Exception as e:
        return f"Erro ao acessar o site: {str(e)}"

@tool
def buscar_na_web(termo: str) -> str:
    """
    Pesquisa no DuckDuckGo para informações em tempo real (Preços, Notícias).
    Args:
        termo: O que você quer pesquisar.
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
    Lê um arquivo CSV, Excel ou JSON e retorna estatísticas básicas (média, contagem, colunas).
    
    Args:
        caminho_arquivo: O caminho do arquivo (ex: 'vendas.csv').
    """
    try:
        if caminho_arquivo.endswith('.csv'):
            df = pd.read_csv(caminho_arquivo)
        elif caminho_arquivo.endswith('.xlsx'):
            df = pd.read_excel(caminho_arquivo)
        else:
            return "Formato não suportado. Use CSV ou Excel."
            
        resumo = df.describe().to_string()
        info_colunas = str(df.columns.tolist())
        return f"Colunas: {info_colunas}\n\nEstatísticas:\n{resumo}"
    except Exception as e:
        return f"Erro ao analisar dados: {str(e)}"

# Nota: O CodeAgent JÁ sabe criar gráficos com matplotlib nativamente,
# não precisamos criar uma ferramenta específica para isso, basta pedir no chat!

# ==========================================
# ⚙️ CONFIGURAÇÕES (SIDEBAR PROFISSIONAL)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040946.png", width=50)
    st.markdown("### Painel de Controle")
    
    # MENU EXPANSÍVEL (Cleaner UI)
    with st.expander("🧠 Configuração do Cérebro", expanded=True):
        
        # 1. ESCOLHA DO MODELO
        opcoes_modelos = {}
        
        # Google
        opcoes_modelos["☁️ Gemini 2.5 Flash (Rápido)"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
        opcoes_modelos["☁️ Gemini 2.5 Pro (Potente)"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
        
        # Groq
        opcoes_modelos["🚀 Groq Llama 3.3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
        
        # OpenRouter
        opcoes_modelos["🌐 OpenRouter (DeepSeek)"] = ("openrouter/deepseek/deepseek-r1:free", "OPENROUTER_API_KEY")

        # Local
        if OLLAMA_AVAILABLE:
            opcoes_modelos["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)
            opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)

        nome_escolhido = st.selectbox("Modelo Ativo:", list(opcoes_modelos.keys()))
        model_id, api_env_var = opcoes_modelos[nome_escolhido]

        # 2. TEMPERATURA (CRIATIVIDADE)
        criatividade = st.slider(
            "Nível de Criatividade (Temperatura)", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.2, 
            step=0.1,
            help="0.0 = Preciso e Robótico | 1.0 = Criativo e Imprevisível"
        )

    # MENU DE FERRAMENTAS
    with st.expander("🧰 Ferramentas Habilitadas", expanded=False):
        st.checkbox("Acesso à Internet (Busca + Scraping)", value=True, disabled=True)
        st.checkbox("Sistema de Arquivos (Ler/Escrever)", value=True, disabled=True)
        st.checkbox("Análise de Dados (Pandas/CSV)", value=True, disabled=True)
        st.checkbox("Leitura de Documentos (RAG)", value=True, disabled=True)

    if st.button("🗑️ Nova Conversa", type="primary"):
        st.session_state["messages"] = []
        st.rerun()

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ex: Pesquise o preço do MDF ou analise o arquivo vendas.csv..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        status_container = st.status("🧠 Pensando...", expanded=False)

        try:
            # Configuração de Chaves
            api_key = os.environ.get(api_env_var) if api_env_var else None
            base_url = "http://localhost:11434" if "ollama" in model_id else None

            # MODELO COM TEMPERATURA AJUSTÁVEL
            modelo = LiteLLMModel(
                model_id=model_id,
                api_key=api_key,
                api_base=base_url,
                max_tokens=4000,
                temperature=criatividade # <--- AQUI ENTRA A SUA CONFIGURAÇÃO
            )

            # LISTA DE FERRAMENTAS COMPLETAS
            tools_list = [
                consultar_documentos, 
                salvar_arquivo, 
                ler_arquivo, 
                analisar_dados_csv, # Nova Ferramenta Analista
                scraper_web         # Nova Ferramenta Scraper
            ]
            
            if BUSCA_DISPONIVEL:
                tools_list.append(buscar_na_web)

            # AGENTE
            agent = CodeAgent(
                tools=tools_list,
                model=modelo,
                add_base_tools=True,
                # Autoriza bibliotecas de análise e gráficos
                additional_authorized_imports=[
                    'datetime', 'numpy', 'pandas', 'matplotlib', 'plt', 
                    'requests', 'bs4', 'json', 'os'
                ]
            )

            response = agent.run(f"USUÁRIO: {prompt}\n(Responda em Português)")
            
            status_container.update(label="✅ Concluído", state="complete")
            placeholder.markdown(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})

            # Se a IA gerou gráfico, ele salva como arquivo. Vamos tentar mostrar.
            if os.path.exists("chart.png"): # Exemplo se ela salvar chart.png
                 st.image("chart.png")

        except Exception as e:
            status_container.update(label="❌ Erro", state="error")
            st.error(f"Erro no processamento: {e}")
