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
    # Tenta listar para ver se o serviço está rodando
    try:
        ollama.list() 
        OLLAMA_AVAILABLE = True
    except:
        OLLAMA_AVAILABLE = False
except: OLLAMA_AVAILABLE = False

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
            df = pd.read_json(f)
            # Converte colunas de data se existirem
            if "Prazo" in df.columns: df["Prazo"] = pd.to_datetime(df["Prazo"]).dt.date
            if "Data" in df.columns: df["Data"] = pd.to_datetime(df["Data"]).dt.date
            return df
    # Retorna DataFrames vazios com a estrutura correta se não existir arquivo
    if tipo == "projetos":
        return pd.DataFrame([
            {"Projeto": "Exemplo App", "Cliente": "Carpintaria", "Status": "Em Curso", "Prazo": date.today(), "Valor": 5000.00, "Progresso": 50, "Prioridade": "Alta"}
        ])
    elif tipo == "financas":
        return pd.DataFrame([
            {"Data": date.today(), "Descricao": "Pagamento Inicial", "Categoria": "Serviço", "Tipo": "Entrada", "Valor": 15000.00, "Status": True}
        ])
    return pd.DataFrame()

def salvar_dados(tipo, df):
    arquivo = DB_FILES.get(tipo)
    # Garante que datas sejam serializáveis
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

    /* CARDS ESTILO TRELLO/KANBAN */
    .kanban-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
        border-left: 4px solid #0ea5e9;
        transition: transform 0.2s;
    }
    .kanban-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .kanban-header { font-weight: bold; color: #1e293b; margin-bottom: 5px; }
    .kanban-meta { font-size: 0.8rem; color: #64748b; display: flex; justify-content: space-between; }

    /* MENU LATERAL */
    section[data-testid="stSidebar"] { background-color: #0f172a; }
    section[data-testid="stSidebar"] h1, h2, h3 { color: white !important; }
    
    /* BOTÕES */
    .stButton>button { border-radius: 8px; font-weight: 600; }
    
    /* LOGO CONTAINER */
    .logo-box {
        background: white; border-radius: 12px; padding: 10px;
        width: 80px; height: 80px; margin: 0 auto 15px auto;
        display: flex; align-items: center; justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

LOGO_URL = "CarpintariaDigitalLogo.png"

# ==========================================
# 🧠 NAVEGAÇÃO
# ==========================================
if "page" not in st.session_state: st.session_state["page"] = "entrada"
if "auth" not in st.session_state: st.session_state["auth"] = False

def navegar(destino):
    st.session_state["page"] = destino
    st.rerun()

# ==========================================
# 1. PÁGINA: ENTRADA
# ==========================================
if st.session_state["page"] == "entrada":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="logo-box"><img src="{LOGO_URL}" width="50"></div>
            <h1 style="color:#1e293b; font-size: 3rem;">Carpintaria Digital</h1>
            <p style="color:#64748b;">ENTERPRISE OS v7.0</p>
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
# 2. PÁGINA: DUMBANENGUE
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
# 3. PÁGINA: LOGIN
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
# 4. PÁGINA: ESCRITÓRIO (O HUB)
# ==========================================
elif st.session_state["page"] == "escritorio":
    if not st.session_state["auth"]: navegar("entrada")

    # --- SIDEBAR (FERRAMENTAS) ---
    with st.sidebar:
        st.markdown(f'<div class="logo-box"><img src="{LOGO_URL}" width="40"></div>', unsafe_allow_html=True)
        st.title("Workspace")
        
        modulo = st.radio("Módulos", [
            "📊 Dashboard Geral",
            "🚀 Projetos (Trello/Notion)",
            "💰 Financeiro Pro",
            "👥 Clientes CRM",
            "🧠 Cérebro IA",
            "🎟️ Eventos QR"
        ])
        
        st.markdown("---")
        st.subheader("💾 Segurança")
        
        # BOTÃO DE BACKUP REAL
        if st.button("☁️ Fazer Backup Total"):
            # Coleta todos os dados
            dados_backup = {
                "timestamp": str(datetime.now()),
                "projetos": carregar_dados("projetos").to_dict(orient="records"),
                "financas": carregar_dados("financas").to_dict(orient="records"),
                "clientes": carregar_dados("clientes").to_dict(orient="records")
            }
            json_str = json.dumps(dados_backup, indent=2, default=str)
            st.download_button(
                label="⬇️ Baixar Arquivo (.json)",
                data=json_str,
                file_name=f"backup_carpintaria_{date.today()}.json",
                mime="application/json"
            )
            st.success("Backup pronto para download!")

        st.markdown("---")
        if st.button("Sair"):
            st.session_state["auth"] = False
            navegar("entrada")

    # --- MÓDULO: PROJETOS (NOTION + TRELLO STYLE) ---
    if modulo == "🚀 Projetos (Trello/Notion)":
        c1, c2 = st.columns([3, 1])
        with c1: st.title("🚀 Gestão de Projetos")
        with c2: 
            view_mode = st.radio("Visualização", ["📋 Tabela (Notion)", "🧱 Kanban (Trello)"], horizontal=True)
        
        df_proj = carregar_dados("projetos")
        
        # --- VIEW 1: NOTION (TABELA RICA) ---
        if view_mode == "📋 Tabela (Notion)":
            st.markdown("### Visão Detalhada")
            edited_df = st.data_editor(
                df_proj,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Progresso": st.column_config.ProgressColumn(
                        "Progresso", help="Status de conclusão", min_value=0, max_value=100, format="%f%%"
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status", options=["A Fazer", "Em Curso", "Revisão", "Concluído", "Cancelado"], required=True
                    ),
                    "Prioridade": st.column_config.SelectboxColumn(
                        "Prioridade", options=["Alta", "Média", "Baixa"], width="small"
                    ),
                    "Prazo": st.column_config.DateColumn("Prazo Final"),
                    "Valor": st.column_config.NumberColumn("Valor (MT)", format="%.2f MT")
                },
                key="editor_projetos"
            )
            
            if st.button("💾 Salvar Alterações (Tabela)"):
                salvar_dados("projetos", edited_df)
                st.toast("Projetos atualizados com sucesso!", icon="✅")

        # --- VIEW 2: KANBAN (TRELLO) ---
        elif view_mode == "🧱 Kanban (Trello)":
            st.markdown("### Quadro de Tarefas")
            
            # Filtros básicos
            cols = st.columns(3)
            status_list = ["A Fazer", "Em Curso", "Concluído"]
            colors = ["#fca5a5", "#fde047", "#86efac"] # Vermelho, Amarelo, Verde (Pastel)
            
            for idx, status in enumerate(status_list):
                with cols[idx]:
                    st.markdown(f"<div style='background:{colors[idx]}; padding:10px; border-radius:8px; text-align:center; font-weight:bold; color:#333;'>{status}</div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Filtra tarefas deste status
                    tasks = df_proj[df_proj["Status"] == status]
                    
                    if tasks.empty:
                        st.caption("Sem tarefas.")
                    else:
                        for _, row in tasks.iterrows():
                            # Card Visual
                            st.markdown(f"""
                            <div class="kanban-card">
                                <div class="kanban-header">{row['Projeto']}</div>
                                <div style="font-size:0.9rem; margin-bottom:5px;">👤 {row.get('Cliente', 'N/A')}</div>
                                <div class="kanban-meta">
                                    <span>📅 {row.get('Prazo', 'S/D')}</span>
                                    <span>💰 {row.get('Valor', 0)}</span>
                                </div>
                                <div style="margin-top:5px; height:5px; background:#e2e8f0; border-radius:3px;">
                                    <div style="width:{row.get('Progresso', 0)}%; height:100%; background:#0ea5e9; border-radius:3px;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            st.info("ℹ️ Para editar ou mover cards, use a visão 'Tabela (Notion)'.")

    # --- MÓDULO: FINANCEIRO PRO ---
    elif modulo == "💰 Financeiro Pro":
        st.title("💰 Controle Financeiro")
        
        df_fin = carregar_dados("financas")
        
        # 1. KPIs no Topo
        if not df_fin.empty:
            entradas = df_fin[df_fin["Tipo"] == "Entrada"]["Valor"].sum()
            saidas = df_fin[df_fin["Tipo"] == "Saída"]["Valor"].sum()
            saldo = entradas - saidas
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Entradas (Receita)", f"MT {entradas:,.2f}", delta="Faturado")
            kpi2.metric("Saídas (Despesas)", f"MT {saidas:,.2f}", delta="-Custo", delta_color="inverse")
            kpi3.metric("Fluxo de Caixa", f"MT {saldo:,.2f}", delta="Lucro Líquido", delta_color="normal")
        
        # 2. Gráfico de Tendência
        st.markdown("### 📈 Evolução")
        if not df_fin.empty:
            chart_data = df_fin[["Data", "Valor", "Tipo"]].copy()
            chart_data["Data"] = pd.to_datetime(chart_data["Data"])
            # Ajusta valores de saída para negativo para o gráfico
            chart_data.loc[chart_data["Tipo"] == "Saída", "Valor"] *= -1
            
            st.bar_chart(chart_data, x="Data", y="Valor", color="Tipo", stack=False)

        # 3. Editor de Dados
        st.markdown("### 📝 Lançamentos")
        edited_fin = st.data_editor(
            df_fin,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], required=True),
                "Categoria": st.column_config.SelectboxColumn("Categoria", options=["Serviço", "Produto", "Imposto", "Software", "Pessoal"]),
                "Valor": st.column_config.NumberColumn("Valor", format="%.2f MT"),
                "Status": st.column_config.CheckboxColumn("Pago/Recebido"),
                "Data": st.column_config.DateColumn("Data")
            },
            key="editor_financas"
        )
        
        if st.button("💾 Gravar Financeiro"):
            salvar_dados("financas", edited_fin)
            st.toast("Fluxo de caixa atualizado!", icon="💰")

    # --- OUTROS MÓDULOS (Dashboard, CRM, IA, Eventos) ---
    elif modulo == "📊 Dashboard Geral":
        st.title("📊 Visão Executiva")
        # (Dashboard Simplificado para focar nos novos módulos acima)
        st.info("Utilize os módulos laterais para gestão detalhada.")
        
    elif modulo == "👥 Clientes CRM":
        st.title("👥 Clientes")
        df_cli = carregar_dados("clientes")
        edited_cli = st.data_editor(df_cli, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar Clientes"): salvar_dados("clientes", edited_cli)

    elif modulo == "🧠 Cérebro IA":
        st.title("🧠 Inteligência Artificial")
        # IA Chat Logic (Simplificada)
        prompt = st.chat_input("Pergunte algo...")
        if prompt:
            st.write(f"Usuário: {prompt}")
            st.info("Configure a API Key no código para respostas reais.")

    elif modulo == "🎟️ Eventos QR":
        st.title("🎟️ QR Codes")
        txt = st.text_input("Conteúdo do QR")
        if st.button("Gerar") and QR_AVAILABLE and txt:
            img = qrcode.make(txt)
            buf = io.BytesIO()
            img.save(buf)
            st.image(buf.getvalue(), width=200)