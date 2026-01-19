import streamlit as st
import os
import pandas as pd
import requests
import json
import base64
import io
import time
from datetime import datetime
from smolagents import CodeAgent, LiteLLMModel, tool

# ==========================================
# 🔧 CONFIGURAÇÕES DO SISTEMA HÍBRIDO
# ==========================================
# Sim, esta estrutura suporta OFF-LINE (Local) e ON-LINE (Nuvem)
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError:
    BUSCA_DISPONIVEL = False

try:
    import ollama
    # Teste rápido de conexão local
    ollama.list()
    OLLAMA_AVAILABLE = True
except:
    OLLAMA_AVAILABLE = False

# ==========================================
# 💾 BANCO DE DADOS (JSON)
# ==========================================
DB_FILES = {
    "projetos": "db_projetos.json",
    "clientes": "db_clientes.json",
    "financas": "db_financas.json",
    "eventos": "db_eventos.json"
}

def carregar_dados(tipo):
    arquivo = DB_FILES.get(tipo)
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f: return pd.read_json(f)
    return pd.DataFrame() # Retorna vazio se não existir

def salvar_dados(tipo, df):
    arquivo = DB_FILES.get(tipo)
    df.to_json(arquivo, orient="records", date_format="iso")

# ==========================================
# 🎨 UI & UX PROFISSIONAL (GLASSMORPHISM)
# ==========================================
st.set_page_config(page_title="Carpintaria OS", page_icon="🪚", layout="wide", initial_sidebar_state="collapsed")

