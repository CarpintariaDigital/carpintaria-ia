import streamlit as st
import ollama
from smolagents import CodeAgent, LiteLLMModel

# --- IMPORTS DOS NOSSOS MÓDULOS NOVOS ---
from config_carpintaria import CerebroHibrido
from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Carpintaria Digital Pro", page_icon="🪚", layout="wide")
st.title("🪚 Carpintaria Digital Pro")

# Inicializa o Cérebro
cerebro = CerebroHibrido()

# --- 2. PAINEL DE CONTROLE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    
    # Mostra status da conexão
    if cerebro.tem_internet:
        st.success(f"Sinal: {cerebro.modo}")
    else:
        st.warning(f"Sinal: {cerebro.modo}")

    st.subheader("🧠 Modelo Base (Local)")
    modelo_local = st.selectbox(
        "Preferência Offline:", 
        ["qwen2.5-coder:3b", "llama3.2:latest", "phi3.5:latest"]
    )
    
    st.divider()
    modo_agente = st.toggle("🕵️ Ativar Modo Agente (Full Stack)", value=True)
    
    st.info("Ferramentas Ativas:\n- 📚 RAG (Documentos)\n- 💾 Salvar Arquivos\n- 📖 Ler Arquivos")

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
if prompt := st.chat_input("Qual a tarefa de hoje?"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Define qual configuração usar (Nuvem ou Local automaticamente)
        config_llm = cerebro.obter_config_modelo(modelo_local)
        
        # --- MODO AGENTE (COM FERRAMENTAS E ACESSO AO DISCO) ---
        if modo_agente:
            status = st.status(f"🕵️ Agente processando com {config_llm['model_id']}...", expanded=True)
            try:
                # Configura o modelo dinamicamente
                modelo_agente = LiteLLMModel(
                    model_id=config_llm['model_id'],
                    api_base=config_llm['api_base'],
                    api_key=config_llm['api_key'],
                    max_tokens=4000,
                    temperature=0.2
                )

                # Inicializa Agente com NOVAS FERRAMENTAS
                agent = CodeAgent(
                    tools=[consultar_documentos, salvar_arquivo, ler_arquivo], 
                    model=modelo_agente, 
                    add_base_tools=True,
                    additional_authorized_imports=['datetime', 'numpy', 'pandas', 'os', 'json']
                )

                # Prompt Reforçado para usar ferramentas
                prompt_sistema = f"""
                SOLICITAÇÃO: {prompt}
                
                DIRETRIZES:
                1. Se precisar de informação da empresa, USE 'consultar_documentos'.
                2. Se precisar criar código, NÃO apenas mostre na tela. USE 'salvar_arquivo' para criar o arquivo real.
                3. Responda sempre em Português.
                """

                resposta_final = agent.run(prompt_sistema)

                status.update(label="✅ Tarefa Concluída!", state="complete", expanded=False)
                message_placeholder.markdown(resposta_final)
                st.session_state["messages"].append({"role": "assistant", "content": resposta_final})

            except Exception as e:
                status.update(label="❌ Erro", state="error")
                st.error(f"Erro no Agente: {e}")
                # Fallback: Se o agente falhar (ex: erro de internet na nuvem), tenta local
                st.warning("Tentando fallback para chat simples local...")

        # --- MODO CHAT SIMPLES (FALLBACK OU CONVERSA RÁPIDA) ---
        else:
            full_response = ""
            # No modo simples, forçamos o local Ollama para ser rápido
            for chunk in ollama.chat(model=modelo_local, messages=st.session_state["messages"], stream=True):
                if 'message' in chunk and 'content' in chunk['message']:
                    full_response += chunk['message']['content']
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
