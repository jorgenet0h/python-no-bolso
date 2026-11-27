"""Sandbox de execução de código gerado por modelo (REQ-027).

É uma DEFESA EM CAMADAS, não isolamento perfeito (ver SECURITY.md). Camadas:
 1. Análise estática (AST) antes de executar: lista de permissão de imports; sem `open`, `exec`,
    `eval`, `getattr` etc.; sem acesso a atributos dunder (`__class__`, `__globals__`...).
 2. Processo filho separado (`python -I`), ambiente vazio, diretório temporário vazio, código por stdin.
 3. Timeout com kill do grupo de processos; saída com teto (passou, mata o processo).
 4. Linux: rlimits aplicados pelo próprio filho (memória, CPU, processos, tamanho de arquivo,
    descritores). Em Windows não há rlimit; só valem as camadas 1 a 3.
 5. Sem rede: nenhum módulo de rede está na lista de permissão.
No deploy, rode a API em container sem privilégios, sem segredos montados e com rede fechada.
"""

import ast
import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass

TIMEOUT_PADRAO_S = 2.0
MEMORIA_PADRAO_MB = 128
LIMITE_SAIDA = 1024 * 1024  # stdout; passou disso, o processo é morto
LIMITE_STDERR = 64 * 1024
LIMITE_CODIGO = 100_000

IMPORTS_PERMITIDOS = {"math", "itertools", "collections", "string", "functools", "statistics", "time"}
NOMES_PROIBIDOS = {
    "open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals",
    "vars", "getattr", "setattr", "delattr", "memoryview", "help", "exit", "quit",
}
# Únicos dunders aceitos (classes simples em exercícios); o resto dá acesso a internals.
DUNDERS_PERMITIDOS = {"__init__", "__name__", "__str__", "__repr__", "__len__", "__eq__",
                      "__lt__", "__iter__", "__next__"}

# Roda no filho: aplica os limites ANTES de ler o código; falha de limite derruba o processo.
_BOOT = """
import sys
try:
    import resource
except ImportError:
    resource = None
if resource is not None:
    mem = int(sys.argv[1]) * 1024 * 1024
    cpu = int(sys.argv[2])
    for lim, val in (
        ("RLIMIT_AS", mem), ("RLIMIT_CPU", cpu), ("RLIMIT_FSIZE", 0), ("RLIMIT_CORE", 0),
        ("RLIMIT_NOFILE", 32), ("RLIMIT_NPROC", 1),
    ):
        if hasattr(resource, lim):
            resource.setrlimit(getattr(resource, lim), (val, val))
codigo = sys.stdin.read()
sys.stdin.close()
sys.argv[:] = ["exercicio"]
exec(compile(codigo, "<exercicio>", "exec"), {"__name__": "__main__"})
"""


@dataclass
class Resultado:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    motivo: str | None = None


def barrar(codigo: str) -> str | None:
    """Motivo do bloqueio, ou None se a análise estática aprovar."""
    try:
        arvore = ast.parse(codigo)
    except (SyntaxError, ValueError, RecursionError, MemoryError) as e:
        return f"sintaxe: {getattr(e, 'msg', type(e).__name__)}"
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                if alias.name.split(".")[0] not in IMPORTS_PERMITIDOS:
                    return f"import proibido: {alias.name}"
        elif isinstance(no, ast.ImportFrom):
            if no.level or (no.module or "").split(".")[0] not in IMPORTS_PERMITIDOS:
                return f"import proibido: {no.module}"
        elif isinstance(no, ast.Name):
            if no.id in NOMES_PROIBIDOS or (no.id.startswith("__") and no.id not in DUNDERS_PERMITIDOS):
                return f"nome proibido: {no.id}"
        elif isinstance(no, ast.Attribute):
            if no.attr.startswith("__") and no.attr not in DUNDERS_PERMITIDOS:
                return f"atributo proibido: {no.attr}"
        elif isinstance(no, ast.Constant) and isinstance(no.value, str) and "__" in no.value:
            # Fecha `"{0.__class__}".format(x)` e afins.
            return "texto com '__' proibido"
    return None


def _ler(fluxo, limite: int, partes: list[bytes], estouro: threading.Event | None, proc):
    """Lê o fluxo todo (para o filho não travar), guardando só até `limite` bytes."""
    guardado = 0
    while True:
        bloco = fluxo.read(65536)
        if not bloco:
            return
        if guardado < limite:
            partes.append(bloco[: limite - guardado])
        guardado += len(bloco)
        if estouro is not None and guardado > limite and not estouro.is_set():
            estouro.set()
            _matar(proc)


def _matar(proc: subprocess.Popen) -> None:
    try:
        if sys.platform != "win32":
            import signal

            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _ambiente() -> dict[str, str]:
    if sys.platform == "win32":  # o Python no Windows não inicia sem estas
        return {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "SYSTEMDRIVE"}}
    return {}


def executar(codigo: str, *, timeout_s: float = TIMEOUT_PADRAO_S,
             memoria_mb: int = MEMORIA_PADRAO_MB) -> Resultado:
    if len(codigo) > LIMITE_CODIGO:
        return Resultado(ok=False, motivo="código grande demais")
    motivo = barrar(codigo)
    if motivo:
        return Resultado(ok=False, motivo=motivo)

    with tempfile.TemporaryDirectory() as pasta:
        proc = subprocess.Popen(
            [sys.executable, "-I", "-c", _BOOT, str(int(memoria_mb)), str(int(timeout_s) + 2)],
            cwd=pasta, env=_ambiente(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=sys.platform != "win32",
        )
        saida: list[bytes] = []
        erro: list[bytes] = []
        estouro = threading.Event()
        leitores = [
            threading.Thread(target=_ler, args=(proc.stdout, LIMITE_SAIDA, saida, estouro, proc),
                             daemon=True),
            threading.Thread(target=_ler, args=(proc.stderr, LIMITE_STDERR, erro, None, proc),
                             daemon=True),
        ]
        for t in leitores:
            t.start()
        try:
            proc.stdin.write(codigo.encode("utf-8"))
            proc.stdin.close()
        except OSError:  # o filho morreu antes de ler (limite ou falha de partida)
            pass
        estourou_tempo = False
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            estourou_tempo = True
            _matar(proc)
            proc.wait()
        _matar(proc)  # netos que sobraram, se houver
        for t in leitores:
            t.join(timeout=2)

    stdout = b"".join(saida).decode("utf-8", errors="replace")
    stderr = b"".join(erro).decode("utf-8", errors="replace")
    if estourou_tempo:
        return Resultado(ok=False, stdout=stdout, stderr=stderr, motivo="timeout")
    if estouro.is_set():
        return Resultado(ok=False, stdout=stdout, stderr=stderr, motivo="saída acima do limite")
    if proc.returncode == 0:
        return Resultado(ok=True, stdout=stdout, stderr=stderr)
    if "MemoryError" in stderr:
        return Resultado(ok=False, stdout=stdout, stderr=stderr, motivo="memoria")
    if proc.returncode < 0:  # morto por sinal (SIGXCPU, SIGKILL do limite de CPU ou de memória)
        return Resultado(ok=False, stdout=stdout, stderr=stderr, motivo="timeout/memoria (sinal)")
    return Resultado(ok=False, stdout=stdout, stderr=stderr, motivo="erro de execução")
