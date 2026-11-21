"""Testes sem API paga, credenciais ou alterações no app."""
import json
import unittest
from viral_dna_adaptadores_isolados import (
    CAMPOS, extrair_ideias, juntar_lotes, chamada_gemini, chamada_groq,
    chamada_openrouter,
)


def ideia(titulo):
    dados = {campo: "Conteúdo de teste com detalhes suficientes" for campo in CAMPOS}
    dados["titulo"] = titulo
    dados["frase_thumbnail"] = "Olhe isto"
    dados["emocao_hipotese"] = "HIPÓTESE: curiosidade visual do público"
    dados["fontes_ids"] = ["id_real_1"]
    return dados


def lote(*titulos):
    return json.dumps({"ideias": [ideia(t) for t in titulos]}, ensure_ascii=False)


class AdaptadoresTestes(unittest.TestCase):
    def test_lote_valido(self):
        self.assertEqual(len(extrair_ideias(lote("Título de teste"), 1, {"id_real_1"})), 1)

    def test_truncado_rejeitado(self):
        with self.assertRaises(ValueError):
            extrair_ideias('{"ideias": [', 1, {"id_real_1"})

    def test_fontes_inventadas_rejeitadas(self):
        with self.assertRaises(ValueError):
            extrair_ideias(lote("Título de teste"), 1, {"outro_id"})

    def test_quatro_ideias_dois_lotes(self):
        dados = juntar_lotes(
            [lote("Primeiro título", "Segundo título"),
             lote("Terceiro título", "Quarto título")], {"id_real_1"})
        self.assertEqual(len(dados["ideias"]), 4)

    def test_duplicidade_entre_lotes(self):
        with self.assertRaises(ValueError):
            juntar_lotes(
                [lote("Título igual", "Segundo título"),
                 lote("Título igual", "Quarto título")], {"id_real_1"})

    def test_groq_injetado(self):
        self.assertEqual(
            chamada_groq(lambda chave, modelo, prompt: "ok", "chave", "modelo", "prompt"),
            "ok")

    def test_gemini_compativel(self):
        class Resposta:
            def json(self):
                return {"candidates": [{"content": {"parts": [{"text": "JSON válido"}]}}]}
        self.assertEqual(chamada_gemini(lambda *args: Resposta(), "chave", "prompt"), "JSON válido")

    def test_openrouter_sem_chave_nao_chama_rede(self):
        with self.assertRaises(ValueError):
            chamada_openrouter("", "modelo", "prompt")


if __name__ == "__main__":
    unittest.main()
