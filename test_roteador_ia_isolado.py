"""Testes isolados, sem rede, credenciais ou dependências externas."""
import unittest
from roteador_ia_isolado import executar, ProvedoresIndisponiveis


def validar(dados):
    return isinstance(dados, dict) and dados.get("ideias") == 4


class TestarRoteador(unittest.TestCase):
    def test_groq_sucesso_nao_chama_outros(self):
        chamadas = []
        def criar(nome, resposta):
            def chamar():
                chamadas.append(nome)
                return resposta
            return chamar
        provedores = {
            "groq": criar("groq", {"ideias": 4}),
            "gemini": criar("gemini", {"ideias": 4}),
            "openrouter": criar("openrouter", {"ideias": 4}),
        }
        resultado = executar(provedores, validar)
        self.assertEqual(resultado.provedor, "groq")
        self.assertEqual(chamadas, ["groq"])

    def test_falha_groq_gemini_sucesso(self):
        chamadas = []
        def groq():
            chamadas.append("groq")
            raise TimeoutError("falha simulada")
        def gemini():
            chamadas.append("gemini")
            return {"ideias": 4}
        def openrouter():
            chamadas.append("openrouter")
            return {"ideias": 4}
        resultado = executar({"groq": groq, "gemini": gemini, "openrouter": openrouter}, validar)
        self.assertEqual(resultado.provedor, "gemini")
        self.assertEqual(chamadas, ["groq", "gemini"])

    def test_duas_falhas_openrouter_sucesso(self):
        chamadas = []
        def falhar(nome):
            def chamar():
                chamadas.append(nome)
                raise ConnectionError("falha simulada")
            return chamar
        def openrouter():
            chamadas.append("openrouter")
            return {"ideias": 4}
        resultado = executar({
            "groq": falhar("groq"),
            "gemini": falhar("gemini"),
            "openrouter": openrouter,
        }, validar)
        self.assertEqual(resultado.provedor, "openrouter")
        self.assertEqual(chamadas, ["groq", "gemini", "openrouter"])
        self.assertEqual(len(resultado.tentativas), 2)

    def test_json_invalido_aciona_fallback(self):
        resultado = executar({
            "groq": lambda: {"ideias": 1},
            "gemini": lambda: {"ideias": 4},
        }, validar)
        self.assertEqual(resultado.provedor, "gemini")
        self.assertEqual(resultado.tentativas[0][1], "RespostaInvalida")

    def test_todos_falham_com_erro_controlado(self):
        def falha():
            raise TimeoutError("segredo que nao deve ser exibido")
        with self.assertRaises(ProvedoresIndisponiveis) as contexto:
            executar({"groq": falha, "gemini": falha, "openrouter": falha}, validar)
        self.assertEqual(len(contexto.exception.tentativas), 3)
        self.assertNotIn("segredo", str(contexto.exception))

    def test_provedor_ausente_pula_sem_interromper(self):
        resultado = executar({"openrouter": lambda: {"ideias": 4}}, validar)
        self.assertEqual(resultado.provedor, "openrouter")
        self.assertEqual(resultado.tentativas[0], ("groq", "nao_configurado"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
