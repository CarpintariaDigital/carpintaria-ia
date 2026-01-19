# ferramentas_avancadas.py
import os
from smolagents import tool
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

# --- FERRAMENTA 1: RAG (Bibliotecário) ---
@tool
def consultar_documentos(termo_busca: str) -> str:
    """
    Realiza uma busca semântica (RAG) nos documentos da pasta 'documentos_consultoria'.
    Usa esta ferramenta quando o usuário perguntar sobre manuais, regras ou conteúdo específico da empresa.
    Args:
        termo_busca: O termo para pesquisar no banco de dados.
    """
    pasta_docs = "documentos_consultoria"
    pasta_banco = "banco_vetorial_chroma"
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    if not os.path.exists(pasta_banco) or not os.listdir(pasta_banco):
        # ... (Lógica de indexação igual à anterior) ...
        # Para economizar espaço aqui, assuma a mesma lógica de leitura de PDF/TXT
        return "Banco de dados vazio ou não encontrado. Adicione arquivos."
    
    vector_db = Chroma(persist_directory=pasta_banco, embedding_embeddings=embeddings)
    resultados = vector_db.similarity_search(termo_busca, k=3)

    if not resultados: return "Não encontrei informações relevantes."

    texto = ""
    for doc in resultados:
        texto += f"📄 Fonte: {os.path.basename(doc.metadata.get('source', '?'))}\nConteúdo: {doc.page_content}\n\n"
    return texto

# --- FERRAMENTA 2: CRIAR ARQUIVO (Carpinteiro) ---
@tool
def salvar_arquivo(caminho_arquivo: str, conteudo: str) -> str:
    """
    Cria ou sobrescreve um arquivo com o conteúdo fornecido.
    Use isso para criar scripts Python, relatórios Markdown ou arquivos de texto.
    
    Args:
        caminho_arquivo: O caminho completo e nome do arquivo (ex: 'projetos/script.py').
        conteudo: O texto ou código exato para escrever no arquivo.
    """
    try:
        pasta = os.path.dirname(caminho_arquivo)
        if pasta and not os.path.exists(pasta):
            os.makedirs(pasta)
            
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return f"✅ Arquivo '{caminho_arquivo}' criado com sucesso."
    except Exception as e:
        return f"❌ Erro ao salvar arquivo: {str(e)}"

# --- FERRAMENTA 3: LER ARQUIVO (Auditor) ---
@tool
def ler_arquivo(caminho_arquivo: str) -> str:
    """
    Lê o conteúdo de um arquivo existente.
    Args:
        caminho_arquivo: O caminho do arquivo para ler.
    """
    try:
        if not os.path.exists(caminho_arquivo):
            return "Arquivo não encontrado."
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler: {str(e)}"