# CSS AVANÇADO
st.markdown("""
<style>
    /* RESET & FUNDO */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(242, 246, 252) 0%, rgb(227, 235, 245) 90%);
        font-family: 'Inter', sans-serif;
    }
    header[data-testid="stHeader"] {background: transparent;}

    /* GLASSMORPHISM (Efeito Vidro) */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: transform 0.2s;
    }
    .glass-card:hover { transform: translateY(-5px); }

    /* BOTÕES MODERNOS */
    div.stButton > button {
        background: #1e293b;
        color: white;
        border-radius: 12px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover {
        background: #334155;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* SIDEBAR PROFISSIONAL */
    section[data-testid="stSidebar"] {
        background-color: #0f172a; /* Azul muito escuro */
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: white !important;
    }
    section[data-testid="stSidebar"] span {
        color: #cbd5e1 !important;
    }

    /* LOGO FIX */
    .logo-container {
        display: flex; justify-content: center; align-items: center;
        background: white; border-radius: 12px; padding: 10px;
        width: 100px; height: 100px; margin: 0 auto 15px auto;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# URL DO LOGO (Substitua pelo seu link se tiver, senão usa ícone padrão)
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2040/2040946.png"

# ==========================================
# 🧠 LÓGICA DE NAVEGAÇÃO
# ==========================================
if "page" not in st.session_state: st.session_state["page"] = "entrada"
if "auth" not in st.session_state: st.session_state["auth"] = False
if "messages" not in st.session_state: st.session_state["messages"] = []

def navegar(destino):
    st.session_state["page"] = destino
    st.rerun()

# ==========================================
# 🚪 PÁGINA 1: ENTRADA (LANDING PAGE)
# ==========================================
if st.session_state["page"] == "entrada":
    
    # Layout Centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo com container branco para garantir visibilidade
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="logo-container">
                <img src="{LOGO_URL}" style="width: 80px; height: 80px; object-fit: contain;">
            </div>
            <h1 style="color:#1e293b; font-size: 3rem; margin-bottom: 0;">Carpintaria Digital</h1>
            <p style="color:#64748b; font-size: 1.2rem; letter-spacing: 1px;">SISTEMA OPERACIONAL INTEGRADO</p>
        </div>
        <br>
        """, unsafe_allow_html=True)

    # Cards de Acesso (Glassmorphism)
    c_left, c_spacer, c_right = st.columns([1, 0.2, 1])
    
    with c_left:
        st.markdown("""
        <div class="glass-card" style="text-align:center; height: 250px;">
            <h2 style="font-size:3rem;">🛒</h2>
            <h3 style="color:#1e293b;">Dumbanengue</h3>
            <p style="color:#64748b;">Vitrine Pública de Apps e Produtos</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("") # Espaço
        if st.button("Acessar Vitrine ➔", use_container_width=True):
            navegar("dumbanengue")

    with c_right:
        st.markdown("""
        <div class="glass-card" style="text-align:center; height: 250px;">
            <h2 style="font-size:3rem;">💼</h2>
            <h3 style="color:#1e293b;">Escritório</h3>
            <p style="color:#64748b;">Gestão, Finanças e Inteligência Artificial</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("") # Espaço
        if st.button("Entrar no Escritório 🔒", use_container_width=True):
            navegar("login")

# ==========================================
# 🛒 PÁGINA 2: DUMBANENGUE (VITRINE)
# ==========================================
elif st.session_state["page"] == "dumbanengue":
    if st.button("⬅ Voltar", key="btn_voltar"): navegar("entrada")
    
    st.markdown("<h1 style='text-align:center; color:#1e293b;'>🛒 Dumbanengue Digital</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#64748b;'>Soluções e Aplicativos prontos para uso.</p><br>", unsafe_allow_html=True)
    
    apps = [
        {"nome": "Gestão de Estoque", "desc": "Controle total de madeira.", "icon": "📦"},
        {"nome": "Catálogo Visual", "desc": "Vitrine para clientes.", "icon": "📖"},
        {"nome": "Calculadora", "desc": "Orçamentos rápidos.", "icon": "🧮"},
    ]
    
    cols = st.columns(3)
    for idx, app in enumerate(apps):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:2rem;">{app['icon']}</div>
                <h4>{app['nome']}</h4>
                <p style="font-size:0.9rem; color:#64748b;">{app['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.button(f"Abrir {app['nome']}", key=f"app_{idx}", use_container_width=True)

# ==========================================
# 🔒 PÁGINA 3: LOGIN
# ==========================================
elif st.session_state["page"] == "login":
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <h2>🔒 Acesso Restrito</h2>
            <p>Insira a chave da Carpintaria</p>
        </div>
        <br>
        """, unsafe_allow_html=True)
        
        senha = st.text_input("Senha", type="password")
        
        c_entrar, c_voltar = st.columns(2)
        if c_entrar.button("Entrar", use_container_width=True):
            senha_real = st.secrets.get("APP_PASSWORD", "admin") # Senha padrão se não configurar secrets
            if senha == senha_real:
                st.session_state["auth"] = True
                navegar("escritorio")
            else:
                st.error("Senha incorreta.")
                
        if c_voltar.button("Cancelar", use_container_width=True):
            navegar("entrada")

# ==========================================
# 💼 PÁGINA 4: ESCRITÓRIO (O CORE)
# ==========================================
elif st.session_state["page"] == "escritorio":
    if not st.session_state["auth"]: navegar("entrada")

    # --- SIDEBAR RESTAURADA (CONFIGURAÇÕES IA & MENU) ---
    with st.sidebar:
        # Logo na Sidebar (com fundo branco para destacar)
        st.markdown(f"""
        <div style="background:white; padding:10px; border-radius:10px; text-align:center; margin-bottom:20px;">
            <img src="{LOGO_URL}" width="60">
            <h3 style="color:#0f172a; margin:5px 0 0 0;">Carpintaria</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("Navegação")
        modulo = st.radio("Selecione:", [
            "📊 Dashboard", 
            "🧠 Cérebro IA", # IA AQUI
            "🎟️ Eventos QR", 
            "📂 Projetos", 
            "💰 Financeiro"
        ])
        
        st.markdown("---")
        
        # --- CONFIGURAÇÃO DA IA (VOLTOU!) ---
        if modulo == "🧠 Cérebro IA":
            with st.expander("⚙️ Configuração da IA", expanded=True):
                st.info("Status: Híbrido (Local/Nuvem)")
                
                opcoes_modelos = {}
                # Opções Nuvem
                opcoes_modelos["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
                opcoes_modelos["🚀 Groq Llama 3.3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
                
                # Opções Locais (Offline)
                if OLLAMA_AVAILABLE:
                    opcoes_modelos["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)
                    opcoes_modelos["🏠 Local: Llama 3.2"] = ("ollama/llama3.2:latest", None)
                
                nome_modelo = st.selectbox("Modelo Ativo:", list(opcoes_modelos.keys()))
                st.session_state["modelo_atual"] = opcoes_modelos[nome_modelo]
                
                temp = st.slider("Criatividade:", 0.0, 1.0, 0.3)
                
                if st.button("🗑️ Limpar Chat"):
                    st.session_state["messages"] = []
                    st.rerun()

        st.markdown("---")
        if st.button("Sair / Logout"):
            st.session_state["auth"] = False
            navegar("entrada")

    # --- ÁREA DE CONTEÚDO PRINCIPAL ---
    
    # 1. IA CHAT (Com Tools)
    if modulo == "🧠 Cérebro IA":
        st.title("🧠 Escritório de Inteligência")
        st.caption(f"Conectado a: {nome_modelo}")
        
        # Histórico
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
        if prompt := st.chat_input("Digite sua ordem..."):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                placeholder = st.empty()
                status = st.status("⚙️ Processando...", expanded=False)
                try:
                    # Recupera configs
                    model_id, api_env_var = st.session_state["modelo_atual"]
                    api_key = st.secrets.get(api_env_var) if api_env_var else None
                    base_url = "http://localhost:11434" if "ollama" in model_id else None
                    
                    # Inicializa Modelo
                    modelo = LiteLLMModel(
                        model_id=model_id, api_key=api_key, api_base=base_url,
                        max_tokens=4000, temperature=temp
                    )
                    
                    # Inicializa Agente (Com Tools)
                    agent = CodeAgent(
                        tools=[], # Adicione ferramentas aqui se necessário
                        model=modelo, add_base_tools=True
                    )
                    
                    res = agent.run(prompt)
                    status.update(label="Concluído", state="complete")
                    placeholder.markdown(res)
                    st.session_state["messages"].append({"role": "assistant", "content": res})
                    
                except Exception as e:
                    status.update(label="Erro", state="error")
                    st.error(f"Falha técnica: {e}")

    # 2. EVENTOS (QR Code)
    elif modulo == "🎟️ Eventos QR":
        st.title("🎟️ Gestor de Tickets")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            nome_ev = st.text_input("Nome do Evento")
            participante = st.text_input("Nome do Participante")
            tipo = st.selectbox("Tipo", ["VIP", "Normal", "Staff", "Corporativo"])
            
            if st.button("Gerar QR Code", use_container_width=True):
                if QR_AVAILABLE and participante:
                    dados = f"{nome_ev}|{participante}|{tipo}|{datetime.now()}"
                    img = qrcode.make(dados)
                    # Exibe
                    buf = io.BytesIO()
                    img.save(buf)
                    byte_im = buf.getvalue()
                    st.session_state["last_qr"] = byte_im
                else:
                    st.error("Biblioteca QR ausente ou dados incompletos.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            if "last_qr" in st.session_state:
                st.image(st.session_state["last_qr"], caption="QR Code Gerado", width=250)
                st.success("Pronto para impressão!")

    # 3. DASHBOARD
    elif modulo == "📊 Dashboard":
        st.title("Visão Geral")
        c1, c2, c3 = st.columns(3)
        c1.metric("Projetos Ativos", "12")
        c2.metric("Receita Mensal", "MT 145.000")
        c3.metric("Tickets Gerados", "85")
        
        st.markdown("### Atividade Recente")
        st.dataframe(pd.DataFrame({
            "Atividade": ["Novo Cliente", "Pagamento Recebido", "Ticket Criado"],
            "Horário": ["10:00", "11:30", "14:15"],
            "Status": ["✅", "✅", "✅"]
        }), use_container_width=True)

    # 4. FINANCEIRO (Exemplo Notion Style)
    elif modulo == "💰 Financeiro":
        st.title("💰 Gestão Financeira")
        df = carregar_dados("financas")
        # Se vazio cria estrutura
        if df.empty: df = pd.DataFrame(columns=["Data", "Descricao", "Valor", "Tipo"])
        
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar Dados"):
            salvar_dados("financas", edited)
            st.success("Salvo!")

    # 5. PROJETOS
    elif modulo == "📂 Projetos":
        st.title("📂 Projetos em Curso")
        st.info("Módulo de gestão de tarefas e prazos.")
        # Adicione lógica similar ao financeiro aqui