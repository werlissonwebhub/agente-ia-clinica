import requests

url = "http://localhost:8000/chat"

# Simulando uma conversa contínua (com histórico)
payload = {
    "historico": [
        {"role": "user", "content": "Olá, quais cursos vocês têm?"},
        {"role": "model", "content": "Olá! Temos o curso de Harmonização Glútea. Deseja saber os valores?"}
    ],
    "pergunta_atual": "Qual é o valor da matrícula e das parcelas dele?"
}

headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    print("Resposta da IA com Histórico:")
    print(response.json())
except Exception as e:
    print("Erro ao conectar:", e)
    