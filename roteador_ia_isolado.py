"""Roteador experimental de provedores de IA. Nenhuma API é chamada por este módulo."""
from dataclasses import dataclass
from typing import Any, Callable, Mapping


class RespostaInvalida(ValueError):
    """O provedor respondeu, mas o resultado não passou na validação."""


class ProvedoresIndisponiveis(RuntimeError):
    def __init__(self, tentativas):
        self.tentativas = tuple(tentativas)
        super().__init__("Nenhum provedor retornou uma resposta válida.")


@dataclass(frozen=True)
class Resultado:
    provedor: str
    dados: Any
    tentativas: tuple


def executar(
    provedores: Mapping[str, Callable[[], Any]],
    validar: Callable[[Any], bool],
    ordem=("groq", "gemini", "openrouter"),
) -> Resultado:
    """Tenta provedores em ordem. Cada callable deve fazer no máximo uma chamada.

    Exceções são registradas somente pelo tipo, para evitar expor chaves,
    prompts e dados sensíveis. A aplicação decide como adaptar cada provedor.
    """
    tentativas = []
    for nome in ordem:
        chamar = provedores.get(nome)
        if chamar is None:
            tentativas.append((nome, "nao_configurado"))
            continue
        try:
            dados = chamar()
            if not validar(dados):
                raise RespostaInvalida("Estrutura rejeitada pelo validador.")
            return Resultado(nome, dados, tuple(tentativas))
        except Exception as erro:
            tentativas.append((nome, type(erro).__name__))
    raise ProvedoresIndisponiveis(tentativas)
