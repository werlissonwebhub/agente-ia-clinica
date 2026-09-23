# main.py
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from mangum import Mangum
from contexto_clinica import CLINICA_CONTEXT

# Carrega as variáveis do ambiente (localmente)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Apenas um aviso caso rode sem env local, mas na Vercel configuraremos nas Environment Variables
    print("Aviso: GEMINI_API_KEY não encontrada no carregamento padrão.")

if api_key:
    genai.configure(api_key=api_key)

app = FastAPI(
    title="Agente IA Estética Primavera - Vercel",
    description="Backend avançado com suporte a histórico, IA e Webhook do Instagram.",
    version="2.1.0"
)

# Configuração do prompt e modelo
SYSTEM_PROMPT = f"""
{CLINICA_CONTEXT}

---
DIRETRIZES DE COMPORTAMENTO E PRECISÃO (OBRIGATÓRIO):
1. PRECISÃO ABSOLUTA: Nunca invente valores, datas, procedimentos ou endereços que não constem estritamente no contexto acima.
2. LIMITAÇÃO DE ESCOPO: Se o cliente fizer uma pergunta sobre um assunto totalmente fora do escopo da clínica ou solicitar informações indisponíveis, responda educadamente com o fallback: "Para que eu possa te dar uma informação exata sobre isso, vou te transferir agora mesmo para um de nossos atendentes humanos no WhatsApp oficial."
3. FOCO EM CONVERSÃO: Sempre termine as respostas engajando o cliente (ex: perguntando se ele prefere atendimento no período da manhã ou tarde, ou direcionando para o link do WhatsApp).
4. FORMATO WHATSAPP/INSTAGRAM: Utilize formatação limpa (negritos com **, emojis moderados e quebras de linha amigáveis).
"""

model = genai.GenerativeModel(
    model_name="gemini-3.6-flash",
    system_instruction=SYSTEM_PROMPT
)

class MensagemItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    historico: Optional[List[MensagemItem]] = []
    pergunta_atual: str

@app.post("/chat", summary="Processa o chat com histórico e alta precisão")
async def processar_chat(dados: ChatRequest):
    try:
        # Garante a chave ativa caso venha da variável de ambiente da Vercel
        current_key = os.getenv("GEMINI_API_KEY")
        if current_key:
            genai.configure(api_key=current_key)

        chat_history = []
        for msg in dados.historico:
            role_gemini = "user" if msg.role == "user" else "model"
            chat_history.append({
                "role": role_gemini,
                "parts": [msg.content]
            })

        chat_sessao = model.start_chat(history=chat_history)
        response = chat_sessao.send_message(dados.pergunta_atual)

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
    
    # Token fixo direto para garantir validação
    VERIFY_TOKEN = "esteticaprimaveratoken"

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge) if hub_challenge else "OK"
    raise HTTPException(status_code=403, detail="Token de verificação inválido")

@app.post("/webhook")
async def receber_mensagem_instagram(request: Request):
    body = await request.json()
    # Aqui vamos processar a mensagem que chega do Instagram Direct e mandar para o Gemini
    print("Webhook recebido do Instagram:", body)
    return {"status": "recebido"}

@app.get("/", summary="Health Check")
async def root():
    return {"status": "online", "servico": "Agente IA Estética Primavera na Vercel Rodando!"}

# Adaptador Mangum para a Vercel ler o FastAPI como função serverless
handler = Mangum(app)