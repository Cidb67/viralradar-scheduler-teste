"""Teste isolado de um modelo gratuito específico com vídeos reais."""
import json
import os
import urllib.error
import urllib.request

from viral_dna_4_ideias_youtube_real import coletar, prompt_lote, OPENROUTER
from viral_dna_adaptadores_isolados import extrair_ideias

MODELO = "google/gemma-4-26b-a4b-it:free"

def main():
    chave_y = os.environ.get("YOUTUBE_API_KEY", "").strip()
    chave_o = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not chave_y or not chave_o:
        raise SystemExit("Secrets necessários ausentes.")
    nome, videos = coletar("@manualdomundo", chave_y)
    ids = {v["id"] for v in videos}
    print("Canal:", nome, "| vídeos:", len(videos), "| IDs:", len(ids), flush=True)
    prompt = prompt_lote(nome, videos, 1, [], quantidade=1)
    corpo = {
        "model": MODELO,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_tokens": 3500,
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        OPENROUTER, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + chave_o,
                 "Content-Type": "application/json",
                 "X-Title": "ViralRadar Gemma teste isolado"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=110) as resposta:
            dados = json.load(resposta)
    except urllib.error.HTTPError as erro:
        print("HTTP:", erro.code, flush=True)
        raise SystemExit("Modelo indisponível ou requisição rejeitada; nenhuma resposta aprovada.") from None
    escolha = dados["choices"][0]
    uso = dados.get("usage") or {}
    print("Modelo:", dados.get("model", "não informado"), flush=True)
    print("Parada:", escolha.get("finish_reason"), flush=True)
    print("Tokens saída:", uso.get("completion_tokens", "não informado"), flush=True)
    print("Tokens raciocínio:", (uso.get("completion_tokens_details") or {}).get("reasoning_tokens", "não informado"), flush=True)
    if escolha.get("finish_reason") != "stop":
        raise SystemExit("Resposta truncada: rejeitada.")
    ideias = extrair_ideias(escolha.get("message", {}).get("content"), 1, ids)
    print("SUCESSO: uma ideia completa validada com referência real.", flush=True)
    print("Título:", ideias[0]["titulo"], flush=True)
    print("IDs válidos:", len(ideias[0]["fontes_ids"]), flush=True)
    print("Teste de uma ideia, não comprova qualidade editorial ou quatro ideias.", flush=True)

if __name__ == "__main__":
    main()
