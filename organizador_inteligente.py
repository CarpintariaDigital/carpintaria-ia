import os
import shutil
import ollama
from pypdf import PdfReader

# --- CONFIGURAÇÕES ---
PASTA_ORIGEM = "documentos_consultoria"  # Onde estão os arquivos bagunçados
MODELO_INTELIGENTE = "qwen2.5-coder:3b"  # O modelo que vai ler e classificar

# Lista de áreas permitidas (para ele não inventar pastas malucas)
AREAS_CONHECIMENTO = [
    "Desenvolvimento Web", 
    "Marketing e Vendas", 
    "Gestão Financeira", 
    "Recursos Humanos", 
    "Jurídico", 
    "Outros"
]

def extrair_texto_inicio(caminho_arquivo):
    """Lê os primeiros 1000 caracteres do arquivo para a IA analisar"""
    texto = ""
    try:
        if caminho_arquivo.endswith('.pdf'):
            reader = PdfReader(caminho_arquivo)
            # Tenta ler a primeira página
            if len(reader.pages) > 0:
                texto = reader.pages[0].extract_text()
        elif caminho_arquivo.endswith('.txt') or caminho_arquivo.endswith('.md'):
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                texto = f.read()
    except Exception as e:
        print(f"⚠️ Erro ao ler {caminho_arquivo}: {e}")
    
    return texto[:1000] # Retorna só o começo para ser rápido

def classificar_documento(nome_arquivo, texto_conteudo):
    """Pergunta para o Qwen qual é a categoria do arquivo"""
    
    prompt = f"""
    Você é um bibliotecário especialista. Analise o nome do arquivo e o trecho do conteúdo abaixo.
    Classifique este documento em EXATAMENTE UMA das seguintes categorias: 
    {AREAS_CONHECIMENTO}

    Responda APENAS com o nome da categoria, sem explicações.
    
    Arquivo: {nome_arquivo}
    Conteúdo: {texto_conteudo}
    """

    try:
        response = ollama.chat(model=MODELO_INTELIGENTE, messages=[
            {'role': 'user', 'content': prompt},
        ])
        
        categoria = response['message']['content'].strip()
        
        # Limpeza básica caso a IA responda com ponto final ou aspas
        for char in ['.', '"', "'", '*']:
            categoria = categoria.replace(char, '')
            
        # Segurança: Se a IA inventar uma categoria, joga em "Outros"
        match_encontrado = False
        for area in AREAS_CONHECIMENTO:
            if area.lower() in categoria.lower():
                return area
                
        return "Outros"
        
    except Exception as e:
        print(f"Erro na IA: {e}")
        return "Outros"

def main():
    print(f"📂 Iniciando organização da pasta: {PASTA_ORIGEM}...")
    
    # Verifica se a pasta existe
    if not os.path.exists(PASTA_ORIGEM):
        print("❌ A pasta de origem não existe.")
        return

    arquivos = [f for f in os.listdir(PASTA_ORIGEM) if os.path.isfile(os.path.join(PASTA_ORIGEM, f))]
    
    if not arquivos:
        print("A pasta está vazia ou todos os arquivos já foram organizados (estão em subpastas).")
        return

    print(f"Encontrei {len(arquivos)} arquivos para analisar.\n")

    for arquivo in arquivos:
        caminho_completo = os.path.join(PASTA_ORIGEM, arquivo)
        
        # 1. Extrair Texto
        print(f"📖 Lendo: {arquivo}...", end="\r")
        conteudo = extrair_texto_inicio(caminho_completo)
        
        if not conteudo:
            print(f"⏩ Pulando {arquivo} (vazio ou ilegível)")
            continue

        # 2. Classificar com IA
        categoria = classificar_documento(arquivo, conteudo)
        print(f"🧠 Classificado como: [{categoria}] -> {arquivo}")
        
        # 3. Mover Arquivo
        pasta_destino = os.path.join(PASTA_ORIGEM, categoria)
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            
        shutil.move(caminho_completo, os.path.join(pasta_destino, arquivo))

    print("\n✅ Organização Concluída!")

if __name__ == "__main__":
    main()
