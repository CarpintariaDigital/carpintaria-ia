import streamlit as st
import os
import pandas as pd
import json
import io
import time
from datetime import datetime, date
from smolagents import CodeAgent, LiteLLMModel, tool

# ==========================================
# 🔧 SETUP & BANCO DE DADOS
# ==========================================
try:
    import qrcode
    QR_AVAILABLE = True
except ImportError: QR_AVAILABLE = False

try:
    import ollama
    try:
        ollama.list()
        OLLAMA_AVAILABLE = True
    except:
        OLLAMA_AVAILABLE = False
except: OLLAMA_AVAILABLE = False

# Fallback para busca se a biblioteca faltar
try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError: BUSCA_DISPONIVEL = False

DB_FILES = {
    "projetos": "db_projetos.json",
    "clientes": "db_clientes.json",
    "financas": "db_financas.json",
    "eventos": "db_eventos.json"
}

# --- FUNÇÕES DE DADOS ---
def carregar_dados(tipo):
    arquivo = DB_FILES.get(tipo)
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f: 
            try:
                df = pd.read_json(f)
                # Conversão segura de datas
                if "Prazo" in df.columns: df["Prazo"] = pd.to_datetime(df["Prazo"]).dt.date
                if "Data" in df.columns: df["Data"] = pd.to_datetime(df["Data"]).dt.date
                return df
            except: pass # Se der erro no JSON, retorna vazio
    
    # Estruturas padrão para não quebrar o app
    if tipo == "projetos":
        return pd.DataFrame(columns=["Projeto", "Cliente", "Status", "Prazo", "Valor", "Progresso", "Prioridade"])
    elif tipo == "financas":
        return pd.DataFrame(columns=["Data", "Descricao", "Categoria", "Tipo", "Valor", "Status"])
    elif tipo == "clientes":
        return pd.DataFrame(columns=["Nome", "Empresa", "Email", "Telefone", "Status"])
    return pd.DataFrame()

def salvar_dados(tipo, df):
    arquivo = DB_FILES.get(tipo)
    df.to_json(arquivo, orient="records", date_format="iso")

