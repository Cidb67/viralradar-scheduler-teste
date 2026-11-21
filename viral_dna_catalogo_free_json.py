"""Inspeciona modelos gratuitos OpenRouter sem usar chaves ou gerar tokens."""
import json
import urllib.request

URL = "https://openrouter.ai/api/v1/models"
with urllib.request.urlopen(URL, timeout=30) as response:
    modelos = json.load(response).get("data", [])

candidatos = []
for modelo in modelos:
    identificador = modelo.get("id", "")
    preco = modelo.get("pricing") or {}
    if not identificador.endswith(":free"):
        continue
    parametros = set(modelo.get("supported_parameters") or [])
    limite = (modelo.get("top_provider") or {}).get("max_completion_tokens")
    try:
        limite = int(limite or 0)
    except (TypeError, ValueError):
        limite = 0
    candidatos.append({
        "id": identificador,
        "contexto": modelo.get("context_length"),
        "saida_max": limite,
        "json": "response_format" in parametros,
        "structured": "structured_outputs" in parametros,
        "reasoning": "reasoning" in parametros,
        "include_reasoning": "include_reasoning" in parametros,
        "custo_entrada": preco.get("prompt"),
        "custo_saida": preco.get("completion"),
    })
candidatos.sort(key=lambda x: (x["json"] or x["structured"], not x["reasoning"], x["saida_max"]), reverse=True)
print("Modelos :free encontrados:", len(candidatos))
print("Candidatos (metadados; nenhuma garantia de disponibilidade ou qualidade):")
for item in candidatos[:35]:
    print(json.dumps(item, ensure_ascii=False))
print("Nenhuma chamada de geração realizada.")
