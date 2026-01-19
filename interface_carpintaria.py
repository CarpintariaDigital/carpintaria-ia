import streamlit as st
import os
from smolagents import CodeAgent, LiteLLMModel, tool

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Carpintaria Digital Pro", page_icon="🪚", layout="wide")
st.title("🪚 Carpintaria Digital Pro (Versão Híbrida 2.5)")

# --- IMPORTAÇÃO SEGURA DO OLLAMA (OFFLINE) ---
try:
    import ollama
    # Testa conexão rápida
    ollama.list()
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

# --- IMPORTAÇÃO SEGURA DA BUSCA (ONLINE) ---
try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError:
    BUSCA_DISPONIVEL = False

from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# --- FERRAMENTA DE BUSCA BLINDADA (Não quebra sem net) ---
@tool
def buscar_na_web(termo: str) -> str:
    """
    Pesquisa na internet (DuckDuckGo). Use para preços, câmbio e notícias.
    Requer conexão ativa.
    """
    if not BUSCA_DISPONIVEL:
        return "Erro: Biblioteca de busca não instalada."
    
    try:
        # Tenta conectar. Se estiver sem net, vai cair no except
        results = DDGS().text(termo, max_results=3)
        if not results:
            return "Nenhum resultado encontrado."
        
        resposta = f"Resultados para '{termo}':\n"
        for i, r in enumerate(results):
            resposta += f"{i+1}. {r['title']}: {r['body']} (Link: {r['href']})\n"
        return resposta
    except Exception as e:
        # Retorna erro amigável em vez de quebrar o app
        return f"⚠️ Falha na busca (Sem internet ou erro): {str(e)}"

# --- 2. BARRA LATERAL (MENU) ---
with st.sidebar:
    st.header("🧠 Cérebro da IA")
    
    opcoes_modelos = {}

    # --- GOOGLE GEMINI (Nomes Corrigidos da sua Lista) ---
    st.caption("☁️ Google (Requer Internet)")
    # Note que no LiteLLM usamos o prefixo 'gemini/' e o nome que achamos na lista
    opcoes_modelos["Google: Gemini 2.5 Flash (Novo!)"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
    opcoes_modelos["Google: Gemini 2.5 Pro (Potente)"] = ("gemini/gemini-2.5-pro", "GEMINI_API_KEY")
    opcoes_modelos["Google: Gemini 2.0 Flash Lite (Rápido)"] = ("gemini/gemini-2.0-flash-lite", "GEMINI_API_KEY")

    # --- GROQ ---
    st.caption("☁️ Groq (Grátis)")
    opcoes_modelos["Groq: Llama 3.3 (Versátil)"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")

    # --- OPENROUTER ---
    st.caption("☁️ OpenRouter")
    opcoes_modelos["OpenRouter: DeepSeek R1 (Free)"] = ("openrouter/deepseek/deepseek-r1:free", "OPENROUTER_API_KEY")
    opcoes_modelos["OpenRouter: Mistral 7B (Free)"] = ("openrouter/mistralai/mistral-7b-instruct:free", "OPENROUTER_API_KEY")

    st.divider()

    # --- LOCAL (OLLAMA) ---
    if OLLAMA_AVAILABLE:
        st.success("🟢 Modo Local (Offline) Ativo")
        # Adiciona modelos locais no topo da lista se quiser prioridade
        opcoes_locais = {
            "🏠 Local: Qwen 2.5 Coder": ("ollama/qwen2.5-coder:3b", None),
            "🏠 Local: Llama 3.2": ("ollama/llama3.2:latest", None),
            "🏠 Local: Phi 3.5": ("ollama/phi3.5:latest", None)
        }
        # Junta os dicionários
        opcoes_modelos = {**opcoes_locais, **opcoes_modelos}
    else:
        st.error("🔴 Modo Local Indisponível (Rode 'ollama serve')")

    # Seleção
    nome_escolhido = st.selectbox("Escolha o Cérebro:", list(opcoes_modelos.keys()))
    model_id, api_env_var = opcoes_modelos[nome_escolhido]

    modo_agente = st.toggle("🕵️ Agente (Docs + Web)", value=True)

    if st.button("🗑️ Limpar Conversa"):
        st.session_state["messages"] = []
        st.rerun()

# --- 3. LÓGICA DO CHAT ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte algo..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status = st.status(f"⚙️ Processando com {nome_escolhido}...", expanded=True)

        try:
            # 1. Configura Chave API (Só se não for Local)
            api_key = None
            if api_env_var: 
                api_key = os.environ.get(api_env_var)
                if not api_key:
                    status.update(label="❌ Sem Chave", state="error")
                    st.error(f"Falta a chave {api_env_var} nos Secrets ou Variáveis de Ambiente!")
                    st.stop()
            
            # 2. Configura URL Local (Só se for Ollama)
            base_url = "http://localhost:11434" if "ollama" in model_id else None
            
            modelo_agente = LiteLLMModel(
                model_id=model_id,
                api_key=api_key, 
                api_base=base_url,
                max_tokens=4000
            )

            if modo_agente:
                minhas_ferramentas = [consultar_documentos, salvar_arquivo, ler_arquivo]
                
                # Só usa a busca se a biblioteca existir
                if BUSCA_DISPONIVEL:
                    minhas_ferramentas.append(buscar_na_web)

                agent = CodeAgent(
                    tools=minhas_ferramentas, 
                    model=modelo_agente, 
                    add_base_tools=True,
                    additional_authorized_imports=['datetime', 'numpy', 'pandas', 'os', 'json', 'duckduckgo_search']
                )
                
                # INSTRUÇÕES BLINDADAS
                aviso_offline = ""
                if "Local" in nome_escolhido:
                    aviso_offline = "VOCÊ ESTÁ EM MODO LOCAL. Se a ferramenta 'buscar_na_web' falhar por falta de internet, ignore e responda com seu conhecimento interno."

                prompt_sistema = f"""
                SOLICITAÇÃO: {prompt}
                DIRETRIZES:
                1. Priorize 'consultar_documentos' para perguntas da empresa.
                2. Use 'buscar_na_web' para dados externos atuais.
                {aviso_offline}
                3. Responda sempre em Português.
                """
                
                resposta_final = agent.run(prompt_sistema)
            else:
                agent = CodeAgent(tools=[], model=modelo_agente, add_base_tools=False)
                resposta_final = agent.run(prompt)

            status.update(label="✅ Pronto!", state="complete", expanded=False)
            message_placeholder.markdown(resposta_final)
            st.session_state["messages"].append({"role": "assistant", "content": resposta_final})

        except Exception as e:
            status.update(label="❌ Erro", state="error")
            st.error(f"Erro técnico: {str(e)}")
            if "Local" in nome_escolhido:
                st.info("💡 Se você estiver offline, verifique se rodou 'ollama serve' no terminal.")