# ==========================================
# 🎨 UI SISTEMA (GLASSMORPHISM PRO)
# ==========================================
st.set_page_config(page_title="Carpintaria OS Pro", page_icon="🪚", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* FUNDO E FONTE */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(242, 246, 252) 0%, rgb(227, 235, 245) 90%);
        font-family: 'Inter', sans-serif;
    }
    header[data-testid="stHeader"] {background: transparent;}

    /* CARDS KANBAN */
    .kanban-card {
        background: white; padding: 15px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px;
        border-left: 4px solid #0ea5e9; transition: transform 0.2s;
    }
    .kanban-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }

    /* MENU LATERAL */
    section[data-testid="stSidebar"] { background-color: #0f172a; }
    section[data-testid="stSidebar"] h1, h2, h3, p { color: white !important; }
    
    /* BOTÕES */
    .stButton>button { border-radius: 8px; font-weight: 600; }
    
    /* TICKET VISUAL */
    .ticket-card {
        border: 1px dashed #cbd5e1; border-left: 5px solid #0f172a;
        padding: 20px; border-radius: 10px; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Lógica do Logo: Tenta local, senão usa URL
LOGO_URL = "CarpintariaDigitalLogo.png"
if not os.path.exists(LOGO_URL):
    LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2040/2040946.png"

# ==========================================
# 🧠 TOOLS PARA A IA
# ==========================================
@tool
def buscar_web(termo: str) -> str:
    """Pesquisa no DuckDuckGo. Args: termo: Texto a buscar."""
    if not BUSCA_DISPONIVEL: return "Busca indisponível."
    try:
        res = DDGS().text(termo, max_results=3)
        return str(res)
    except Exception as e: return f"Erro: {e}"

# ==========================================
# 🧭 NAVEGAÇÃO & ESTADO
# ==========================================
if "page" not in st.session_state: st.session_state["page"] = "entrada"
if "auth" not in st.session_state: st.session_state["auth"] = False
if "messages" not in st.session_state: st.session_state["messages"] = []

def navegar(destino):
    st.session_state["page"] = destino
    st.rerun()

# ==========================================
# PÁGINA 1: ENTRADA
# ==========================================
if st.session_state["page"] == "entrada":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Exibe imagem do logo (seja local ou URL)
        st.image(LOGO_URL, width=80, use_container_width=False)
        st.markdown(f"""
        <div style="text-align: center;">
            <h1 style="color:#1e293b; font-size: 3rem;">Carpintaria Digital</h1>
            <p style="color:#64748b;">ENTERPRISE OS v8.0</p>
        </div>
        """, unsafe_allow_html=True)

    c_left, c_spacer, c_right = st.columns([1, 0.2, 1])
    with c_left:
        st.info("🛒 **Dumbanengue**\n\nVitrine pública de Apps.")
        if st.button("Acessar Vitrine ➔", use_container_width=True): navegar("dumbanengue")
    with c_right:
        st.error("💼 **Escritório Corporativo**\n\nERP, CRM, Projetos e IA.")
        if st.button("Login Seguro 🔒", use_container_width=True): navegar("login")

# ==========================================
# PÁGINA 2: DUMBANENGUE
# ==========================================
elif st.session_state["page"] == "dumbanengue":
    st.button("⬅ Voltar", on_click=lambda: navegar("entrada"))
    st.title("🛒 Vitrine de Soluções")
    colunas = st.columns(3)
    apps = [{"n": "Estoque", "i": "📦"}, {"n": "Catálogo", "i": "📖"}, {"n": "Orçamentos", "i": "💰"}]
    for i, app in enumerate(apps):
        with colunas[i]:
            st.markdown(f"### {app['i']} {app['n']}")
            st.button("Ver Detalhes", key=f"btn_{i}")

# ==========================================
# PÁGINA 3: LOGIN
# ==========================================
elif st.session_state["page"] == "login":
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h2 style='text-align:center'>🔒 Acesso Master</h2>", unsafe_allow_html=True)
        senha = st.text_input("Chave de Acesso", type="password")
        if st.button("Autenticar", use_container_width=True):
            senha_real = st.secrets.get("APP_PASSWORD", "admin")
            if senha == senha_real:
                st.session_state["auth"] = True
                navegar("escritorio")
            else:
                st.error("Chave inválida.")
        if st.button("Cancelar"): navegar("entrada")

# ==========================================
# PÁGINA 4: ESCRITÓRIO (O HUB)
# ==========================================
elif st.session_state["page"] == "escritorio":
    if not st.session_state["auth"]: navegar("entrada")

    # --- SIDEBAR COMPLETA ---
    with st.sidebar:
        st.image(LOGO_URL, width=50)
        st.title("Workspace")
        
        modulo = st.radio("Módulos", [
            "📊 Dashboard Geral",
            "🚀 Projetos (Kanban)",
            "💰 Financeiro Pro",
            "👥 Clientes CRM",
            "🧠 Cérebro IA",
            "🎟️ Eventos QR"
        ])
        
        st.markdown("---")
        
        # CONTROLES DA IA (Só aparecem se estiver no módulo IA)
        if modulo == "🧠 Cérebro IA":
            with st.expander("⚙️ Configuração IA", expanded=True):
                opcoes = {}
                opcoes["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
                opcoes["🚀 Groq Llama 3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
                if OLLAMA_AVAILABLE:
                    opcoes["🏠 Local: Qwen"] = ("ollama/qwen2.5-coder:3b", None)
                
                escolha = st.selectbox("Modelo:", list(opcoes.keys()))
                st.session_state["modelo_ia"] = opcoes[escolha]
                
                if st.button("Limpar Chat"):
                    st.session_state["messages"] = []
                    st.rerun()

        st.markdown("---")
        if st.button("☁️ Backup Total"):
            dados = {k: carregar_dados(k).to_dict(orient="records") for k in DB_FILES.keys()}
            st.download_button("⬇️ Baixar JSON", json.dumps(dados, default=str), "backup.json")

        if st.button("Sair"):
            st.session_state["auth"] = False
            navegar("entrada")

    # --- 1. DASHBOARD GERAL (ARRANJADO) ---
    if modulo == "📊 Dashboard Geral":
        st.title("📊 Visão Executiva")
        
        # Carrega dados reais
        df_proj = carregar_dados("projetos")
        df_fin = carregar_dados("financas")
        df_cli = carregar_dados("clientes")
        
        # Cálculos
        n_proj = len(df_proj[df_proj["Status"] == "Em Curso"]) if not df_proj.empty else 0
        n_cli = len(df_cli) if not df_cli.empty else 0
        
        saldo = 0.0
        if not df_fin.empty:
            ent = df_fin[df_fin["Tipo"]=="Entrada"]["Valor"].sum()
            sai = df_fin[df_fin["Tipo"]=="Saída"]["Valor"].sum()
            saldo = ent - sai

        c1, c2, c3 = st.columns(3)
        c1.metric("Projetos Ativos", n_proj, "+1 esta semana")
        c2.metric("Total Clientes", n_cli)
        c3.metric("Lucro Líquido", f"MT {saldo:,.2f}", delta="Atualizado agora")
        
        st.markdown("### 📅 Cronograma Recente")
        if not df_proj.empty:
            st.dataframe(df_proj[["Projeto", "Status", "Prazo", "Progresso"]].head(), use_container_width=True)

    # --- 2. PROJETOS (KANBAN/TRELLO) ---
    elif modulo == "🚀 Projetos (Kanban)":
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 Gestão de Projetos")
        with c2: view_mode = st.radio("Modo", ["Tabela", "Kanban"], horizontal=True)
        
        df_proj = carregar_dados("projetos")
        
        if view_mode == "Tabela":
            edited = st.data_editor(df_proj, num_rows="dynamic", use_container_width=True, key="edit_proj")
            if st.button("Salvar Projetos"): salvar_dados("projetos", edited)
        else:
            cols = st.columns(3)
            status_list = ["A Fazer", "Em Curso", "Concluído"]
            colors = ["#fee2e2", "#fef9c3", "#dcfce7"]
            for idx, s in enumerate(status_list):
                with cols[idx]:
                    st.markdown(f"<div style='background:{colors[idx]}; padding:10px; border-radius:5px; text-align:center;'><b>{s}</b></div>", unsafe_allow_html=True)
                    if not df_proj.empty:
                        tasks = df_proj[df_proj["Status"] == s]
                        for _, row in tasks.iterrows():
                            st.markdown(f"""
                            <div class="kanban-card">
                                <b>{row.get('Projeto', 'Sem Nome')}</b><br>
                                <small>👤 {row.get('Cliente', '-')}</small><br>
                                <small>📅 {row.get('Prazo', '-')}</small>
                            </div>
                            """, unsafe_allow_html=True)

    # --- 3. FINANCEIRO PRO ---
    elif modulo == "💰 Financeiro Pro":
        st.title("💰 Controle Financeiro")
        df_fin = carregar_dados("financas")
        
        # Gráfico
        if not df_fin.empty:
            chart_data = df_fin.copy()
            chart_data.loc[chart_data["Tipo"] == "Saída", "Valor"] *= -1
            st.bar_chart(chart_data, x="Data", y="Valor", color="Tipo")
            
        edited = st.data_editor(df_fin, num_rows="dynamic", use_container_width=True, key="edit_fin")
        if st.button("Salvar Finanças"): salvar_dados("financas", edited)

    # --- 4. CRM CLIENTES (ARRANJADO) ---
    elif modulo == "👥 Clientes CRM":
        st.title("👥 Gestão de Clientes")
        df_cli = carregar_dados("clientes")
        
        if not df_cli.empty:
            st.info(f"Total de contatos na base: {len(df_cli)}")
        
        edited = st.data_editor(df_cli, num_rows="dynamic", use_container_width=True, key="edit_cli")
        if st.button("Salvar Clientes"): salvar_dados("clientes", edited)

    # --- 5. CÉREBRO IA (RESTAURADO & FUNCIONAL) ---
    elif modulo == "🧠 Cérebro IA":
        st.title("🧠 Inteligência Artificial")
        
        # Verifica se modelo foi selecionado na sidebar
        if "modelo_ia" not in st.session_state:
            st.warning("Selecione um modelo na barra lateral.")
        else:
            mid, env_key = st.session_state["modelo_ia"]
            st.caption(f"Modelo Ativo: {mid}")

            # Chat UI
            for msg in st.session_state["messages"]:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt := st.chat_input("Pergunte à Carpintaria..."):
                st.session_state["messages"].append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)

                with st.chat_message("assistant"):
                    ph = st.empty()
                    try:
                        api_key = st.secrets.get(env_key) if env_key else None
                        base = "http://localhost:11434" if "ollama" in mid else None
                        
                        modelo = LiteLLMModel(model_id=mid, api_key=api_key, api_base=base)
                        
                        # Agente com ferramenta de busca
                        tools = [buscar_web] if BUSCA_DISPONIVEL else []
                        agent = CodeAgent(tools=tools, model=modelo, add_base_tools=True)
                        
                        res = agent.run(prompt)
                        ph.markdown(res)
                        st.session_state["messages"].append({"role": "assistant", "content": res})
                    except Exception as e:
                        st.error(f"Erro na IA: {e}")

    # --- 6. EVENTOS QR (VISUAL & FUNCIONAL) ---
    elif modulo == "🎟️ Eventos QR":
        st.title("🎟️ Gestor de Tickets")
        
        c1, c2 = st.columns(2)
        with c1:
            nome_ev = st.text_input("Evento", "Conferência 2026")
            tipo = st.selectbox("Tipo", ["VIP (Dourado)", "Standard (Azul)", "Staff (Cinza)"])
            participante = st.text_input("Participante")
            
            if st.button("Gerar Ticket"):
                if QR_AVAILABLE and participante:
                    st.session_state["qr_data"] = {
                        "ev": nome_ev, "tipo": tipo, "part": participante, "time": str(datetime.now())
                    }
                else: st.error("Instale 'qrcode' ou preencha os dados.")
        
        with c2:
            if "qr_data" in st.session_state:
                d = st.session_state["qr_data"]
                
                # Cores baseadas no tipo
                bg = "#fef9c3" if "VIP" in d["tipo"] else "#e0f2fe" if "Standard" in d["tipo"] else "#f3f4f6"
                border = "#ca8a04" if "VIP" in d["tipo"] else "#0284c7"
                
                # Gera QR
                img = qrcode.make(str(d))
                buf = io.BytesIO()
                img.save(buf)
                byte_im = buf.getvalue()
                
                # Ticket Visual HTML
                st.markdown(f"""
                <div style="background:{bg}; padding:20px; border-radius:15px; border:2px solid {border}; text-align:center;">
                    <h3 style="margin:0; color:#333;">{d['ev']}</h3>
                    <span style="background:{border}; color:white; padding:2px 8px; border-radius:10px; font-size:0.8rem;">{d['tipo']}</span>
                    <hr style="border-color:#ccc; margin:15px 0;">
                    <h2 style="margin:10px 0;">{d['part']}</h2>
                </div>
                """, unsafe_allow_html=True)
                st.image(byte_im, width=200)