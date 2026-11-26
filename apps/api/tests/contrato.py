"""Adaptador entre os testes e a implementação.

Os testes saem da SPEC e de docs/arquitetura.md, nunca do código. Tudo o que a spec não fixa
(nomes de módulo, funções, formato de payload) está concentrado AQUI e documentado em
docs/spec-gaps.md como "contrato proposto". Quando a implementação divergir, só este arquivo
muda, e a divergência vira decisão registrada, não ajuste silencioso de teste.

Falha por requisito ainda não implementado sempre começa com o prefixo NAO-IMPLEMENTADO.
Isso separa a falha de categoria A (falta implementar) da B (erro do próprio teste).
"""

from __future__ import annotations

import importlib
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

import pytest

PREFIXO = "NAO-IMPLEMENTADO"
HEADER_DEVICE = "X-Device-Id"

TIPOS = ["prever_saida", "completar_lacuna", "ordenar_linhas", "achar_bug"]
NIVEIS = ["iniciante", "intermediario", "avancado"]
TEMAS = ["variaveis", "condicionais", "lacos", "listas", "funcoes", "strings", "dicionarios", "erros"]

# Código e status HTTP de cada erro (D-14). Toda resposta de erro é {"code", "message"}.
ERROS = {
    "SEM_EXERCICIO": 404,
    "RESPOSTA_INVALIDA": 422,
    "FILTRO_INVALIDO": 422,
    "ENUM_INVALIDO": 422,
    "DEVICE_INVALIDO": 400,
    "LIMITE_EXCEDIDO": 429,
    "INDISPONIVEL": 503,
    "ERRO_INTERNO": 500,
    "NAO_ENCONTRADO": 404,
    "METODO_NAO_PERMITIDO": 405,
}

# Campos que entregariam a resposta ao cliente (REQ-004).
CAMPOS_GABARITO = ["gabarito", "saida_esperada", "explicacao", "explicacoes_por_opcao"]


def nao_implementado(req: str, detalhe: str) -> None:
    pytest.fail(f"{PREFIXO} [{req}] {detalhe} (contrato proposto em docs/spec-gaps.md)", pytrace=False)


def carregar(modulo: str, req: str):
    """Importa um módulo da API. Ausência do módulo alvo é categoria A; qualquer outro
    ImportError (dependência quebrada, erro de sintaxe dentro do módulo) propaga como B."""
    try:
        return importlib.import_module(modulo)
    except ModuleNotFoundError as e:
        if e.name and (modulo == e.name or modulo.startswith(e.name + ".")):
            nao_implementado(req, f"módulo '{modulo}' não existe")
        raise


def atributo(modulo: str, nome: str, req: str):
    mod = carregar(modulo, req)
    if not hasattr(mod, nome):
        nao_implementado(req, f"'{modulo}.{nome}' não existe")
    return getattr(mod, nome)


def novo_device() -> str:
    return str(uuid.uuid4())


def chamar(client, metodo: str, rota: str, req: str, device: str | None = None, **kw):
    """Chama a API. 404/405 do roteador (sem corpo {code, message}) = rota não implementada."""
    headers = dict(kw.pop("headers", {}) or {})
    if device is not None:
        headers[HEADER_DEVICE] = device
    resp = client.request(metodo, rota, headers=headers, **kw)
    if resp.status_code in (404, 405):
        try:
            corpo = resp.json()
        except ValueError:
            corpo = {}
        if not (isinstance(corpo, dict) and "code" in corpo):
            nao_implementado(req, f"rota {metodo} {rota} não existe (HTTP {resp.status_code})")
    return resp


def checar_erro(resp, code: str) -> None:
    """Confere código, status HTTP e formato exato {code, message} de uma resposta de erro."""
    corpo = resp.json()
    assert corpo.get("code") == code, f"esperava {code}, veio {corpo}"
    assert resp.status_code == ERROS[code], f"{code}: HTTP {resp.status_code}"
    assert {"code", "message"} <= set(corpo)
    assert corpo["message"]


# ---------------------------------------------------------------- exercícios de exemplo

BASES = {
    "prever_saida": {
        "enunciado": "O que o código imprime?",
        "codigo": "x = 2\ny = 3\nprint(x + y)",
        "opcoes": ["4", "5", "6", "23"], "gabarito": [1], "saida_esperada": "5\n",
    },
    "completar_lacuna": {
        "enunciado": "Complete a lacuna para imprimir 10.",
        "codigo": "total = 4 + ___\nprint(total)",
        "opcoes": ["5", "6", "7", "8"], "gabarito": [1], "saida_esperada": "10\n",
    },
    "ordenar_linhas": {
        "enunciado": "Ordene as linhas para imprimir 3.",
        "codigo": "",
        "opcoes": ["print(a + b)", "a = 1", "b = 2"], "gabarito": [1, 2, 0], "saida_esperada": "3\n",
    },
    "achar_bug": {
        "enunciado": "Qual linha tem o bug?",
        "codigo": "n = 5\nsoma = 0\nfor i in range(n):\n    soma += i\nprint(soma)",
        "opcoes": ["n = 5", "soma = 0", "for i in range(n):", "soma += i"],
        "gabarito": [2], "saida_esperada": "15\n",
        # A saída afirmada é a da versão corrigida (D-09).
        "codigo_corrigido": "n = 5\nsoma = 0\nfor i in range(1, n + 1):\n    soma += i\nprint(soma)",
    },
}


