"""Diagnóstico seguro de HTTP 429 no OpenRouter sem chamadas de geração."""
import json
import os
import urllib.error
import urllib.request

chave = os.environ.get("OPENROUTER_API_KEY", "").strip()
if not chave:
    raise SystemExit("OPENROUTER_API_KEY ausente.")
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/key",
    headers={"Authorization": "Bearer " + chave, "Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=25) as resposta:
        dados = json.load(resposta).get("data") or {}
except urllib.error.HTTPError as erro:
    print("HTTP na consulta de limites:", erro.code)
    raise SystemExit("Consulta de limites indisponível.") from None

# Exibir apenas métricas de cota, nunca identificadores ou a chave.
for campo in ("limit", "limit_remaining", "usage", "usage_daily",
              "usage_weekly", "usage_monthly", "is_free_tier"):
    if campo in dados:
        print(campo + ":", dados[campo])
print("Diagnóstico concluído sem solicitar geração de texto.")
