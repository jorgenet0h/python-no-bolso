"""Executor de código dos evals.

NÃO é o sandbox de produção (REQ-027 é do app). É uma guarda de melhor esforço para rodar, na
máquina de quem desenvolve, código escrito por modelo: (1) análise estática barra import fora de
uma lista curta, builtins perigosos e acesso a atributos dunder; (2) processo filho isolado (-I),
sem variáveis de ambiente, em diretório temporário vazio, com timeout. Sem limite de memória no
Windows. Não use para código de usuário.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass

IMPORTS_PERMITIDOS = {"math", "itertools", "collections", "string", "functools", "statistics"}
NOMES_PROIBIDOS = {
    "open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals",
    "vars", "getattr", "setattr", "delattr", "memoryview", "help", "exit", "quit",
}
LIMITE_SAIDA = 64 * 1024


@dataclass
class Resultado:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    motivo: str | None = None


def barrar(codigo: str) -> str | None:
    """Devolve o motivo do bloqueio, ou None se a análise estática aprovar."""
    try:
        arvore = ast.parse(codigo)
    except SyntaxError as e:
        return f"sintaxe: {e.msg}"
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                if alias.name.split(".")[0] not in IMPORTS_PERMITIDOS:
                    return f"import proibido: {alias.name}"
        elif isinstance(no, ast.ImportFrom):
            if no.level or (no.module or "").split(".")[0] not in IMPORTS_PERMITIDOS:
                return f"import proibido: {no.module}"
        elif isinstance(no, ast.Name) and (no.id in NOMES_PROIBIDOS or no.id.startswith("__")):
            return f"nome proibido: {no.id}"
        elif isinstance(no, ast.Attribute) and no.attr.startswith("__"):
            return f"atributo proibido: {no.attr}"
    return None


def executar(codigo: str, timeout_s: float = 3.0) -> Resultado:
    motivo = barrar(codigo)
    if motivo:
        return Resultado(ok=False, motivo=motivo)
    env = {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "SYSTEMDRIVE"}}
    with tempfile.TemporaryDirectory() as pasta:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", codigo], cwd=pasta, env=env, capture_output=True,
                text=True, timeout=timeout_s, check=False,
            )
        except subprocess.TimeoutExpired:
            return Resultado(ok=False, motivo="timeout")
    return Resultado(
        ok=proc.returncode == 0,
        stdout=proc.stdout[:LIMITE_SAIDA],
        stderr=proc.stderr[:LIMITE_SAIDA],
        motivo=None if proc.returncode == 0 else "erro de execução",
    )
