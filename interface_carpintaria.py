import streamlit as st
import os
import pandas as pd
import requests
import json
import base64
import io
from datetime import datetime
from smolagents import CodeAgent, LiteLLMModel, tool

# Tenta importar qrcode, se não tiver, usa fallback
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

# ==========================================
# 💾 BANCO DE DADOS LOCAL (JSON)
# ==========================================
DB_FILES = {
    "projetos": "db_projetos.json",
    "clientes": "db_clientes.json",
    "financas": "db_financas.json",
    "eventos": "db_eventos.json" # Novo DB para eventos
}

def carregar_dados(tipo):
    arquivo = DB_FILES.get(tipo)
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f:
            return pd.read_json(f)
    else:
        if tipo == "projetos":
            return pd.DataFrame(columns=["ID", "Projeto", "Tipo", "Cliente", "Status", "Prazo", "Valor"])
        elif tipo == "clientes":
            return pd.DataFrame(columns=["ID", "Nome", "Empresa", "Email", "Telefone", "Obs"])
        elif tipo == "financas":
            return pd.DataFrame(columns=["Data", "Descricao", "Categoria", "Tipo", "Valor", "Status"])
        elif tipo == "eventos":
            return pd.DataFrame(columns=["Evento", "Tipo", "Data", "Participante", "Codigo_QR", "Status"])
        return pd.DataFrame()

def salvar_dados(tipo, df):
    arquivo = DB_FILES.get(tipo)
    df.to_json(arquivo, orient="records", date_format="iso")

# ==========================================
# 📱 CONFIGURAÇÃO VITRINE
# ==========================================
MEUS_APPS = [
    {"nome": "Gestão de Estoque", "icone": "📦", "desc": "Controle de madeira e insumos.", "link": "#"},
    {"nome": "Catálogo Digital", "icone": "📖", "desc": "Vitrine de produtos.", "link": "#"},
    {"nome": "Orçamentos", "icone": "💰", "desc": "Calculadora de projetos.", "link": "#"}
]

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Carpintaria OS",
    page_icon="🪚",
    layout="wide",
    initial_sidebar_state="collapsed" # Começa fechado para focar na Entrada
)

# LOGO URL (Seu logo)
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/2040/2040946.png"

# --- CSS PREMIUM (UI/UX) ---
st.markdown("""
<style>
    /* 1. Limpeza Geral */
    header[data-testid="stHeader"] {background-color: transparent;}
    .stApp {background-color: #F8FAFC;} /* Light Clean (Cinza muito suave) */
    
    /* 2. Animação de Ícones Flutuantes (Background) */
    @keyframes float {
        0% { transform: translateY(0px) rotate(0deg); opacity: 0.1; }
        50% { transform: translateY(-20px) rotate(5deg); opacity: 0.3; }
        100% { transform: translateY(0px) rotate(0deg); opacity: 0.1; }
    }
    
    .floating-icon {
        position: fixed;
        color: #64748b;
        font-size: 2rem;
        z-index: 0; /* Fica atrás de tudo */
        animation: float 6s ease-in-out infinite;
    }
    
    /* Posicionamento dos Ícones no Fundo */
    .icon-1 { top: 10%; left: 10%; animation-delay: 0s; }
    .icon-2 { top: 20%; right: 15%; animation-delay: 1s; }
    .icon-3 { bottom: 15%; left: 20%; animation-delay: 2s; }
    .icon-4 { bottom: 30%; right: 10%; animation-delay: 3s; }
    .icon-5 { top: 50%; left: 5%; animation-delay: 4s; }
    .icon-6 { top: 15%; left: 50%; animation-delay: 1.5s; }

    /* 3. Botões da Entrada (Grandes e Modernos) */
    .btn-entrada {
        width: 100%;
        padding: 30px;
        border-radius: 20px;
        border: none;
        font-weight: bold;
        font-size: 1.2rem;
        transition: transform 0.2s;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        display: block;
    }
    .btn-entrada:hover { transform: scale(1.05); }
    
    /* Estilo Específico via Streamlit Button Hack */
    div.stButton > button {
        border-radius: 12px;
        height: auto;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    /* 4. Ticket de Evento */
    .ticket-card {
        background: white;
        border: 1px dashed #cbd5e1;
        border-left: 5px solid #0f172a;
        padding: 20px;
        margin-top: 10px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }

    /* Conteúdo acima do fundo */
    .main-content {
        position: relative;
        z-index: 10;
    }
</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<div class="floating-icon icon-1"><i class="fas fa-brain"></i></div> <div class="floating-icon icon-2"><i class="fas fa-heartbeat"></i></div> <div class="floating-icon icon-3"><i class="fas fa-bullhorn"></i></div> <div class="floating-icon icon-4"><i class="fas fa-robot"></i></div> <div class="floating-icon icon-5"><i class="fas fa-shield-alt"></i></div> <div class="floating-icon icon-6"><i class="fas fa-qrcode"></i></div> """, unsafe_allow_html=True)

