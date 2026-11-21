"""Consulta pública de capacidades de modelos OpenRouter; não gera texto."""
import json
import urllib.request

URL = "https://openrouter.ai/api/v1/models"
MODELO = "nvidia/nemotron-3.5-super-vl:free"
with urllib.request.urlopen(URL, timeout=25) as resp:
    modelos = json.load(resp).get("data", [])
alvo = next((m for m in modelos if m.get("id") == MODELO), None)
if alvo is None:
    raise SystemExit("Modelo não encontrado no catálogo público.")
print("Modelo:", alvo["id"])
print("Parâmetros suportados:", alvo.get("supported_parameters", []))
print("Saída máxima:", (alvo.get("top_provider") or {}).get("max_completion_tokens", "não informado"))
print("Custo de entrada:", (alvo.get("pricing") or {}).get("prompt", "não informado"))
print("Custo de saída:", (alvo.get("pricing") or {}).get("completion", "não informado"))
print("Possui parâmetro reasoning:", "reasoning" in alvo.get("supported_parameters", []))
print("Possui parâmetro include_reasoning:", "include_reasoning" in alvo.get("supported_parameters", []))
print("Consulta concluída sem geração, sem chave e sem custo de tokens.")
