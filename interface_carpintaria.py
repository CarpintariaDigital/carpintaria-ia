import streamlit as st
import os
import pandas as pd
import requests
import json
import base64
from datetime import datetime
from bs4 import BeautifulSoup
from smolagents import CodeAgent, LiteLLMModel, tool

# ==========================================
# 💾 BANCO DE DADOS LOCAL (JSON)
# ==========================================
# Simula um banco de dados salvando em arquivos JSON na pasta do projeto
DB_FILES = {
    "projetos": "db_projetos.json",
    "clientes": "db_clientes.json",
    "financas": "db_financas.json"
}

def carregar_dados(tipo):
    arquivo = DB_FILES.get(tipo)
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f:
            return pd.read_json(f)
    else:
        # Estruturas iniciais vazias se o arquivo não existir
        if tipo == "projetos":
            return pd.DataFrame(columns=["ID", "Projeto", "Tipo", "Cliente", "Status", "Prazo", "Valor"])
        elif tipo == "clientes":
            return pd.DataFrame(columns=["ID", "Nome", "Empresa", "Email", "Telefone", "Obs"])
        elif tipo == "financas":
            return pd.DataFrame(columns=["Data", "Descricao", "Categoria", "Tipo", "Valor", "Status"])
        return pd.DataFrame()

def salvar_dados(tipo, df):
    arquivo = DB_FILES.get(tipo)
    df.to_json(arquivo, orient="records", date_format="iso")

# ==========================================
# 📱 CONFIGURAÇÃO VITRINE (DUMBANENGUE)
# ==========================================
MEUS_APPS = [
    {"nome": "Gestão de Estoque", "icone": "📦", "desc": "Controle de madeira e insumos.", "link": "#"},
    {"nome": "Catálogo Digital", "icone": "📖", "desc": "Vitrine de produtos.", "link": "#"},
    {"nome": "Orçamentos", "icone": "💰", "desc": "Calculadora de projetos.", "link": "#"}
]

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Carpintaria OS Pro",
    page_icon="🪚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS PRO (Design System Notion-Like)
st.markdown("""
<style>
    /* Remove cabeçalho padrão */
    header[data-testid="stHeader"] {background-color: transparent;}
    .stApp {background-color: #FFFFFF;} /* Fundo Branco Limpo */
    
    /* Sidebar Escura Profissional */
    section[data-testid="stSidebar"] {
        background-color: #111827; /* Preto Carvão */
    }
    
    /* Títulos e Métricas */
    h1, h2, h3 {font-family: 'Segoe UI', sans-serif; color: #1f2937;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem !important; color: #0ea5e9;}
    
    /* Cards do Dashboard */
    .css-1r6slb0 {border: 1px solid #e5e7eb; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);}
    
    /* Botões de Ação */
    .stButton>button {border-radius: 8px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 SISTEMA DE LOGIN
# ==========================================
def verificar_acesso():
    if "APP_PASSWORD" not in st.secrets: return True
    if "senha_correta" not in st.session_state: st.session_state["senha_correta"] = False
    
    if not st.session_state["senha_correta"]:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.markdown("<br><br><h2 style='text-align:center'>🔒 Acesso Restrito</h2>", unsafe_allow_html=True)
            senha = st.text_input("Senha de Acesso:", type="password")
            if st.button("Entrar no Sistema", use_container_width=True):
                if senha == st.secrets["APP_PASSWORD"]:
                    st.session_state["senha_correta"] = True
                    st.rerun()
                else:
                    st.error("Acesso negado.")
        return False
    return True

# Lógica de bloqueio: Entrada e Dumbanengue são públicos, o resto exige senha.
# Vamos controlar isso dentro da navegação.

# ==========================================
# 🧠 FERRAMENTAS IA
# ==========================================
# (Mantendo as ferramentas da versão anterior para o Chat IA)
try:
    from duckduckgo_search import DDGS
    BUSCA_DISPONIVEL = True
except ImportError: BUSCA_DISPONIVEL = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
except: OLLAMA_AVAILABLE = False

from ferramentas_avancadas import consultar_documentos, salvar_arquivo, ler_arquivo

@tool
def buscar_na_web(termo: str) -> str:
    """Pesquisa no DuckDuckGo (internet). Args: termo: O texto a pesquisar."""
    if not BUSCA_DISPONIVEL: return "Erro: Busca indisponível."
    try:
        results = DDGS().text(termo, max_results=3)
        return str(results) if results else "Nada encontrado."
    except Exception as e: return f"Erro busca: {str(e)}"

# ==========================================
# 🧭 NAVEGAÇÃO
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="background:#1f2937; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h2 style="color:white; margin:0;">🪵 Carpintaria</h2>
        <p style="color:#9ca3af; font-size:0.8rem;">Operating System v4.0</p>
    </div>
    """, unsafe_allow_html=True)

    # Menu Principal
    menu = st.radio("NAVEGAÇÃO", ["🚪 Entrada (Público)", "🛒 Dumbanengue (Vitrine)", "🔒 Acesso Interno"], label_visibility="collapsed")
    
    st.markdown("---")
    
    # Sub-menu se estiver logado
    modulo_interno = "Dashboard"
    if menu == "🔒 Acesso Interno":
        if verificar_acesso():
            st.caption("GESTÃO CORPORATIVA")
            modulo_interno = st.selectbox("Selecione o Módulo:", 
                ["📊 Dashboard Geral", "📂 Projetos & Serviços", "👥 Clientes (CRM)", "💰 Financeiro", "🧠 Escritório IA"]
            )
            
            if st.button("💾 Backup dos Dados"):
                # Cria um JSON com tudo para baixar
                dados_backup = {
                    "clientes": carregar_dados("clientes").to_dict(),
                    "projetos": carregar_dados("projetos").to_dict(),
                    "financas": carregar_dados("financas").to_dict()
                }
                st.download_button("Baixar JSON", data=json.dumps(dados_backup, indent=2), file_name="backup_carpintaria.json")
            
            if st.button("❌ Sair"):
                st.session_state["senha_correta"] = False
                st.rerun()
        else:
            st.stop() # Para a execução da sidebar se não logar

