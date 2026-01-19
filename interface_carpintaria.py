import streamlit as st
import os
from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool

# --- BLOCO DE IMPORTAÇÃO SEGURA (Ollama) ---
try:
    import ollama
    # Tenta listar modelos só para ver se o servidor responde
    ollama.list()
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

# --- IMPORTS DOS NOSSOS MÓDULOS ---
from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# Inicializa ferramenta de busca na internet
ferramenta_busca = DuckDuckGoSearchTool()

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Carpintaria Digital Pro", page_icon="🪚", layout="wide")
st.title("🪚 Carpintaria Digital Pro")

# --- 2. PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("🧠 Cérebro da IA")
    
    # --- MENU DE ESCOLHA DE MODELOS ---
    # Estrutura: "Nome no Menu": ("provedor/modelo", "nome_da_variavel_api")
    
    opcoes_modelos = {
        # 1. GROQ (Melhor opção Gratuita e Rápida)
        "🚀 Groq: Llama 3.3 (Recomendado)": ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY"),
        
        # 2. GOOGLE (Correção do nome do modelo)
        "☁️ Google: Gemini 1.5 Flash": ("gemini/gemini-1.5-flash", "GEMINI_API_KEY"),
        
        # 3. OPENROUTER (Apenas modelos explicitamente 'free')
        "🆓 OpenRouter: Google Gemini 2.0 (Free)": ("openrouter/google/gemini-2.0-flash-exp:free", "OPENROUTER_API_KEY"),
        "🆓 OpenRouter: Llama 3 8B (Free)": ("openrouter/meta-llama/llama-3-8b-instruct:free", "OPENROUTER_API_KEY"),
    }

    # Se o Ollama estiver rodando (Local), adiciona as opções locais
    if OLLAMA_AVAILABLE:
        opcoes_modelos["🏠 Local: Qwen 2.5 Coder"] = ("ollama/qwen2.5-coder:3b", None)
        opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)
        st.success("🟢 Modo Local Ativo")
    
    # O Menu Dropdown
    nome_escolhido = st.selectbox("Escolha o Modelo:", list(opcoes_modelos.keys()))
    
    # Pega as configurações baseadas na escolha
    model_id, api_env_var = opcoes_modelos[nome_escolhido]

    st.divider()
    
    modo_agente = st.toggle("🕵️ Ativar Agente (Busca + Docs)", value=True)
    st.caption("Ferramentas: Internet, PDFs, Arquivos")

    if st.button("🗑️ Limpar Memória"):
        st.session_state["messages"] = []
        st.rerun()

# --- 3. HISTÓRICO ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. LÓGICA PRINCIPAL ---
if prompt := st.chat_input("Pergunte sobre madeira, preços ou documentos..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status = st.status(f"⚙️ Conectando ao {nome_escolhido}...", expanded=True)

        try:
            # --- PREPARAÇÃO DAS CHAVES API ---
            api_key = None
            if api_env_var: # Se for modelo de nuvem
                api_key = os.environ.get(api_env_var)
                if not api_key:
                    status.update(label="❌ Erro de Chave", state="error")
                    st.error(f"Falta a chave {api_env_var} nos Secrets do Streamlit!")
                    st.stop()
            
            # --- CONFIGURAÇÃO DO MODELO ---
            # Define URL base se for Ollama
            base_url = "http://localhost:11434" if "ollama" in model_id else None
            
            modelo_agente = LiteLLMModel(
                model_id=model_id,
                api_key=api_key, 
                api_base=base_url,
                max_tokens=4000,
                temperature=0.2
            )

            # --- MODO AGENTE OU CHAT ---
            if modo_agente:
                # Agente com ferramentas (Internet + Docs)
                agent = CodeAgent(
                    tools=[consultar_documentos, salvar_arquivo, ler_arquivo, ferramenta_busca], 
                    model=modelo_agente, 
                    add_base_tools=True,
                    additional_authorized_imports=['datetime', 'numpy', 'pandas', 'os', 'json']
                )
                
                prompt_sistema = f"""
                SOLICITAÇÃO: {prompt}
                DIRETRIZES:
                1. Use 'duckduckgo_search' para coisas atuais (preços, câmbio, notícias).
                2. Use 'consultar_documentos' para dados internos da empresa.
                3. Responda sempre em Português.
                """
                resposta_final = agent.run(prompt_sistema)
            else:
                # Agente simples (Conversa rápida)
                agent = CodeAgent(tools=[], model=modelo_agente, add_base_tools=False)
                resposta_final = agent.run(prompt)

            status.update(label="✅ Concluído!", state="complete", expanded=False)
            message_placeholder.markdown(resposta_final)
            st.session_state["messages"].append({"role": "assistant", "content": resposta_final})

        except Exception as e:
            status.update(label="❌ Erro", state="error")
            erro_msg = str(e)
            
            # Tratamento de erros amigável
            if "404" in erro_msg and "gemini" in erro_msg.lower():
                st.error("Erro do Google: Modelo não encontrado. Tente selecionar o Groq.")
            elif "402" in erro_msg or "credits" in erro_msg.lower():
                st.error("Erro do OpenRouter: Conta sem créditos. Use o Groq ou Gemini (Google Direto).")
            else:
                st.error(f"Ocorreu um erro técnico: {erro_msg}")
