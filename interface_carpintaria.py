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
# Tenta carregar bibliotecas opcionais sem quebrar o sistema
try:
    import qrcode
    QR_AVAILABLE = True
except ImportError: 
    QR_AVAILABLE = False

try:
    import ollama
    try:
        ollama.list()
        OLLAMA_AVAILABLE = True
    except:
        OLLAMA_AVAILABLE = False
except: 
    OLLAMA_AVAILABLE = False

# Fallback para busca web
try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError: 
    BUSCA_DISPONIVEL = False

# Arquivos de dados
DB_FILES = {
    "projetos": "db_projetos.json",
    "clientes": "db_clientes.json",
    "financas": "db_financas.json",
    "eventos": "db_eventos.json"
}

# --- FUNÇÕES DE DADOS (PERSISTÊNCIA) ---
def carregar_dados(tipo):
    arquivo = DB_FILES.get(tipo)
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f: 
            try:
                df = pd.read_json(f)
                # Conversão segura de datas para evitar erros de plotagem
                if "Prazo" in df.columns: df["Prazo"] = pd.to_datetime(df["Prazo"]).dt.date
                if "Data" in df.columns: df["Data"] = pd.to_datetime(df["Data"]).dt.date
                return df
            except: pass 
    
    # Estruturas padrão vazias (Evita erros de "DataFrame not found")
    if tipo == "projetos":
        return pd.DataFrame(columns=["Projeto", "Cliente", "Status", "Prazo", "Valor", "Progresso", "Prioridade"])
    elif tipo == "financas":
        return pd.DataFrame(columns=["Data", "Descricao", "Categoria", "Tipo", "Valor", "Status"])
    elif tipo == "clientes":
        return pd.DataFrame(columns=["Nome", "Empresa", "Email", "Telefone", "Status"])
    return pd.DataFrame()

def salvar_dados(tipo, df):
    arquivo = DB_FILES.get(tipo)
    # Salva datas em formato ISO
    df.to_json(arquivo, orient="records", date_format="iso")

# ==========================================
# 🎨 UI SISTEMA (GLASSMORPHISM PRO)
# ==========================================
st.set_page_config(page_title="Carpintaria OS Pro", page_icon="🪚", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    /* 1. FUNDO E CONFIGURAÇÕES GERAIS */
    .stApp {
        background: linear-gradient(135deg, #e0e7ff 0%, #f8fafc 100%);
        font-family: 'Inter', sans-serif;
    }
    header[data-testid="stHeader"] {background: transparent;}
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 2. GLASSMORPHISM AVANÇADO */
    .stContainer, .stAlert, .stExpander, [data-testid="stVerticalBlock"] > div:has(div.stAlert), .kanban-card {
        background: rgba(255, 255, 255, 0.4) !important;
        border-radius: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        transition: transform 0.3s ease;
    }
    
    .kanban-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12) !important;
    }

    /* 3. BOTÕES PROFISSIONAIS */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        border: none !important;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
    }
    
    .stButton>button:hover {
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4) !important;
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    }

    /* 4. SIDEBAR GLASS */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* 5. MENU FLUTUANTE COM ANIMAÇÃO */
    .floating-menu {
        position: fixed;
        top: 50%;
        left: 20px;
        transform: translateY(-50%);
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 15px;
        padding: 15px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: floatSidebar 3s ease-in-out infinite;
    }

    @keyframes floatSidebar {
        0%, 100% { transform: translateY(-50%) translateX(0px); }
        50% { transform: translateY(-52%) translateX(5px); }
    }

    .floating-icon {
        width: 45px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        font-size: 1.2rem;
        background: rgba(255, 255, 255, 0.8);
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        position: relative;
    }

    .floating-icon:hover {
        transform: scale(1.2) rotate(10deg);
        background: #6366f1;
        color: white;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
    }

    .floating-icon::after {
        content: attr(data-tooltip);
        position: absolute;
        left: 60px;
        background: #1e293b;
        color: white;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }

    .floating-icon:hover::after {
        opacity: 1;
        visibility: visible;
        left: 55px;
    }
    
    /* 6. LOGO BOX */
    .logo-box {
        background: white;
        border-radius: 20px;
        padding: 12px;
        width: 90px;
        height: 90px;
        margin: 0 auto 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9;
    }
    
    /* 7. AJUSTE DE LAYOUT */
    .block-container {
        padding-left: 100px !important;
        padding-right: 50px !important;
    }

    /* Estilização de métricas */
    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# Lógica do Logo Inteligente
