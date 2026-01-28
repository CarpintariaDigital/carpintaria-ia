import os
import sqlite3
import json
from datetime import datetime
import uvicorn
import httpx
import asyncio
import subprocess
import tempfile
import numpy as np
import PyPDF2
from io import BytesIO
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
try:
    from smolagents import LiteLLMModel, CodeAgent
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False


# --- CONFIGURAÇÕES ---
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/carpintaria.db"
else:
    DB_PATH = "carpintaria.db"
OLLAMA_URL = "http://localhost:11434"

def init_db():
    """Inicializa a base de dados SQLite se não existir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela CRM
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            empresa TEXT,
            status TEXT DEFAULT 'Lead',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela Projetos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            progresso INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Planeamento',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela Oficina (Documentos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            titulo TEXT NOT NULL,
            conteudo TEXT,
            categoria TEXT,
            metadata TEXT,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela Forja de Conhecimento (RAG)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conhecimento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            conteudo TEXT,
            tipo TEXT, -- 'nota' ou 'manual'
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            embedding BLOB -- Vetor de embeddings (JSON ou binário)
        )
    ''')
    
    # Dados Iniciais (Opcional)
    cursor.execute("SELECT COUNT(*) FROM crm")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO crm (nome, status) VALUES ('Admin Carpintaria', 'Master')")
    
    conn.commit()
    conn.close()

# --- HELPERS ---
async def get_embedding(text: str):
    """Gera embeddings usando o motor Ollama local."""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                },
                timeout=30.0
            )
            if res.status_code == 200:
                return res.json().get("embedding")
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
    return None

def cosine_similarity(v1, v2):
    """Calcula a similaridade de cosseno entre dois vetores."""
    if not v1 or not v2: return 0
    a = np.array(v1)
    b = np.array(v2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0: return 0
    return np.dot(a, b) / (norm_a * norm_b)

init_db()

app = FastAPI(title="Carpintaria OS 2026")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/platforms", StaticFiles(directory="static/platforms"), name="platforms")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
app.mount("/images", StaticFiles(directory="static/images"), name="images")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")

# Data Models
class ChatMessage(BaseModel):
    mensagem: str
    agente: Optional[str] = "consultor"
    model: Optional[str] = "llama3"
    provider: Optional[str] = "gemini"
    api_key: Optional[str] = ""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

class LoginRequest(BaseModel):
    username: Optional[str] = "admin"
    password: str

class TranslationRequest(BaseModel):
    q: str
    source: Optional[str] = "auto"
    target: str

class DocSave(BaseModel):
    filename: Optional[str] = None
    titulo: str
    conteudo: str
    categoria: str
    metadata: Optional[str] = "{}"

# Routes for HTML pages
@app.get("/sw.js")
async def get_sw():
    return FileResponse("static/sw.js", media_type="application/javascript")

@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("static/manifest.json", media_type="application/json")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/Entrada.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/office", response_class=HTMLResponse)
async def read_office():
    with open("static/Escritorio.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/store", response_class=HTMLResponse)
async def read_store():
    if os.path.exists("static/dumbanengue.html"):
        with open("static/dumbanengue.html", "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Store file not found")

@app.get("/studio", response_class=HTMLResponse)
async def read_studio():
    if os.path.exists("static/Studio.html"):
        with open("static/Studio.html", "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Studio file not found")

@app.get("/academy", response_class=HTMLResponse)
async def read_academy():
    if os.path.exists("static/Academy.html"):
        with open("static/Academy.html", "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Academy file not found")

@app.get("/tradutor", response_class=HTMLResponse)
async def read_tradutor():
    if os.path.exists("static/Tradutor.html"):
        with open("static/Tradutor.html", "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Tradutor file not found")

# API Endpoints
@app.post("/api/chat")
async def api_chat(chat: ChatMessage):
    provider = chat.provider.lower()
    model_name = chat.model # Hugging Face é case-sensitive
    
    # Instruções de Sistema específicas
    system_instr = ""
    if chat.agente == "dev":
        system_instr = """És o Carpinteiro Digital (Senior Dev). Tens acesso a FERRAMENTAS:
        - Para executar Python: @@EXECUTE_PYTHON[teu_codigo]@@
        - Para salvar arquivos: @@WRITE_FILE[nome.ext|||conteudo]@@
        - Para ler arquivos: @@READ_FILE[nome.ext]@@
        Sempre que precisares de testar código ou salvar um projeto, usa estes comandos no teu output.
        """

    # RAG Semântico: Se o agente for professor/tutor, procurar no conhecimento
    contexto = ""
    if chat.agente in ["professor", "tutor"]:
        try:
            query_embed = await get_embedding(chat.mensagem)
            if query_embed:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT titulo, conteudo, embedding FROM conhecimento")
                rows = cursor.fetchall()
                
                scored_chunks = []
                for row in rows:
                    if row[2]: # Se houver embedding
                        chunk_embed = json.loads(row[2])
                        score = cosine_similarity(query_embed, chunk_embed)
                        if score > 0.4: # Threshold de relevância
                            scored_chunks.append((score, row[1]))
                
                # Ordenar por score e pegar os melhores
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                if scored_chunks:
                    contexto = "\n\n[CONTEXTO DA FORJA DE CONHECIMENTO]:\n" + "\n---\n".join([c[1] for c in scored_chunks[:3]])
                conn.close()
        except Exception as e:
            print(f"Erro no RAG Semântico: {e}")
            pass

    # Prompt Final com Instruções e Contexto
    prompt_final = chat.mensagem
    if system_instr:
        prompt_final = f"INSTRUTIVO: {system_instr}\n\n{prompt_final}"
    if contexto:
        prompt_final = f"CONTEXTO DA FORJA: {contexto}\n\n{prompt_final}"

    # --- EXECUÇÃO REAL VIA SMOLAGENTS (Se disponível) ---
    if SMOLAGENTS_AVAILABLE:
        try:
            # Configuração do Modelo
            api_key_to_use = chat.api_key if chat.api_key else None
            
            # Se for local, usamos o endpoint do Ollama
            base_url = OLLAMA_URL if provider == "local" else None
            
            # Mapeamento de modelo para LiteLLM (ex: gemini/gemini-1.5-flash)
            model_id = model_name
            if provider == "huggingface":
                if not model_id.startswith("huggingface/"):
                    model_id = f"huggingface/{model_id}"
            elif provider == "openrouter":
                if not model_id.startswith("openrouter/"):
                    model_id = f"openrouter/{model_id}"
            elif provider == "local":
                if not model_id.startswith("ollama/"):
                    model_id = f"ollama/{model_id}"
            elif provider != "auto" and provider != "local" and "/" not in model_id:
                model_id = f"{provider}/{model_id}"

            # Log de Depuração (Ver no server.log)
            print(f"--- IA Request ---")
            print(f"Provider: {provider}, Model: {model_id}")
            print(f"Params: temp={chat.temperature}, tokens={chat.max_tokens}")

            model = LiteLLMModel(
                model_id=model_id,
                api_key=api_key_to_use,
                api_base=base_url,
                temperature=chat.temperature,
                max_tokens=chat.max_tokens if chat.max_tokens > 0 else 2048
            )

            # Para agentes não-dev, usamos uma execução mais leve para evitar erros de 'request body'
            # em modelos sensíveis que não lidam bem com o system prompt do CodeAgent
            if chat.agente != "dev":
                # Simples Chat Completion via LiteLLMModel
                response_text = model(messages=[{"role": "user", "content": prompt_final}])
            else:
                # O Agente pode usar ferramentas (como a mão do carpinteiro)
                agent = CodeAgent(model=model, tools=[], add_base_tools=False)
                response_text = agent.run(prompt_final)
            
            return {
                "resposta": response_text, 
                "agente": chat.agente, 
                "model_used": model_id
            }
        except Exception as e:
            print(f"Erro no Agente: {e}")
            # Tentar fallback direto via litellm se o agente falhar
            try:
                import litellm
                res = litellm.completion(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt_final}],
                    api_key=api_key_to_use,
                    temperature=chat.temperature,
                    max_tokens=chat.max_tokens if chat.max_tokens > 0 else 2048
                )
                response_text = res.choices[0].message.content
                return {
                    "resposta": response_text,
                    "agente": chat.agente,
                    "model_used": model_id,
                    "note": "fallback_applied"
                }
            except Exception as e2:
                print(f"Erro no Fallback: {e2}")
                if provider != "local":
                    return {"resposta": f"❌ Erro na Conexão {provider.upper()}: {str(e2)}. Verifica a tua chave ou o modelo.", "agente": chat.agente}

    # --- FALLBACK PARA LÓGICA ANTIGA (Caso smolagents falhe ou local sem ele) ---
    if provider == "local":
        try:
            async with httpx.AsyncClient() as client:
                ollama_res = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt_final,
                        "stream": False,
                        "options": {
                            "temperature": chat.temperature,
                            "num_predict": chat.max_tokens
                        }
                    },
                    timeout=60.0
                )
                if ollama_res.status_code == 200:
                    response_text = ollama_res.json().get("response", "")
                else:
                    response_text = f"[Ollama Error]: Status {ollama_res.status_code}"
        except Exception as e:
            response_text = f"[Ollama Link Down]: Certifica-te que o Ollama está a correr em {OLLAMA_URL}. Erro: {str(e)}"
    else:
        # Simulação para Cloud (melhorada para simular ferramentas se o agente for dev)
        if chat.agente == "dev" and "olá" not in chat.mensagem.lower():
             response_text = f"[{provider.upper()}]: Entendido, Mestre. Vou preparar o código e usar a ferramenta de escrita.\n@@WRITE_FILE[hello.py|||print('Olá da Carpintaria Digital')]@@\nFicheiro criado com sucesso."
        else:
            response_text = f"[{provider.upper()} - {model_name.upper()}]: Saudações, Mestre. Operando como {chat.agente}."

    return {
        "resposta": response_text, 
        "agente": chat.agente, 
        "model_used": f"{provider}:{model_name}"
    }


@app.post("/api/auth/login")
async def api_login(auth: LoginRequest):
    # Simplificação: Username opcional, Senha '2026', 'carpintaria2026' ou 'admin'
    if (auth.password == "2026" or auth.password == "carpintaria2026" or auth.password == "admin"):
        return {"success": True, "token": "fake-jwt-token"}
    return JSONResponse(status_code=401, content={"success": False, "message": "Senha incorreta"})

@app.get("/api/files/list")
async def list_files(path: str = "."):
    try:
        # Prevent accessing files outside project directory for security
        base_path = os.getcwd()
        target_path = os.path.abspath(os.path.join(base_path, path))
        if not target_path.startswith(base_path):
             raise HTTPException(status_code=403, detail="Forbidden area")
             
        files = []
        for item in os.listdir(target_path):
            full_path = os.path.join(target_path, item)
            files.append({
                "name": item,
                "isDir": os.path.isdir(full_path),
                "size": os.path.getsize(full_path) if os.path.isfile(full_path) else 0
            })
        return {"path": path, "files": files}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/traduzir")
async def api_translate_v2(req: TranslationRequest):
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=req.source, target=req.target)
        translated_text = translator.translate(req.q)
        return {"translatedText": translated_text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/auth/logout")
async def api_logout():
    return {"success": True}

@app.post("/api/crm/novo")
async def api_crm_novo(request: Request):
    data = await request.json()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO crm (nome, email, telefone, empresa, status) VALUES (?, ?, ?, ?, ?)",
        (data.get("nome"), data.get("email"), data.get("telefone"), data.get("empresa"), data.get("tipo", "Lead"))
    )
    conn.commit()
    conn.close()
    return {"success": True}

@app.delete("/api/crm/apagar/{item_id}")
async def api_crm_apagar(item_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM crm WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# Dashboard & KPIs
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM crm")
    total_contactos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM projetos WHERE status != 'Concluído'")
    projetos_ativos = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "projetos_ativos": projetos_ativos,
        "receita_mes": 750000,
        "total_contactos": total_contactos,
        "total_documentos": 12
    }

# CRM
@app.get("/api/crm/listar")
async def list_crm(token: Optional[str] = None):
    return [
        {"id": 1, "nome": "Cliente Exemplo", "tipo": "CLIENTE", "telefone": "+258 84 000 0000"},
        {"id": 2, "nome": "Fornecedor Madeira", "tipo": "FORNECEDOR", "telefone": "+258 82 111 1111"}
    ]

# Documentos / Oficina
@app.get("/api/docs/listar")
async def list_docs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, titulo, categoria FROM documentos ORDER BY atualizado_em DESC")
    docs = [{"filename": r[0], "titulo": r[1], "categoria": r[2]} for r in cursor.fetchall()]
    conn.close()
    if not docs:
        return [
            {"filename": "exemplo.txt", "titulo": "Primeiro Projeto", "categoria": "Geral"}
        ]
    return docs

@app.post("/api/docs/guardar")
async def save_doc(doc: DocSave):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    filename = doc.filename
    if not filename:
        filename = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    
    cursor.execute('''
        INSERT INTO documentos (filename, titulo, conteudo, categoria, metadata, atualizado_em)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(filename) DO UPDATE SET
            titulo=excluded.titulo,
            conteudo=excluded.conteudo,
            categoria=excluded.categoria,
            metadata=excluded.metadata,
            atualizado_em=CURRENT_TIMESTAMP
    ''', (filename, doc.titulo, doc.conteudo, doc.categoria, doc.metadata))
    
    conn.commit()
    conn.close()
    return {"success": True, "filename": filename}

@app.post("/api/docs/ler")
async def read_doc(req: Request):
    data = await req.json()
    filename = data.get("filename")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, conteudo, categoria, metadata FROM documentos WHERE filename = ?", (filename,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        return {
            "titulo": res[0],
            "conteudo": res[1],
            "categoria": res[2],
            "metadata": json.loads(res[3] if res[3] else "{}")
        }
    return {"titulo": "Novo", "conteudo": "", "categoria": "Geral", "metadata": {}}

# Outros Módulos (Txiling, Negocios, Saúde, Academia, Backup, Sync, Faturação)
@app.get("/api/backup/stats")
async def backup_stats(): return {"ultimo_backup": "2026-01-27 10:00", "total_backups": 15}

@app.get("/api/sync/status")
async def sync_status(token: Optional[str] = None): return {"online": True, "last_sync": "Agora"}

@app.get("/api/faturacao/estatisticas")
async def fat_stats(token: Optional[str] = None): return {"receita_mes": "150.000 MT", "receita_total": "1.200.000 MT"}

@app.get("/api/faturacao/listar")
async def fat_list(token: Optional[str] = None): return []

@app.get("/api/txiling/eventos")
async def txiling_list(token: Optional[str] = None): return []

@app.get("/api/negocios/anuncios")
async def negocios_list(token: Optional[str] = None): return []

@app.get("/api/negocios/estatisticas")
async def negocios_stats(token: Optional[str] = None): return {"visualizacoes_total": 5400, "media_visualizacoes": 120}

@app.get("/api/saude/estabelecimentos")
async def saude_list(token: Optional[str] = None): return []

@app.get("/api/saude/estatisticas")
async def saude_stats(token: Optional[str] = None): return {"estabelecimentos_ativos": 45}

@app.get("/api/academia/estatisticas")
async def academia_stats(token: Optional[str] = None): return {"cursos_ativos": 8, "taxa_conclusao": "85%"}

@app.get("/api/academia/cursos")
async def academia_cursos(token: Optional[str] = None): return []

# Forja de Conhecimento (RAG) Endpoints
@app.get("/api/conhecimento/listar")
async def list_conhecimento():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, tipo, criado_em FROM conhecimento ORDER BY criado_em DESC")
    items = [{"id": r[0], "titulo": r[1], "tipo": r[2], "data": r[3]} for r in cursor.fetchall()]
    conn.close()
    return items

@app.post("/api/conhecimento/upload")
async def upload_file_knowledge(file: UploadFile = File(...)):
    filename = file.filename
    content_type = file.content_type
    extracted_text = ""

    try:
        if content_type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(BytesIO(await file.read()))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif "text" in content_type:
            extracted_text = (await file.read()).decode("utf-8")
        else:
            return JSONResponse(status_code=400, content={"error": "Tipo de ficheiro não suportado. Usa PDF ou TXT."})

        if not extracted_text.strip():
            return JSONResponse(status_code=400, content={"error": "Não foi possível extrair texto do ficheiro."})

        # Gera embedding para o conhecimento extraído
        embedding = await get_embedding(extracted_text[:2000]) # Limite para embedding inicial
        embedding_json = json.dumps(embedding) if embedding else None

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conhecimento (titulo, conteudo, tipo, embedding) VALUES (?, ?, ?, ?)",
            (filename, extracted_text, "manual", embedding_json)
        )
        conn.commit()
        conn.close()
        return {"success": True, "filename": filename}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/conhecimento/subir")
async def upload_knowledge(req: Request):
    data = await req.json()
    titulo = data.get("titulo")
    conteudo = data.get("conteudo")
    tipo = data.get("tipo", "manual")
    
    # Gera embedding para o novo conhecimento
    embedding = await get_embedding(conteudo)
    embedding_json = json.dumps(embedding) if embedding else None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conhecimento (titulo, conteudo, tipo, embedding) VALUES (?, ?, ?, ?)",
        (titulo, conteudo, tipo, embedding_json)
    )
    conn.commit()
    conn.close()
    return {"success": True}

@app.delete("/api/conhecimento/apagar/{item_id}")
async def delete_knowledge(item_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conhecimento WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# --- OLLAMA FORGE ENDPOINTS ---
@app.get("/api/ollama/status")
async def ollama_status():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(OLLAMA_URL)
            return {"online": res.status_code == 200}
    except:
        return {"online": False}

@app.get("/api/ollama/models")
async def ollama_models():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            if res.status_code == 200:
                return res.json()
            return {"models": []}
    except:
        return {"models": []}

@app.post("/api/ollama/pull")
async def ollama_pull(req: Request):
    data = await req.json()
    model = data.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Modelo não especificado")
    
    # Executa de forma assíncrona para não bloquear
    async def run_pull():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", f"{OLLAMA_URL}/api/pull", json={"name": model}) as response:
                    async for line in response.aiter_lines():
                        print(f"Ollama Pull [{model}]: {line}")
        except Exception as e:
            print(f"Erro ao baixar modelo {model}: {str(e)}")
    asyncio.create_task(run_pull())
    return {"success": True, "message": f"Download de {model} iniciado em background."}

# --- ATELIÊ DE DESIGN (IMAGE PROXY) ---
@app.post("/api/atelie/roteirizar")
async def api_roteirizar(req: dict):
    conteudo = req.get("conteudo", "")
    provider = req.get("provider", "local").lower()
    model = req.get("model", "tinyllama")
    
    prompt = f"""
    Transforma o seguinte conteúdo numa aula curta e animada (estilo whiteboard).
    Cria um diálogo entre um 'Mestre' (experiente) e um 'Aprendiz' (curioso).
    
    CONTEÚDO: {conteudo}
    
    RESPONDE APENAS EM JSON VÁLIDO no formato:
    {{
      "aula": [
        {{"personagem": "mestre", "texto": "...", "acao": "desenhar_objeto_x"}},
        {{"personagem": "aprendiz", "texto": "...", "acao": "olhar"}},
        ...
      ]
    }}
    Limitado a 5-8 falas.
    """
    
    if provider == "local":
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=60.0
            )
            if res.status_code == 200:
                try:
                    return json.loads(res.json().get("response", "{}"))
                except:
                    return {"aula": [{"personagem": "mestre", "texto": "Erro ao forjar roteiro.", "acao": "triste"}]}
    
    # Mock para cloud se necessário
    return {
        "aula": [
            {"personagem": "mestre", "texto": "Bem-vindo à aula automática, Aprendiz!", "acao": "saudar"},
            {"personagem": "aprendiz", "texto": "Obrigado, Mestre! O que vamos aprender?", "acao": "curioso"},
            {"personagem": "mestre", "texto": "Sobre como a IA poupa o teu trabalho de desenhista.", "acao": "apontar"}
        ]
    }
@app.post("/api/atelie/gerar")
async def atelie_gerar_imagem(req: Request):
    data = await req.json()
    prompt = data.get("prompt", "desenho")
    # Simulação de geração via busca de alta qualidade (Soberania de Conetividade)
    keywords = prompt.replace(" ", ",")
    # Usando Unsplash Source para feedback visual imediato
    url = f"https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&q=80&w=800&q={keywords}"
    # Se o prompt tiver 'cartoon', tentamos algo mais específico
    if 'cartoon' in prompt.lower() or 'desenho' in prompt.lower():
        url = "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?auto=format&fit=crop&q=80&w=800"
    
    return {"success": True, "url": url}

# --- AGENTIAL CODE TOOLS (MÃO DO CARPINTEIRO) ---
@app.post("/api/tools/execute")
async def tool_execute_python(req: Request):
    data = await req.json()
    code = data.get("code")
    if not code:
        return {"error": "Nenhum código fornecido"}
    
    # Execução controlada (Sandbox Simples)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        temp_name = f.name
    
    try:
        result = subprocess.run(
            ["python3", temp_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return {"output": output, "success": result.returncode == 0}
    except subprocess.TimeoutExpired:
        return {"error": "Tempo limite de execução (10s) excedido", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

@app.post("/api/tools/write")
async def tool_write_file(req: Request):
    data = await req.json()
    path = data.get("path")
    content = data.get("content")
    
    # Garante que escreve apenas na pasta de projetos para segurança
    safe_path = os.path.join("projetos", os.path.basename(path))
    os.makedirs("projetos", exist_ok=True)
    
    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": safe_path}
    except Exception as e:
        return {"error": str(e), "success": False}

@app.get("/api/tools/read/{filename}")
async def tool_read_file(filename: str):
    safe_path = os.path.join("projetos", os.path.basename(filename))
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