# ==========================================
# 🔐 LÓGICA DE NAVEGAÇÃO E SENHA
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "entrada"
if "senha_validada" not in st.session_state:
    st.session_state["senha_validada"] = False

def ir_para(pagina):
    if pagina == "escritorio":
        # Se for escritório, pede senha primeiro
        st.session_state["tentando_acessar_escritorio"] = True
    else:
        st.session_state["pagina_atual"] = pagina

# ==========================================
# 🖥️ PÁGINA 1: A ENTRADA (NOVO DESIGN)
# ==========================================
if st.session_state["pagina_atual"] == "entrada":
    # Verifica se está tentando logar
    if st.session_state.get("tentando_acessar_escritorio", False):
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.info("🔒 Área Restrita: Escritório")
            senha = st.text_input("Insira a senha:", type="password")
            c_a, c_b = st.columns(2)
            if c_a.button("Entrar"):
                # Verifica senha (nos secrets ou padrão dev)
                senha_real = st.secrets.get("APP_PASSWORD", "1234") 
                if senha == senha_real:
                    st.session_state["senha_validada"] = True
                    st.session_state["pagina_atual"] = "escritorio"
                    st.session_state["tentando_acessar_escritorio"] = False
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            if c_b.button("Cancelar"):
                st.session_state["tentando_acessar_escritorio"] = False
                st.rerun()
        st.stop()

    # LAYOUT DA ENTRADA
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    
    # Espaçamento vertical para centralizar
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col_esq, col_centro, col_dir = st.columns([1, 1.5, 1])
    
    with col_esq:
        st.markdown("<br><br>", unsafe_allow_html=True) # Alinha verticalmente
        if st.button("🛒 DUMBANENGUE\n(Vitrine Pública)", use_container_width=True):
            ir_para("dumbanengue")
            st.rerun()
            
    with col_centro:
        # LOGO NO MEIO
        st.markdown(f"""
        <div style="text-align: center;">
            <img src="{LOGO_URL}" width="180" style="border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
            <h1 style="color: #0f172a; margin-top: 10px;">Carpintaria Digital</h1>
            <p style="color: #64748b;">Sistema Operacional Integrado</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_dir:
        st.markdown("<br><br>", unsafe_allow_html=True) # Alinha verticalmente
        if st.button("💼 ESCRITÓRIO\n(Área de Gestão)", use_container_width=True, type="primary"):
            ir_para("escritorio")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🖥️ PÁGINA 2: DUMBANENGUE (VITRINE)
# ==========================================
elif st.session_state["pagina_atual"] == "dumbanengue":
    if st.button("⬅️ Voltar à Entrada"):
        st.session_state["pagina_atual"] = "entrada"
        st.rerun()
        
    st.title("🛒 Dumbanengue Digital")
    st.markdown("Soluções prontas para o seu negócio.")
    
    colunas = st.columns(3)
    for index, app in enumerate(MEUS_APPS):
        with colunas[index % 3]:
            with st.container(border=True):
                st.markdown(f"## {app['icone']}")
                st.markdown(f"**{app['nome']}**")
                st.caption(app['desc'])
                st.link_button("Acessar App", app['link'], use_container_width=True)

# ==========================================
# 🖥️ PÁGINA 3: ESCRITÓRIO (ERP + IA + EVENTOS)
# ==========================================
elif st.session_state["pagina_atual"] == "escritorio":
    if not st.session_state["senha_validada"]:
        st.session_state["pagina_atual"] = "entrada"
        st.rerun()

    # --- SIDEBAR DO ESCRITÓRIO ---
    with st.sidebar:
        st.image(LOGO_URL, width=60)
        st.title("Escritório")
        
        modulo = st.radio("Menu", [
            "📊 Dashboard", 
            "🎟️ Gestor de Eventos", # NOVO!
            "📂 Projetos", 
            "👥 Clientes", 
            "💰 Financeiro", 
            "🧠 IA Assistente"
        ])
        
        st.markdown("---")
        if st.button("🚪 Sair"):
            st.session_state["senha_validada"] = False
            st.session_state["pagina_atual"] = "entrada"
            st.rerun()

    # --- MÓDULO: GESTOR DE EVENTOS (NOVO) ---
    if modulo == "🎟️ Gestor de Eventos":
        st.title("🎟️ Gestor de Eventos & Bilhetes")
        st.caption("Crie convites QR Code para eventos corporativos, desportivos e festas.")
        
        if not QR_AVAILABLE:
            st.warning("⚠️ Biblioteca 'qrcode' não instalada. Rode: pip install qrcode[pil]")
        else:
            tabs = st.tabs(["Criar Novo Ticket", "Meus Eventos"])
            
            with tabs[0]:
                c1, c2 = st.columns(2)
                with c1:
                    evt_nome = st.text_input("Nome do Evento", "Conferência Tech 2025")
                    evt_tipo = st.selectbox("Tipo de Ticket", ["Bilhete Desportivo", "Convite Corporativo", "Ingresso Festa", "Check-in Staff"])
                    evt_data = st.date_input("Data do Evento")
                    evt_participante = st.text_input("Nome do Participante / Convidado")
                
                with c2:
                    st.markdown("### Prévia do Design")
                    cor_bg = "#ffffff"
                    if evt_tipo == "Bilhete Desportivo": cor_bg = "#e0f2fe" # Azul claro
                    if evt_tipo == "Convite Corporativo": cor_bg = "#f1f5f9" # Cinza
                    if evt_tipo == "Ingresso Festa": cor_bg = "#fce7f3" # Rosa claro
                    
                    st.markdown(f"""
                    <div style="background-color:{cor_bg}; padding:15px; border-radius:10px; border:1px solid #ccc; text-align:center;">
                        <h4>{evt_nome}</h4>
                        <p><strong>{evt_tipo}</strong></p>
                        <hr>
                        <h2>QR CODE AQUI</h2>
                        <p>{evt_participante}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button("🖨️ Gerar Ticket QR Code"):
                    if evt_participante:
                        # Gera QR Code
                        dados_qr = f"EVENTO:{evt_nome}|TIPO:{evt_tipo}|NOME:{evt_participante}|DATA:{evt_data}"
                        qr = qrcode.make(dados_qr)
                        
                        # Converte para imagem mostrável no Streamlit
                        img_byte_arr = io.BytesIO()
                        qr.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        # Salva no DB local
                        st.image(img_byte_arr, width=200, caption="Código de Acesso Gerado")
                        st.success(f"Ticket criado para {evt_participante}!")
                    else:
                        st.error("Preencha o nome do participante.")

    # --- MÓDULO: DASHBOARD ---
    elif modulo == "📊 Dashboard":
        st.title("Visão Geral")
        df_fin = carregar_dados("financas")
        rec = df_fin[df_fin["Tipo"]=="Entrada"]["Valor"].sum()
        desp = df_fin[df_fin["Tipo"]=="Saída"]["Valor"].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Faturamento", f"MT {rec:,.2f}")
        c2.metric("Despesas", f"MT {desp:,.2f}")
        c3.metric("Eventos Ativos", "3") # Exemplo
        
        st.markdown("### Acesso Rápido")
        st.info("Use o menu lateral para navegar nos módulos.")

    # --- OUTROS MÓDULOS (Mantidos da versão anterior) ---
    elif modulo == "📂 Projetos":
        st.title("Projetos")
        df = carregar_dados("projetos")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="proj_editor")
        if st.button("Salvar Projetos"): salvar_dados("projetos", edited)

    elif modulo == "👥 Clientes":
        st.title("Clientes")
        df = carregar_dados("clientes")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="cli_editor")
        if st.button("Salvar Clientes"): salvar_dados("clientes", edited)
        
    elif modulo == "💰 Financeiro":
        st.title("Financeiro")
        df = carregar_dados("financas")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="fin_editor")
        if st.button("Salvar Finanças"): salvar_dados("financas", edited)
        
    elif modulo == "🧠 IA Assistente":
        st.title("IA Carpintaria")
        # Interface de chat simplificada
        prompt = st.chat_input("Como posso ajudar?")
        if prompt:
            st.chat_message("user").write(prompt)
            st.chat_message("assistant").write("Estou conectando aos módulos...")
            # (Aqui você insere a lógica do CodeAgent se tiver as APIs configuradas)