LOGO_URL = "CarpintariaDigitalLogo.png"
if not os.path.exists(LOGO_URL):
    LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2040/2040946.png"

# --- MENU FLUTUANTE GLOBAL ---
def render_floating_menu():
    menu_html = """
    <div class="floating-menu">
        <div class="floating-icon" data-tooltip="ERP / Dashboard">📊</div>
        <div class="floating-icon" data-tooltip="Inteligência Artificial">🧠</div>
        <div class="floating-icon" data-tooltip="Saúde / Bem-estar">🏥</div>
        <div class="floating-icon" data-tooltip="Vendas / CRM">📈</div>
        <div class="floating-icon" data-tooltip="Marketing">📱</div>
        <div class="floating-icon" data-tooltip="Stock / Estoque">📦</div>
        <div class="floating-icon" data-tooltip="CRM">🤝</div>
        <div class="floating-icon" data-tooltip="Consultoria">💼</div>
        <div class="floating-icon" data-tooltip="Academia / Treino">🎓</div>
        <div class="floating-icon" data-tooltip="Dev / Código">💻</div>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)

render_floating_menu()

# ==========================================
# 🧠 FERRAMENTAS IA (CORRIGIDO PARA SMOLAGENTS)
# ==========================================
@tool
def buscar_web(termo: str) -> str:
    """
    Realiza uma pesquisa na internet usando o DuckDuckGo.
    
    Args:
        termo: O texto ou assunto que você deseja pesquisar na web.
    """
    if not BUSCA_DISPONIVEL: return "Módulo de busca não instalado."
    try:
        res = DDGS().text(termo, max_results=3)
        return str(res)
    except Exception as e: return f"Erro na busca: {e}"

# ==========================================
# 🧭 NAVEGAÇÃO
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
        # Logo Box para destaque
        st.markdown(f"""
        <div style="display:flex; justify-content:center;">
            <div class="logo-box"><img src="{LOGO_URL}" width="50"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align: center;">
            <h1 style="color:#1e293b; font-size: 3rem; margin-top:10px;">Carpintaria Digital</h1>
            <p style="color:#64748b; font-size: 1.2rem;">ENTERPRISE OS v8.1</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_spacer, c_right = st.columns([1, 0.2, 1])
    
    with c_left:
        st.info("🛒 **Dumbanengue**\n\nVitrine pública de Apps e Serviços.")
        if st.button("Acessar Vitrine ➔", use_container_width=True): navegar("dumbanengue")
        
    with c_right:
        st.warning("💼 **Escritório Corporativo**\n\nGestão, Finanças, CRM e IA.")
        if st.button("Login Master 🔒", use_container_width=True): navegar("login")

# ==========================================
# PÁGINA 2: DUMBANENGUE
# ==========================================
elif st.session_state["page"] == "dumbanengue":
    st.button("⬅ Voltar à Entrada", on_click=lambda: navegar("entrada"))
    st.title("🛒 Vitrine de Soluções")
    st.markdown("---")
    
    colunas = st.columns(3)
    apps = [
        {"n": "Gestão de Estoque", "i": "📦", "d": "Controle de entrada e saída."},
        {"n": "Catálogo Digital", "i": "📖", "d": "Vitrine para seus clientes."},
        {"n": "Calculadora de Obras", "i": "💰", "d": "Orçamentos automáticos."}
    ]
    
    for i, app in enumerate(apps):
        with colunas[i]:
            with st.container(border=True):
                st.markdown(f"## {app['i']}")
                st.markdown(f"**{app['n']}**")
                st.caption(app['d'])
                st.button("Acessar Demo", key=f"btn_app_{i}", use_container_width=True)

