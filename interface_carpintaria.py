import streamlit as st
import os
from smolagents import CodeAgent, LiteLLMModel, DuckDuckGoSearchTool

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Carpintaria Digital Pro", page_icon="🪚", layout="wide")
st.title("🪚 Carpintaria Digital Pro")

# --- BLOCO DE IMPORTAÇÃO SEGURA (Ollama) ---
try:
    import ollama
    ollama.list()
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

# --- BLOCO DE IMPORTAÇÃO SEGURA (Ferramentas) ---
from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# Tenta carregar a Busca. Se falhar (por falta de biblioteca), o app continua vivo.
try:
    ferramenta_busca = DuckDuckGoSearchTool()
    BUSCA_ATIVA = True
except Exception as e:
    print(f"Aviso: Busca na internet desativada. Erro: {e}")
    ferramenta_busca = None
    BUSCA_ATIVA = False

# --- 2. PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("🧠 Cérebro da IA")
    
    # Menu de Modelos (Mantive o que ajustamos antes)
    opcoes_modelos = {
        "🚀 Groq: Llama 3.3 (Recomendado)": ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY"),
        "☁️ Google: Gemini 1.5 Flash": ("gemini/gemini-1.5-flash", "GEMINI_API_KEY"),
        "☁️ Google: Gemini Pro (Backup)": ("gemini/gemini-pro", "GEMINI_API_KEY"),
    }

    if OLLAMA_AVAILABLE:
        opcoes_modelos["🏠 Local: Qwen 2.5 Coder"] = ("ollama/qwen2.5-coder:3b", None)
        opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)
    
    nome_escolhido = st.selectbox("Escolha o Modelo:", list(opcoes_modelos.keys()))
    model_id, api_env_var = opcoes_modelos[nome_escolhido]

    st.divider()
    
    modo_agente = st.toggle("🕵️ Ativar Agente Inteligente", value=True)
    
    # Mostra status das ferramentas
    if modo_agente:
        st.caption("Ferramentas Ativas:")
        st.caption("✅ Leitura de PDFs")
        st.caption("✅ Salvar Arquivos")
        if BUSCA_ATIVA:
            st.caption("✅ Internet (DuckDuckGo)")
        else:
            st.caption("❌ Internet (Instalando...)")

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
if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status = st.status(f"⚙️ Conectando ao {nome_escolhido}...", expanded=True)

        try:
            # Configura Chaves
            api_key = None
            if api_env_var:
                api_key = os.environ.get(api_env_var)
                if not api_key:
                    status.update(label="❌ Erro de Chave", state="error")
                    st.error(f"Falta a chave {api_env_var} nos Secrets!")
                    st.stop()
            
            # Configura Modelo
            base_url = "http://localhost:11434" if "ollama" in model_id else None
            modelo_agente = LiteLLMModel(
                model_id=model_id,
                api_key=api_key, 
                api_base=base_url,
                max_tokens=4000
            )

            if modo_agente:
                # --- LISTA DINÂMICA DE FERRAMENTAS ---
                # Só adiciona a busca se ela carregou com sucesso
                minhas_ferramentas = [consultar_documentos, salvar_arquivo, ler_arquivo]
                
                texto_instrucoes = """
                SOLICITAÇÃO: {prompt}
                DIRETRIZES:
                1. Use 'consultar_documentos' para dados internos.
                """
                
                if BUSCA_ATIVA:
                    minhas_ferramentas.append(ferramenta_busca)
                    texto_instrucoes += "\n2. Use 'duckduckgo_search' para preços e notícias atuais."
                else:
                    texto_instrucoes += "\n(Aviso: Busca na internet indisponível temporariamente)."
                
                texto_instrucoes += "\n3. Responda em Português."

                agent = CodeAgent(
                    tools=minhas_ferramentas, 
                    model=modelo_agente, 
                    add_base_tools=True,
                    additional_authorized_imports=['datetime', 'numpy', 'pandas', 'os', 'json']
                )
                
                resposta_final = agent.run(texto_instrucoes.format(prompt=prompt))
            else:
                agent = CodeAgent(tools=[], model=modelo_agente, add_base_tools=False)
                resposta_final = agent.run(prompt)

            status.update(label="✅ Concluído!", state="complete", expanded=False)
            message_placeholder.markdown(resposta_final)
            st.session_state["messages"].append({"role": "assistant", "content": resposta_final})

        except Exception as e:
            status.update(label="❌ Erro", state="error")
            st.error(f"Erro: {str(e)}")
