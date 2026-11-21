import json
import unittest
from roteador_ia_isolado import ProvedoresIndisponiveis
from viral_dna_adaptadores_isolados import CAMPOS
from viral_dna_integracao_isolada import gerar_quatro_ideias

IDS = {"video_a", "video_b"}

def ideia(titulo):
    item = {campo: "Texto de teste detalhado suficiente" for campo in CAMPOS}
    item["titulo"] = titulo
    item["frase_thumbnail"] = "Veja isso"
    item["emocao_hipotese"] = "HIPÓTESE: curiosidade editorial"
    item["fontes_ids"] = ["video_a"]
    return item

def lote(numero):
    return json.dumps({"ideias": [
        ideia("Ideia original %d A" % numero),
        ideia("Ideia original %d B" % numero)
    ]}, ensure_ascii=False)

def prompt(numero, quantidade):
    return str(numero)

class Integracao(unittest.TestCase):
    def test_fallback_ate_openrouter_em_dois_lotes(self):
        chamadas = []
        def falha(nome):
            def executar(p, q):
                chamadas.append(nome)
                raise TimeoutError("Falha simulada")
            return executar
        def openrouter(p, q):
            chamadas.append("openrouter")
            return lote(int(p))
        dados, historico = gerar_quatro_ideias({
            "groq": falha("groq"),
            "gemini": falha("gemini"),
            "openrouter": openrouter,
        }, IDS, prompt)
        self.assertEqual(len(dados["ideias"]), 4)
        self.assertEqual(chamadas, ["groq", "gemini", "openrouter"] * 2)
        self.assertEqual([x[1] for x in historico], ["openrouter", "openrouter"])

    def test_groq_sucesso_nao_chama_fallback(self):
        chamadas = []
        def groq(p, q):
            chamadas.append("groq")
            return lote(int(p))
        def proibido(p, q):
            raise AssertionError("Fallback indevido")
        dados, historico = gerar_quatro_ideias({
            "groq": groq, "gemini": proibido, "openrouter": proibido,
        }, IDS, prompt)
        self.assertEqual(len(dados["ideias"]), 4)
        self.assertEqual(chamadas, ["groq", "groq"])

    def test_json_invalido_aciona_proximo(self):
        def groq(p, q):
            return '{"ideias":['
        dados, historico = gerar_quatro_ideias({
            "groq": groq, "gemini": lambda p, q: lote(int(p)),
        }, IDS, prompt)
        self.assertEqual(len(dados["ideias"]), 4)
        self.assertEqual([x[1] for x in historico], ["gemini", "gemini"])

    def test_referencia_inventada_rejeitada(self):
        with self.assertRaises(ProvedoresIndisponiveis):
            gerar_quatro_ideias({"openrouter": lambda p, q: lote(int(p))},
                                {"outro_video"}, prompt)

    def test_titulo_duplicado_entre_lotes_rejeitado(self):
        with self.assertRaises(ValueError):
            gerar_quatro_ideias({"openrouter": lambda p, q: lote(1)}, IDS, prompt)

    def test_falha_total_controlada(self):
        def falha(p, q):
            raise TimeoutError("Falha simulada")
        with self.assertRaises(ProvedoresIndisponiveis):
            gerar_quatro_ideias({"groq": falha, "gemini": falha,
                                 "openrouter": falha}, IDS, prompt)

    def test_referencia_obrigatoria(self):
        with self.assertRaises(ValueError):
            gerar_quatro_ideias({"openrouter": lambda p, q: lote(1)}, set(), prompt)

if __name__ == "__main__":
    unittest.main(verbosity=2)