# ==========================================
# PÁGINA 3: LOGIN
# ==========================================
elif st.session_state["page"] == "login":
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.markdown("<br><br><h2 style='text-align:center'>🔒 Acesso Master</h2>", unsafe_allow_html=True)
        senha = st.text_input("Senha de Administrador", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("Entrar", use_container_width=True):
            # Senha padrão "admin" se não configurada nos secrets
            senha_real = st.secrets.get("APP_PASSWORD", "admin")
            if senha == senha_real:
                st.session_state["auth"] = True
                navegar("escritorio")
            else:
                st.error("Acesso Negado.")
                
        if col_btn2.button("Cancelar", use_container_width=True): navegar("entrada")

# ==========================================
# PÁGINA 4: ESCRITÓRIO (HUB)
# ==========================================
elif st.session_state["page"] == "escritorio":
    if not st.session_state["auth"]: navegar("entrada")

    # --- SIDEBAR PROFISSIONAL ---
    with st.sidebar:
        st.markdown(f"""
        <div class="logo-box" style="width:60px; height:60px;">
            <img src="{LOGO_URL}" width="40">
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center'>Workspace</h3>", unsafe_allow_html=True)
        
        modulo = st.radio("Navegação", [
            "📊 Dashboard Geral",
            "🚀 Projetos (Kanban)",
            "💰 Financeiro Pro",
            "👥 Clientes CRM",
            "🧠 Cérebro IA",
            "🎟️ Eventos QR"
        ])
        
        st.markdown("---")
        
        # CONTROLES ESPECÍFICOS DA IA
        if modulo == "🧠 Cérebro IA":
            with st.expander("⚙️ Configurar Cérebro", expanded=True):
                opcoes = {}
                opcoes["☁️ Gemini 2.5 Flash"] = ("gemini/gemini-2.5-flash", "GEMINI_API_KEY")
                opcoes["🚀 Groq Llama 3"] = ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY")
                if OLLAMA_AVAILABLE:
                    opcoes["🏠 Local: Qwen 2.5"] = ("ollama/qwen2.5-coder:3b", None)
                
                escolha = st.selectbox("Modelo:", list(opcoes.keys()))
                st.session_state["modelo_ia"] = opcoes[escolha]
                st.slider("Criatividade", 0.0, 1.0, 0.3)
                
                if st.button("Limpar Chat"):
                    st.session_state["messages"] = []
                    st.rerun()

        st.markdown("---")
        if st.button("☁️ Backup dos Dados"):
            dados_completos = {k: carregar_dados(k).to_dict(orient="records") for k in DB_FILES.keys()}
            json_str = json.dumps(dados_completos, indent=2, default=str)
            st.download_button("⬇️ Baixar JSON", json_str, f"backup_{date.today()}.json", "application/json")

        if st.button("🚪 Logout"):
            st.session_state["auth"] = False
            navegar("entrada")

    # --- 1. DASHBOARD GERAL ---
    if modulo == "📊 Dashboard Geral":
        st.title("📊 Visão Executiva")
        
        # Carregando dados reais
        df_proj = carregar_dados("projetos")
        df_fin = carregar_dados("financas")
        df_cli = carregar_dados("clientes")
        
        # Cálculos de KPI
        projetos_ativos = len(df_proj[df_proj["Status"].isin(["Em Curso", "A Fazer"])]) if not df_proj.empty else 0
        total_clientes = len(df_cli) if not df_cli.empty else 0
        
        saldo_atual = 0.0
        if not df_fin.empty:
            entradas = df_fin[df_fin["Tipo"]=="Entrada"]["Valor"].sum()
            saidas = df_fin[df_fin["Tipo"]=="Saída"]["Valor"].sum()
            saldo_atual = entradas - saidas

        # KPIs Visuais
        k1, k2, k3 = st.columns(3)
        k1.metric("Projetos Ativos", projetos_ativos)
        k2.metric("Total de Clientes", total_clientes)
        k3.metric("Lucro Líquido", f"MT {saldo_atual:,.2f}", delta="Em tempo real")
        
        # Tabela Resumo
        st.markdown("### 📋 Projetos Recentes")
        if not df_proj.empty:
            st.dataframe(df_proj[["Projeto", "Status", "Prazo", "Progresso"]].head(5), use_container_width=True)
        else:
            st.info("Nenhum projeto ativo no momento.")

    # --- 2. PROJETOS (KANBAN) ---
    elif modulo == "🚀 Projetos (Kanban)":
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 Projetos")
        with c2: view_mode = st.radio("Visualização", ["Tabela", "Kanban"], horizontal=True)
        
        df_proj = carregar_dados("projetos")
        
        if view_mode == "Tabela":
            edited = st.data_editor(df_proj, num_rows="dynamic", use_container_width=True, key="edit_proj")
            if st.button("💾 Salvar Projetos"): salvar_dados("projetos", edited)
        else:
            # Modo Kanban
            cols = st.columns(3)
            status_map = ["A Fazer", "Em Curso", "Concluído"]
            colors = ["#fee2e2", "#fef9c3", "#dcfce7"] # Cores pastel
            
            for idx, status in enumerate(status_map):
                with cols[idx]:
                    st.markdown(f"<div style='background:{colors[idx]}; padding:8px; border-radius:5px; text-align:center; font-weight:bold; color:#333;'>{status}</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if not df_proj.empty:
                        tasks = df_proj[df_proj["Status"] == status]
                        for _, row in tasks.iterrows():
                            st.markdown(f"""
                            <div class="kanban-card">
                                <strong>{row.get('Projeto', 'Sem Nome')}</strong><br>
                                <span style="font-size:0.8rem; color:#666;">👤 {row.get('Cliente', '-')}</span>
                            </div>
                            """, unsafe_allow_html=True)
            st.info("ℹ️ Edite os status na visão de 'Tabela'.")

    # --- 3. FINANCEIRO PRO ---
    elif modulo == "💰 Financeiro Pro":
        st.title("💰 Financeiro")
        df_fin = carregar_dados("financas")
        
        # Gráfico de Fluxo
        if not df_fin.empty:
            chart_data = df_fin.copy()
            # Inverte valor de saída para aparecer negativo no gráfico
            chart_data.loc[chart_data["Tipo"] == "Saída", "Valor"] *= -1
            st.bar_chart(chart_data, x="Data", y="Valor", color="Tipo")
        
        edited = st.data_editor(
            df_fin, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], required=True),
                "Valor": st.column_config.NumberColumn("Valor", format="%.2f MT")
            }
        )
        if st.button("💾 Salvar Movimentações"): salvar_dados("financas", edited)

    # --- 4. CRM CLIENTES ---
    elif modulo == "👥 Clientes CRM":
        st.title("👥 Carteira de Clientes")
        df_cli = carregar_dados("clientes")
        
        edited = st.data_editor(
            df_cli,
            num_rows="dynamic",
            use_container_width=True,
            column_config={"Email": st.column_config.LinkColumn("Email")}
        )
        if st.button("💾 Salvar Clientes"): salvar_dados("clientes", edited)

    # --- 5. CÉREBRO IA ---
    elif modulo == "🧠 Cérebro IA":
        st.title("🧠 Inteligência Artificial")
        
        if "modelo_ia" not in st.session_state:
            st.warning("👈 Selecione um modelo na barra lateral primeiro.")
        else:
            mid, env_key = st.session_state["modelo_ia"]
            st.caption(f"Conectado a: {mid}")
            
            # Chat
            for msg in st.session_state["messages"]:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt := st.chat_input("Como posso ajudar a Carpintaria?"):
                st.session_state["messages"].append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.markdown(prompt)

                with st.chat_message("assistant"):
                    status = st.status("🧠 Pensando...", expanded=False)
                    try:
                        # Configuração Dinâmica
                        api_key = st.secrets.get(env_key) if env_key else None
                        base_url = "http://localhost:11434" if "ollama" in mid else None
                        
                        modelo = LiteLLMModel(
                            model_id=mid, api_key=api_key, api_base=base_url, max_tokens=2000
                        )
                        
                        # Injeta ferramenta de busca se disponível
                        minhas_tools = [buscar_web] if BUSCA_DISPONIVEL else []
                        
                        agent = CodeAgent(
                            tools=minhas_tools, 
                            model=modelo, 
                            add_base_tools=True # Adiciona ferramentas padrão (Python exec)
                        )
                        
                        resposta = agent.run(prompt)
                        status.update(label="Concluído", state="complete")
                        st.markdown(resposta)
                        st.session_state["messages"].append({"role": "assistant", "content": resposta})
                        
                    except Exception as e:
                        status.update(label="Erro", state="error")
                        st.error(f"Erro na IA: {e}")

    # --- 6. EVENTOS QR (VISUAL) ---
    elif modulo == "🎟️ Eventos QR":
        st.title("🎟️ Criador de Tickets")
        
        c1, c2 = st.columns(2)
        with c1:
            evt_nome = st.text_input("Nome do Evento", "Conferência Tech 2026")
            evt_tipo = st.selectbox("Tipo de Ticket", ["VIP (Gold)", "Normal (Blue)", "Staff (Grey)"])
            evt_nome_p = st.text_input("Nome do Participante")
            
            if st.button("Gerar Ticket QR"):
                if QR_AVAILABLE and evt_nome_p:
                    # Gera dados
                    info_qr = f"{evt_nome}|{evt_tipo}|{evt_nome_p}|{datetime.now()}"
                    st.session_state["ultimo_ticket"] = {"info": info_qr, "nome": evt_nome, "tipo": evt_tipo, "p": evt_nome_p}
                elif not QR_AVAILABLE:
                    st.error("Biblioteca 'qrcode' não instalada.")
                else:
                    st.warning("Preencha o nome do participante.")
        
        with c2:
            if "ultimo_ticket" in st.session_state:
                dados = st.session_state["ultimo_ticket"]
                
                # Cores baseadas no tipo
                bg_color = "#fef08a" if "VIP" in dados["tipo"] else "#bfdbfe" if "Normal" in dados["tipo"] else "#f3f4f6"
                border_color = "#ca8a04" if "VIP" in dados["tipo"] else "#1d4ed8" if "Normal" in dados["tipo"] else "#9ca3af"
                
                # Gerar imagem QR
                qr_img = qrcode.make(dados["info"])
                buf = io.BytesIO()
                qr_img.save(buf)
                byte_im = buf.getvalue()
                
                # Ticket HTML
                st.markdown(f"""
                <div style="background:{bg_color}; border:2px solid {border_color}; border-radius:15px; padding:20px; text-align:center; color:#333;">
                    <h3 style="margin:0;">{dados['nome']}</h3>
                    <span style="background:{border_color}; color:white; padding:2px 10px; border-radius:10px; font-size:0.8rem;">{dados['tipo']}</span>
                    <hr style="border-color:rgba(0,0,0,0.1); margin:15px 0;">
                    <h2 style="margin:5px 0;">{dados['p']}</h2>
                </div>
                """, unsafe_allow_html=True)
                st.image(byte_im, width=200, caption="Scan me")