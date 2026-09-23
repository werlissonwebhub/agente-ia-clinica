import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from mangum import Mangum
from contexto_clinica import CLINICA_CONTEXT

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Inicializa o cliente oficial do novo SDK google-genai
client = genai.Client(api_key=api_key) if api_key else genai.Client()

app = FastAPI(
    title="Agente IA Estética Primavera - Vercel",
    description="Backend avançado com suporte a histórico, IA e Webhook do Instagram.",
    version="2.3.0"
)

SYSTEM_PROMPT = f"""
{CLINICA_CONTEXT}

---
DIRETRIZES DE COMPORTAMENTO E PRECISÃO (OBRIGATÓRIO):
1. PRECISÃO ABSOLUTA: Nunca invente valores, datas, procedimentos ou endereços que não constem estritamente no contexto acima.
2. LIMITAÇÃO DE ESCOPO: Se o cliente fizer uma pergunta sobre um assunto totalmente fora do escopo da clínica ou solicitar informações indisponíveis, responda educadamente com o fallback: "Para que eu possa te dar uma informação exata sobre isso, vou te transferir agora mesmo para um de nossos atendentes humanos no WhatsApp oficial."
3. FOCO EM CONVERSÃO: Sempre termine as respostas engajando o cliente.
4. FORMATO WHATSAPP/INSTAGRAM: Utilize formatação limpa (negritos com **, emojis moderados e quebras de linha amigáveis).
"""

class MensagemItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    historico: Optional[List[MensagemItem]] = []
    pergunta_atual: str

@app.post("/chat", summary="Processa o chat com alta precisão")
async def processar_chat(dados: ChatRequest):
    try:
        # Combina o system instruction e a pergunta atual usando o cliente novo
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=dados.pergunta_atual,
            config={
                "system_instruction": SYSTEM_PROMPT
            }
        )
        return {
            "status": "sucesso",
            "resposta_ia": response.text.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar IA: {str(e)}")

@app.get("/webhook")
async def verificar_webhook(request: Request):
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_challenge = params.get("hub.challenge")
    hub_verify_token = params.get("hub.verify_token")
    
    VERIFY_TOKEN = "esteticaprimaveratoken"

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge) if hub_challenge else "OK"
    raise HTTPException(status_code=403, detail="Token de verificação inválido")

@app.post("/webhook")
async def receber_mensagem_instagram(request: Request):
    body = await request.json()
    print("Webhook recebido do Instagram:", body)
    return {"status": "recebido"}

@app.get("/", summary="Health Check")
async def root():
    return {"status": "online", "servico": "Agente IA Estética Primavera na Vercel Rodando!"}

handler = Mangum(app)