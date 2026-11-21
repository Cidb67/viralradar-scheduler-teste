"""Protótipo isolado: adaptadores de texto e validação de lotes Viral DNA.

Sem imports do app, sem chamadas automáticas e sem modificar produção.
"""
import json
import urllib.error
import urllib.request

CAMPOS = ("titulo", "conceito", "gancho", "frase_thumbnail",
          "visual_thumbnail", "emocao_hipotese", "estrategia_editorial",
          "diferencial_original", "cuidados_verificacao",
          "gatilho_thumbnail", "prompt_thumbnail")


def extrair_ideias(texto, quantidade, ids_permitidos):
    """Valida um lote de 1 ou 2 ideias; o validador final permanece no Viral DNA."""
    if not isinstance(texto, str):
        raise ValueError("Resposta sem texto.")
    bruto = texto.strip()
    if bruto.startswith("```"):
        linhas = bruto.splitlines()
        if len(linhas) < 3 or not linhas[-1].strip().startswith("```"):
            raise ValueError("Resposta truncada.")
        bruto = "\n".join(linhas[1:-1]).strip()
    try:
        objeto = json.loads(bruto)
    except (ValueError, TypeError) as exc:
        raise ValueError("JSON incompleto ou inválido.") from exc
    if not isinstance(objeto, dict) or set(objeto) != {"ideias"}:
        raise ValueError("Estrutura de ideias inválida.")
    ideias = objeto["ideias"]
    if not isinstance(ideias, list) or len(ideias) != quantidade:
        raise ValueError("Quantidade de ideias incorreta.")
    for ideia in ideias:
        if not isinstance(ideia, dict) or set(ideia) != set(CAMPOS) | {"fontes_ids"}:
            raise ValueError("Campos de ideia inválidos.")
        for campo in CAMPOS:
            valor = ideia[campo]
            minimo = 5 if campo in ("titulo", "frase_thumbnail") else 10
            if not isinstance(valor, str) or not minimo <= len(valor.strip()) <= 1000:
                raise ValueError("Campo inválido: " + campo)
        if "hipótese" not in ideia["emocao_hipotese"].casefold():
            raise ValueError("Hipótese não identificada.")
        refs = ideia["fontes_ids"]
        if (not isinstance(refs, list) or not 1 <= len(refs) <= 3
                or len(refs) != len(set(map(str, refs)))
                or any(not isinstance(x, str) or x not in ids_permitidos for x in refs)):
            raise ValueError("Referências inválidas.")
    return ideias


def chamada_openrouter(chave, modelo, prompt, max_tokens=4500, transporte=None):
    """Uma chamada real quando invocada; erros sem exposição de credenciais."""
    if not chave or not modelo:
        raise ValueError("OpenRouter não configurado.")
    if not isinstance(max_tokens, int) or not 512 <= max_tokens <= 8192:
        raise ValueError("Limite de tokens inválido.")
    corpo = {"model": modelo, "messages": [{"role": "user", "content": prompt}],
             "temperature": 0.2, "max_tokens": max_tokens}
    requisicao = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + chave,
                 "Content-Type": "application/json",
                 "X-Title": "ViralRadar DNA teste isolado"},
        method="POST")
    abrir = transporte or urllib.request.urlopen
    try:
        with abrir(requisicao, timeout=90) as resposta:
            dados = json.load(resposta)
    except urllib.error.HTTPError as exc:
        raise ValueError("OpenRouter HTTP " + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("OpenRouter indisponível.") from None
    try:
        escolha = dados["choices"][0]
        if escolha.get("finish_reason") != "stop":
            raise ValueError("OpenRouter encerrou sem concluir a resposta.")
        texto = escolha["message"]["content"]
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("OpenRouter retornou texto vazio.")
        return texto.strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Resposta OpenRouter inválida.") from exc


def chamada_groq(gerador, chave, modelo, prompt):
    """Injeção do adaptador Groq existente, sem copiá-lo ou modificá-lo."""
    return gerador(chave, modelo, prompt)


def chamada_gemini(gerador, chave, prompt, temperatura=0.2):
    """Normaliza o formato compatível Gemini já utilizado pelo aplicativo."""
    resposta = gerador(chave, prompt, temperatura)
    try:
        partes = resposta.json()["candidates"][0]["content"]["parts"]
        texto = "".join(p["text"] for p in partes if isinstance(p.get("text"), str))
        if not texto.strip():
            raise ValueError("Gemini retornou texto vazio.")
        return texto.strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise ValueError("Formato Gemini inválido.") from exc


def juntar_lotes(lotes, ids_permitidos):
    """Agrega 2+2 sem perder a validação e rejeita títulos repetidos."""
    if len(lotes) != 2:
        raise ValueError("São necessários dois lotes.")
    ideias = []
    for texto in lotes:
        ideias.extend(extrair_ideias(texto, 2, ids_permitidos))
    titulos = [i["titulo"].strip().casefold() for i in ideias]
    if len(set(titulos)) != 4:
        raise ValueError("Títulos duplicados entre lotes.")
    return {"ideias": ideias}