# ==========================================
# 🖥️ PÁGINAS DO SISTEMA
# ==========================================

# --- 1. ENTRADA (LANDING PAGE) ---
if menu == "🚪 Entrada (Público)":
    st.markdown("# Bem-vindo à Carpintaria Digital")
    st.markdown("### Transformando Ideias em Estruturas Digitais.")
    st.image("https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.info("**Consultoria & Tech**\n\nSoluções sob medida para o seu negócio.")
    with c2: st.info("**Produtos Digitais**\n\nAcesse nosso Dumbanengue para ver Apps.")
    with c3: st.info("**Carpintaria IA**\n\nInteligência Artificial aplicada.")

# --- 2. DUMBANENGUE (VITRINE) ---
elif menu == "🛒 Dumbanengue (Vitrine)":
    st.title("🛒 Dumbanengue Digital")
    st.markdown("Nossas soluções prontas para uso.")
    colunas = st.columns(3)
    for index, app in enumerate(MEUS_APPS):
        with colunas[index % 3]:
            with st.container(border=True):
                st.markdown(f"## {app['icone']}")
                st.markdown(f"**{app['nome']}**")
                st.caption(app['desc'])
                st.link_button("Acessar", app['link'], use_container_width=True)

# --- 3. ÁREA INTERNA (ERP + IA) ---
elif menu == "🔒 Acesso Interno":
    
    # --- DASHBOARD GERAL ---
    if modulo_interno == "📊 Dashboard Geral":
        st.title("📊 Visão Geral da Carpintaria")
        
        df_proj = carregar_dados("projetos")
        df_fin = carregar_dados("financas")
        
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Projetos Ativos", len(df_proj[df_proj["Status"] == "Em Andamento"]))
        
        # Cálculo financeiro simples (tratamento de erro se vazio)
        receita = df_fin[df_fin["Tipo"]=="Entrada"]["Valor"].sum() if not df_fin.empty else 0.0
        despesa = df_fin[df_fin["Tipo"]=="Saída"]["Valor"].sum() if not df_fin.empty else 0.0
        
        c2.metric("Receita Total", f"MT {receita:,.2f}")
        c3.metric("Despesas", f"MT {despesa:,.2f}")
        c4.metric("Lucro Líquido", f"MT {receita - despesa:,.2f}", delta_color="normal")
        
        st.markdown("### 📅 Cronograma Recente")
        if not df_proj.empty:
            st.dataframe(df_proj[["Projeto", "Cliente", "Status", "Prazo"]].head(), use_container_width=True)
        else:
            st.info("Nenhum projeto cadastrado.")

    # --- GESTÃO DE PROJETOS (NOTION STYLE) ---
    elif modulo_interno == "📂 Projetos & Serviços":
        st.title("📂 Gestão de Projetos")
        st.caption("Consultoria, Apps, Sites, Treinamentos.")
        
        df = carregar_dados("projetos")
        
        # Edição estilo Notion
        edited_df = st.data_editor(
            df,
            num_rows="dynamic", # Permite adicionar linhas
            column_config={
                "Tipo": st.column_config.SelectboxColumn(
                    "Tipo",
                    options=["App", "Site", "Consultoria", "Mentoria", "Treinamento"],
                    required=True
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Planejamento", "Em Andamento", "Revisão", "Concluído", "Cancelado"],
                    required=True
                ),
                "Valor": st.column_config.NumberColumn(
                    "Valor (MT)", format="MT %.2f"
                ),
                "Prazo": st.column_config.DateColumn("Prazo Final")
            },
            use_container_width=True,
            key="editor_projetos"
        )
        
        # Botão Salvar
        if st.button("💾 Salvar Alterações nos Projetos"):
            salvar_dados("projetos", edited_df)
            st.success("Dados atualizados com sucesso!")

    # --- CRM CLIENTES ---
    elif modulo_interno == "👥 Clientes (CRM)":
        st.title("👥 Carteira de Clientes")
        
        df = carregar_dados("clientes")
        
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            column_config={
                "Email": st.column_config.LinkColumn("Email"),
            },
            use_container_width=True,
            key="editor_clientes"
        )
        
        if st.button("💾 Salvar Clientes"):
            salvar_dados("clientes", edited_df)
            st.success("Lista de clientes salva!")

    # --- FINANCEIRO ---
    elif modulo_interno == "💰 Financeiro":
        st.title("💰 Controle Financeiro")
        
        df = carregar_dados("financas")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                column_config={
                    "Tipo": st.column_config.SelectboxColumn(
                        "Tipo", options=["Entrada", "Saída"], required=True
                    ),
                    "Categoria": st.column_config.SelectboxColumn(
                        "Categoria", 
                        options=["Faturação", "Pagamento", "Serviços", "Impostos", "Infraestrutura", "Softwares"],
                    ),
                    "Status": st.column_config.CheckboxColumn("Pago/Recebido"),
                    "Valor": st.column_config.NumberColumn("Valor (MT)", format="%.2f"),
                    "Data": st.column_config.DateColumn("Data")
                },
                use_container_width=True,
                key="editor_financas"
            )
            
            if st.button("💾 Salvar Finanças"):
                salvar_dados("financas", edited_df)
                st.success("Fluxo de caixa atualizado!")
        
        with col2:
            st.markdown("### Resumo")
            if not edited_df.empty:
                entradas = edited_df[edited_df["Tipo"]=="Entrada"]["Valor"].sum()
                saidas = edited_df[edited_df["Tipo"]=="Saída"]["Valor"].sum()
                st.metric("Total Entradas", f"{entradas:,.2f}")
                st.metric("Total Saídas", f"{saidas:,.2f}")

    # --- ESCRITÓRIO IA (O CHAT) ---
    elif modulo_interno == "🧠 Escritório IA":
        st.title("🧠 Inteligência Artificial")
        st.caption("Seu assistente técnico para código e análise.")
        
        # Lógica do Chat (Simplificada da versão anterior)
        if "messages" not in st.session_state: st.session_state["messages"] = []
        
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
        if prompt := st.chat_input("Pergunte à IA..."):
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            # (Aqui entra a conexão com a IA - mantive simples para caber no código)
            # Você deve configurar a API Key na sidebar ou secrets
            st.warning("⚠️ Configure a API Key na aba Configurações (código anterior) para ativar a resposta.")
            # Para integrar totalmente, copie o bloco `try/except` com CodeAgent da resposta anterior para cá.