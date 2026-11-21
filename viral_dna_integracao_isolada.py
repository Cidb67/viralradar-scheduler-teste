"""Integração isolada: roteador + adaptadores + lotes de duas ideias.

Não modifica o aplicativo e não chama APIs automaticamente.
"""
import json
from roteador_ia_isolado import executar
from viral_dna_adaptadores_isolados import extrair_ideias


def gerar_quatro_ideias(provedores, ids_permitidos, montar_prompt):
    """Seleciona um provedor por lote, validando antes de aceitar o resultado.

    Cada callable recebe (prompt, quantidade). Em caso de erro ou JSON
    inválido, o roteador tenta o próximo provedor. A seleção é independente
    por lote para não descartar respostas já validadas.
    """
    if not ids_permitidos:
        raise ValueError("Referências reais são obrigatórias.")
    ideias = []
    historico = []
    for numero in (1, 2):
        prompt = montar_prompt(numero, 2)
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt vazio.")
        funcoes = {
            nome: (lambda chamar=chamar: chamar(prompt, 2))
            for nome, chamar in provedores.items()
        }
        resultado = executar(
            funcoes,
            lambda texto: _validar_lote(texto, ids_permitidos),
        )
        lote = extrair_ideias(resultado.dados, 2, ids_permitidos)
        ideias.extend(lote)
        historico.append((numero, resultado.provedor, resultado.tentativas))
    titulos = [ideia["titulo"].strip().casefold() for ideia in ideias]
    if len(ideias) != 4 or len(set(titulos)) != 4:
        raise ValueError("Quatro ideias distintas não foram obtidas.")
    return {"ideias": ideias}, tuple(historico)


def _validar_lote(texto, ids_permitidos):
    try:
        extrair_ideias(texto, 2, ids_permitidos)
        return True
    except (ValueError, TypeError, KeyError):
        return False
