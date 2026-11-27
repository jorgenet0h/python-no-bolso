"""REQ-027 adversarial: código gerado por modelo é hostil por padrão.

Contrato do sandbox (docs/spec-gaps.md): app.sandbox.executar(codigo, *, timeout_s, memoria_mb)
devolve objeto com ok, stdout, stderr, motivo. Os asserts são sobre EFEITO observável (canários),
não sobre como o sandbox bloqueia. Memória e fork exigem rlimit, só em Linux (CI/container).
"""

import socket
import sys
import threading
import time

import pytest

from tests.contrato import atributo

CANARIO_ENV = "valor-canario-env-7c1d"
CANARIO_ARQ = "conteudo-canario-arquivo-42b9"


def _executar(codigo: str, **kw):
    executar = atributo("app.sandbox", "executar", "REQ-027")
    kw.setdefault("timeout_s", 2)
    return executar(codigo, **kw)


def _saida(res) -> str:
    return f"{res.stdout}\n{res.stderr}"


def _so_linux():
    if sys.platform != "linux":
        pytest.skip("rlimit (memória/processos) só funciona em Linux; ver arquitetura.md, Riscos")


def test_req_027_codigo_legitimo_executa_e_devolve_stdout():
    res = _executar("print(sum(range(5)))")
    assert res.ok is True and res.stdout.strip() == "10"


@pytest.mark.parametrize("codigo", [
    "while True:\n    pass",
    "while True:\n    x = 1 + 1",
    "import time\ntime.sleep(60)",
    "def f():\n    return f()\ntry:\n    f()\nexcept RecursionError:\n    pass\nwhile True: pass",
], ids=["while-pass", "while-conta", "sleep", "recursao-e-loop"])
def test_req_027_loop_infinito_estoura_timeout(codigo):
    inicio = time.monotonic()
    res = _executar(codigo, timeout_s=1)
    assert time.monotonic() - inicio < 6, "sandbox não matou o processo no timeout"
    assert res.ok is False
    assert "timeout" in (res.motivo or "").lower()


def test_req_027_saida_gigante_e_truncada():
    res = _executar("while True:\n    print('x' * 10000)", timeout_s=1)
    assert res.ok is False
    assert len(res.stdout) <= 2 * 1024 * 1024


@pytest.mark.parametrize("codigo", [
    "import os\nprint(os.getcwd())",
    "import subprocess\nsubprocess.run(['echo', 'x'])",
    "import socket\nsocket.socket()",
    "import ctypes",
    "import multiprocessing",
    "import shutil",
    "from os import system",
    "__import__('os')",
    "import importlib\nimportlib.import_module('subprocess')",
    "exec('import os')",
    "eval(\"__import__('socket')\")",
    "getattr(__builtins__, '__import__')('os')",
], ids=["os", "subprocess", "socket", "ctypes", "multiprocessing", "shutil", "from-os",
        "__import__", "importlib", "exec", "eval", "getattr-builtins"])
def test_req_027_import_de_modulos_perigosos_e_bloqueado(codigo):
    res = _executar(codigo)
    assert res.ok is False, f"código perigoso foi aceito: {codigo!r}"


def test_req_027_nao_le_variaveis_de_ambiente(monkeypatch):
    monkeypatch.setenv("SEGREDO_CANARIO", CANARIO_ENV)
    monkeypatch.setenv("DATABASE_URL", "postgresql" + "://u:" + CANARIO_ENV + "@db/x")
    tentativas = [
        "import os\nprint(os.environ)",
        "import os\nprint(os.getenv('SEGREDO_CANARIO'))",
        "print(open('/proc/self/environ').read())",
        "print(__import__('os').environ['DATABASE_URL'])",
        "import sys\nprint(sys.modules.get('os').environ)",
    ]
    for codigo in tentativas:
        res = _executar(codigo)
        assert CANARIO_ENV not in _saida(res), f"vazou ambiente com: {codigo!r}"


def test_req_027_nao_le_nem_escreve_arquivos_do_app(tmp_path):
    segredo = tmp_path / "segredo.txt"
    segredo.write_text(CANARIO_ARQ)
    alvo_escrita = tmp_path / "escrito_pelo_sandbox.txt"
    leitura = [
        f"print(open({str(segredo)!r}).read())",
        "print(open('/etc/passwd').read())",
        f"from pathlib import Path\nprint(Path({str(segredo)!r}).read_text())",
        f"print(open('../../{segredo.name}').read())",
    ]
    for codigo in leitura:
        res = _executar(codigo)
        assert CANARIO_ARQ not in _saida(res), f"leu arquivo com: {codigo!r}"
        assert "root:" not in _saida(res)
    _executar(f"open({str(alvo_escrita)!r}, 'w').write('pwned')")
    assert not alvo_escrita.exists(), "sandbox escreveu fora da sua área"
    assert segredo.read_text() == CANARIO_ARQ


def test_req_027_sem_rede():
    visitas = []
    servidor = socket.socket()
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(5)
    servidor.settimeout(0.5)
    porta = servidor.getsockname()[1]

    def aceita():
        try:
            conexao, _ = servidor.accept()
            visitas.append(conexao)
            conexao.close()
        except OSError:
            pass

    t = threading.Thread(target=aceita)
    t.start()
    try:
        for codigo in [
            f"import socket\ns = socket.create_connection(('127.0.0.1', {porta}))",
            f"import urllib.request\nurllib.request.urlopen('http://127.0.0.1:{porta}')",
            f"import http.client\nhttp.client.HTTPConnection('127.0.0.1', {porta}).request('GET', '/')",
        ]:
            _executar(codigo)
    finally:
        t.join()
        servidor.close()
    assert visitas == [], "sandbox conseguiu abrir conexão de rede"


def test_req_027_subprocess_nao_executa_comando_no_host():
    res = _executar("import subprocess\nprint(subprocess.check_output(['echo', 'PWNED_MARKER']))")
    assert "PWNED_MARKER" not in _saida(res)


def test_req_027_estouro_de_memoria_e_contido():
    executar = atributo("app.sandbox", "executar", "REQ-027")  # A antes de qualquer skip
    _so_linux()
    for codigo in [
        "x = bytearray(4 * 1024 ** 3)\nprint(len(x))",
        "x = [0] * (10 ** 10)",
        "s = 'a'\nwhile True:\n    s += s",
    ]:
        res = executar(codigo, timeout_s=5, memoria_mb=64)
        assert res.ok is False
        assert "mem" in (res.motivo or "").lower() or "memoryerror" in res.stderr.lower()


def test_req_027_fork_bomb_e_contida():
    executar = atributo("app.sandbox", "executar", "REQ-027")  # A antes de qualquer skip
    _so_linux()
    # Limitada de propósito (200 filhos de 30 s): segura se o sandbox falhar, e ainda assim
    # exige que o sandbox impeça a criação de processos em massa.
    bomba = (
        "import os, time\n"
        "for _ in range(200):\n"
        "    if os.fork() == 0:\n"
        "        time.sleep(30)\n"
        "        os._exit(0)\n"
        "print('FORK_OK')\n"
    )
    res = executar(bomba, timeout_s=3)
    assert res.ok is False
    assert "FORK_OK" not in _saida(res)
