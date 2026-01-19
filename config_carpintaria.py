# config_carpintaria.py
import os
import requests
import streamlit as st

class CerebroHibrido:
    def __init__(self):
        self.tem_internet = self._checar_conexao()
        # Se rodar no Streamlit Cloud, assume que é ONLINE sempre
        self.is_cloud = os.getenv("STREAMLIT_SHARING") is not None
        
        if self.is_cloud:
            self.modo = "CLOUD (Apenas APIs) ☁️"
        else:
            self.modo = "ONLINE ☁️" if self.tem_internet else "OFFLINE (Local) 🏠"

    def _checar_conexao(self):
        try:
            requests.get("https://8.8.8.8", timeout=1)
            return True
        except:
            return False

    def obter_config_modelo(self, preferencia_usuario: str):
        """
        Prioridade de escolha:
        1. Se Offline -> Ollama
        2. Se Online:
           - Tenta Groq (Rápido)
           - Tenta Gemini (Janela Longa)
           - Tenta OpenRouter (Vários modelos)
           - Fallback para Ollama se não tiver chaves
        """
        
        # --- MODO OFFLINE ---
        if not self.tem_internet and not self.is_cloud:
            return self._config_ollama(preferencia_usuario)

        # --- MODO ONLINE (Checando Chaves) ---
        
        # 1. Opção Groq (Llama 3 70B - Rápido)
        if "GROQ_API_KEY" in st.secrets:
            return {
                "model_id": "groq/llama-3.3-70b-versatile",
                "api_base": None,
                "api_key": st.secrets["GROQ_API_KEY"]
            }
            
        # 2. Opção Google Gemini (Bom contexto)
        elif "GEMINI_API_KEY" in st.secrets:
            return {
                "model_id": "gemini/gemini-1.5-flash",
                "api_base": None,
                "api_key": st.secrets["GEMINI_API_KEY"]
            }

        # 3. Opção OpenRouter (DeepSeek, Claude, GPT)
        elif "OPENROUTER_API_KEY" in st.secrets:
            return {
                # Você pode mudar para 'openrouter/anthropic/claude-3-haiku' por exemplo
                "model_id": "openrouter/google/gemini-2.0-flash-001", 
                "api_base": None,
                "api_key": st.secrets["OPENROUTER_API_KEY"]
            }

        # Sem chaves? Volta para o Local (se não estiver na nuvem)
        if not self.is_cloud:
            st.warning("⚠️ Internet ok, mas sem chaves de API (Groq/Gemini). Usando Ollama.")
            return self._config_ollama(preferencia_usuario)
        else:
            st.error("❌ Erro: No Streamlit Cloud você PRECISA de chaves de API (Groq/Gemini) nos Secrets.")
            st.stop()

    def _config_ollama(self, modelo):
        return {
            "model_id": f"ollama/{modelo}",
            "api_base": "http://localhost:11434",
            "api_key": "ollama"
        }
