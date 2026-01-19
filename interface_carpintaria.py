import streamlit as st
import os
from smolagents import CodeAgent, LiteLLMModel

# --- BLOCO DE IMPORTAÇÃO SEGURA ---
try:
    import ollama
    # Tenta listar modelos só para ver se o servidor responde
    ollama.list()
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

# --- IMPORTS DOS NOSSOS MÓDULOS ---
from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Carpintaria Digital Pro", page_icon="🪚", layout="wide")
st.title("🪚 Carpintaria Digital Pro - Versão Híbrida")

# --- 2. PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("🧠 Cérebro da IA")
    
    # --- MENU DE ESCOLHA DE MODELOS ---
    # Dicionário que liga o "Nome Bonito" ao "ID Técnico"
    # A estrutura é: "Nome no Menu": ("provedor/modelo", "nome_da_variavel_api")
    
    opcoes_modelos = {
    # --- GOOGLE (Free Tier) ---
        "☁️ Google: Gemini 1.5 Flash (Rápido)": ("gemini/gemini-1.5-flash", "GEMINI_API_KEY"),
        "☁️ Google: Gemini Pro (Estável)": ("gemini/gemini-pro", "GEMINI_API_KEY"),
        
        # --- OPENROUTER (DeepSeek & Outros) ---
        "☁️ OpenRouter: DeepSeek R1 (Raciocínio Forte)": ("openrouter/deepseek/deepseek-r1-distill-llama-70b", "OPENROUTER_API_KEY"),
        "☁️ OpenRouter: Mistral Large": ("openrouter/mistralai/mistral-large-2411", "OPENROUTER_API_KEY"),
        
        # --- GROQ ---
        "☁️ Groq: Llama 3.3 (Versátil)": ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY"),
    }

    # Se o Ollama estiver rodando (Local), adiciona as opções locais
    if OLLAMA_AVAILABLE:
        opcoes_modelos["🏠 Local: Qwen 2.5 Coder"] = ("ollama/qwen2.5-coder:3b", None)
        opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)
        opcoes_modelos["🏠 Local: Phi 3.5"] = ("ollama/phi3.5:latest", None)
        st.success("🟢 Modo Local Ativo (Ollama Detectado)")
    else:
        st.info("☁️ Modo Nuvem (Ollama Indisponível)")

    # O Menu Dropdown
    nome_escolhido = st.selectbox("Escolha o Modelo:", list(opcoes_modelos.keys()))
    
    # Pega as configurações baseadas na escolha
    model_id, api_env_var = opcoes_modelos[nome_escolhido]

    st.divider()
    
    modo_agente = st.toggle("🕵️ Ativar Agente (Usa Ferramentas)", value=True)
    st.caption("Ferramentas: RAG (Docs), Salvar Arquivos, Ler Arquivos")

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
if prompt := st.chat_input("Como posso ajudar na carpintaria hoje?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status = st.status(f"⚙️ Processando com {nome_escolhido}...", expanded=True)

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
            modelo_agente = LiteLLMModel(
                model_id=model_id,
                api_key=api_key, # Pode ser None se for Ollama, o LiteLLM entende
                api_base="http://localhost:11434" if "ollama" in model_id else None,
                max_tokens=4000,
                temperature=0.2
            )

            # --- MODO AGENTE OU CHAT ---
            if modo_agente:
                agent = CodeAgent(
                    tools=[consultar_documentos, salvar_arquivo, ler_arquivo], 
                    model=modelo_agente, 
                    add_base_tools=True,
                    additional_authorized_imports=['datetime', 'numpy', 'pandas', 'os', 'json']
                )
                
                prompt_sistema = f"SOLICITAÇÃO: {prompt}\nContexto: Responda em Português."
                resposta_final = agent.run(prompt_sistema)
            else:
                # Modo simples (sem ferramentas, mas usando o mesmo modelo selecionado)
                # Criamos um agente sem ferramentas só para conversar
                agent = CodeAgent(tools=[], model=modelo_agente, add_base_tools=False)
                resposta_final = agent.run(prompt)

            status.update(label="✅ Concluído!", state="complete", expanded=False)
            message_placeholder.markdown(resposta_final)
            st.session_state["messages"].append({"role": "assistant", "content": resposta_final})

        except Exception as e:
            status.update(label="❌ Erro", state="error")
            st.error(f"Ocorreu um erro: {str(e)}")
            st.warning("Dica: Se for erro de 'Connection', verifique se o Ollama está rodando (se for local) ou as chaves API (se for nuvem).")
