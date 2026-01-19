# ferramentas_avancadas.py
import os
from smolagents import tool
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- IMPORTAÇÃO INTELIGENTE DE EMBEDDINGS ---
# Tenta usar Gemini na nuvem, senão usa Ollama local
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    # Verifica se tem a chave do Google configurada
    if "GEMINI_API_KEY" in os.environ:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        print("✅ Usando Embeddings do Google Gemini (Nuvem)")
    else:
        raise ImportError("Sem chave Gemini, tentando Ollama...")
except (ImportError, Exception):
    try:
        from langchain_ollama import OllamaEmbeddings
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        print("✅ Usando Embeddings do Ollama (Local)")
    except:
        # Fallback de emergência para não quebrar o import
        embeddings = None
        print("⚠️ Nenhum modelo de embedding encontrado.")

# Configuração do Banco Vetorial
PASTA_BANCO = "banco_vetorial_chroma"

@tool
def consultar_documentos(pergunta: str) -> str:
    """
    Pesquisa nos documentos PDF da empresa (manual, tabelas, normas) para responder perguntas técnicas.
    Use isso sempre que a pergunta for sobre processos internos, preços ou normas da carpintaria.
    
    Args:
        pergunta: O texto da pergunta ou termo de busca.
    """
    if embeddings is None:
        return "Erro: Sistema de leitura de documentos não está ativo na nuvem (Faltam configurações de Embedding)."

    try:
        # Conecta ao banco
        vectorstore = Chroma(
            persist_directory=PASTA_BANCO,
            embedding_function=embeddings
        )
        
        # Faz a busca (Pega os 3 trechos mais relevantes)
        docs = vectorstore.similarity_search(pergunta, k=3)
        
        if not docs:
            return "Não encontrei informações relevantes nos documentos internos."
            
        # Junta os textos encontrados
        contexto = "\n\n".join([d.page_content for d in docs])
        return f"Informações encontradas nos documentos:\n{contexto}"
        
    except Exception as e:
        return f"Erro ao consultar documentos: {str(e)}"

@tool
def salvar_arquivo(nome_arquivo: str, conteudo: str) -> str:
    """
    Salva um código, texto ou lista em um arquivo na pasta de trabalho.
    
    Args:
        nome_arquivo: Nome do arquivo (ex: 'orcamento.txt', 'corte.py').
        conteudo: O texto completo para salvar dentro do arquivo.
    """
    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return f"Arquivo '{nome_arquivo}' salvo com sucesso!"
    except Exception as e:
        return f"Erro ao salvar arquivo: {str(e)}"

@tool
def ler_arquivo(nome_arquivo: str) -> str:
    """
    Lê o conteúdo de um arquivo existente.
    
    Args:
        nome_arquivo: Nome do arquivo para ler.
    """
    try:
        if not os.path.exists(nome_arquivo):
            return "Arquivo não encontrado."
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"

# Função auxiliar para processar PDFs novos (Só roda se chamado manualmente)
def processar_pdfs_iniciais():
    if not os.path.exists("documentos_consultoria"):
        os.makedirs("documentos_consultoria")
        return
        
    arquivos = [f for f in os.listdir("documentos_consultoria") if f.endswith('.pdf')]
    if not arquivos:
        return

    print("🔄 Processando documentos iniciais...")
    docs_totais = []
    for arq in arquivos:
        loader = PDFPlumberLoader(os.path.join("documentos_consultoria", arq))
        docs_totais.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs_totais)
    
    Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=PASTA_BANCO
    )
    print("✅ Banco Vetorial Atualizado!")
