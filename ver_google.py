import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega ambiente
load_dotenv()

# Pega a chave ou pede na hora
chave = os.getenv("GEMINI_API_KEY")
if not chave:
    chave = input("Cole sua chave API aqui (AIza...): ").strip()

genai.configure(api_key=chave)

print("\n🔍 Listando modelos disponíveis para sua conta...\n")

try:
    for m in genai.list_models():
        # Filtra apenas modelos que geram texto/chat
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Modelo Disponível: {m.name}")
            
except Exception as e:
    print(f"❌ Erro: {e}")