def exercicio_exemplo(tipo: str = "prever_saida", nivel: str = "iniciante",
                      tema: str = "variaveis", **extra) -> dict:
    """Exercício válido segundo o modelo de dados de docs/arquitetura.md.
    `gabarito` e `resposta` são sempre listas de índices."""
    base = BASES.get(tipo, BASES["prever_saida"])
    ex = {"tipo": tipo, "nivel": nivel, "tema": tema, **base}
    ex["explicacao"] = "Explicação genérica armazenada do exercício."
    ex["explicacoes_por_opcao"] = {
        str(i): f"Explicação específica da opção {i}." for i in range(len(ex["opcoes"]))
    }
    ex.update(extra)
    return ex


def semear_exercicio(req: str, **campos) -> dict:
    """Grava um exercício validado no banco de teste e devolve o dict com `id`.
    Contrato: app.db.SessionLocal e app.models.Exercicio com as colunas do modelo de dados."""
    ex = exercicio_exemplo(**campos)
    db = carregar("app.db", req)
    models = carregar("app.models", req)
    if not hasattr(db, "SessionLocal") or not hasattr(models, "Exercicio"):
        nao_implementado(req, "app.db.SessionLocal / app.models.Exercicio não existem")
    ex_id = str(uuid.uuid4())
    with db.SessionLocal() as sessao:
        sessao.add(models.Exercicio(id=uuid.UUID(ex_id), status="validado", **ex))
        sessao.commit()
    return {**ex, "id": ex_id}


def contar(modelo: str, req: str, **filtros) -> int:
    db = carregar("app.db", req)
    models = carregar("app.models", req)
    if not hasattr(models, modelo):
        nao_implementado(req, f"app.models.{modelo} não existe")
    cls = getattr(models, modelo)
    with db.SessionLocal() as sessao:
        q = sessao.query(cls)
        for k, v in filtros.items():
            q = q.filter(getattr(cls, k) == v)
        return q.count()


def listar(modelo: str, req: str, **filtros) -> list:
    db = carregar("app.db", req)
    models = carregar("app.models", req)
    if not hasattr(models, modelo):
        nao_implementado(req, f"app.models.{modelo} não existe")
    cls = getattr(models, modelo)
    with db.SessionLocal() as sessao:
        q = sessao.query(cls)
        for k, v in filtros.items():
            q = q.filter(getattr(cls, k) == v)
        return list(q.all())


# ---------------------------------------------------------------- dublês para o agente

@dataclass
class ResultadoExecucao:
    ok: bool = True
    stdout: str = ""
    stderr: str = ""
    motivo: str | None = None


class ExecutorFalso:
    """Executor de código injetável. Registra chamadas; nunca executa nada de verdade."""

    def __init__(self, stdout: str = "", ok: bool = True, por_codigo: dict | None = None):
        self.chamadas: list[str] = []
        self.stdout, self.ok, self.por_codigo = stdout, ok, por_codigo or {}

    def __call__(self, codigo: str, **kw) -> ResultadoExecucao:
        self.chamadas.append(codigo)
        if codigo in self.por_codigo:
            return self.por_codigo[codigo]
        return ResultadoExecucao(ok=self.ok, stdout=self.stdout)


@dataclass
class ProvedorFalso:
    """Provedor de modelo injetável. `respostas` é a fila de respostas; uma exceção é levantada.
    Resposta de tool: {"tool": "executar_python", "args": {"codigo": "..."}}.
    Resposta final: {"final": {<exercício>}}."""

    respostas: list = field(default_factory=list)
    nome: str = "falso"
    modelo: str = "falso-1"
    chamadas: list = field(default_factory=list)

    def completar(self, mensagens, tools=None, **kw):
        self.chamadas.append({"mensagens": mensagens, "tools": tools, **kw})
        if not self.respostas:
            raise AssertionError("ProvedorFalso sem respostas na fila")
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def texto_enviado(self) -> str:
        return " ".join(str(c["mensagens"]) for c in self.chamadas)


def resposta_final(ex: dict | None = None) -> dict:
    return {"final": ex or exercicio_exemplo()}


def resposta_tool(codigo: str = "print(5)") -> dict:
    return {"tool": "executar_python", "args": {"codigo": codigo}}


def ambiente_de_teste_ok() -> bool:
    return bool(os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL"))


# ---------------------------------------------------------------- GET /health (REQ-044)
# Formato decidido em DISP-001: a spec vence; REQ-044 pede status da API e do banco.
HEALTH_OK = {"status": "ok", "db": "ok"}
HEALTH_DEGRADADO = {"status": "degraded", "db": "erro"}


@contextmanager
def banco_fora(app, req: str):
    """Simula banco inacessível sobrescrevendo a dependência app.db.get_session."""
    db = carregar("app.db", req)
    if not hasattr(db, "get_session"):
        nao_implementado(req, "app.db.get_session (dependência de sessão) não existe")

    def sem_banco():
        raise ConnectionError("banco fora do ar")
        yield  # pragma: no cover

    app.dependency_overrides[db.get_session] = sem_banco
    try:
        yield
    finally:
        app.dependency_overrides.pop(db.get_session, None)
