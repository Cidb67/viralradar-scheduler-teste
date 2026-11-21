"""Teste econômico de seleção automática gratuita com dados reais do YouTube."""
import json
import os
import urllib.error
import urllib.request

from viral_dna_4_ideias_youtube_real import coletar, prompt_lote, OPENROUTER
from viral_dna_adaptadores_isolados import extrair_ideias

MODELO = "openrouter/free"


def main():
    chave_y = os.environ.get("YOUTUBE_API_KEY", "").strip()
    chave_o = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not chave_y or not chave_o:
        raise SystemExit("Secrets necessários ausentes.")
    nome, videos = coletar(os.environ.get("CANAL_TESTE", "@manualdomundo"), chave_y)
    ids = {v["id"] for v in videos}
    print("Canal:", nome, "| vídeos reais:", len(videos), "| referências:", len(ids), flush=True)
    prompt = prompt_lote(nome, videos, 1, [], quantidade=1)
    corpo = {"model": MODELO,
             "messages": [{"role": "user", "content": prompt}],
             "max_tokens": 3000, "temperature": 0.2}
    req = urllib.request.Request(
        OPENROUTER, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + chave_o,
                 "Content-Type": "application/json",
                 "X-Title": "ViralRadar teste isolado free router"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=100) as resposta:
            dados = json.load(resposta)
    except urllib.error.HTTPError as erro:
        print("OpenRouter HTTP:", erro.code, flush=True)
        raise SystemExit("Roteador gratuito indisponível ou requisição rejeitada.") from None
    escolha = dados["choices"][0]
    print("Modelo escolhido:", dados.get("model", "não informado"), flush=True)
    print("Parada:", escolha.get("finish_reason"), flush=True)
    uso = dados.get("usage") or {}
    print("Tokens de saída:", uso.get("completion_tokens", "não informado"), flush=True)
    print("Tokens de raciocínio:",
          (uso.get("completion_tokens_details") or {}).get("reasoning_tokens", "não informado"),
          flush=True)
    if escolha.get("finish_reason") != "stop":
        raise SystemExit("Resposta incompleta: não aprovada.")
    texto = escolha.get("message", {}).get("content")
    ideias = extrair_ideias(texto, 1, ids)
    print("SUCESSO: uma ideia completa validada com vídeo real e modelo gratuito selecionado.",
          flush=True)
    print("Título:", ideias[0]["titulo"], flush=True)
    print("Referências válidas:", len(ideias[0]["fontes_ids"]), flush=True)
    print("Teste de uma ideia; ainda não prova quatro ideias ou qualidade editorial.", flush=True)


if __name__ == "__main__":
    main()
