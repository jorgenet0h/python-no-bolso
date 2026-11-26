"""REQ-031 a REQ-035 e REQ-044: erros do back-end e health."""

import logging

import pytest

from tests.contrato import atributo, carregar, chamar, nao_implementado

SEGREDO_INTERNO = "segredo-interno-do-teste-9f3a"
CODIGOS_DE_DOMINIO = {"SEM_EXERCICIO", "RESPOSTA_INVALIDA", "DEVICE_INVALIDO", "INDISPONIVEL"}


def _todas_subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from _todas_subclasses(sub)


@pytest.fixture()
def rota_que_explode(app):
    """Rota de teste que levanta erro imprevisto, para exercitar o handler global."""

    async def explode():
        raise RuntimeError(SEGREDO_INTERNO)

    app.add_api_route("/__teste/explode", explode, methods=["GET"])
    yield "/__teste/explode"
    app.router.routes[:] = [r for r in app.router.routes
                            if getattr(r, "path", "") != "/__teste/explode"]


def test_req_031_falhas_de_dominio_sao_excecoes_tipadas():
    base = atributo("app.errors", "ErroDominio", "REQ-031")
    assert issubclass(base, Exception)
    filhas = list(_todas_subclasses(base))
    codigos = {getattr(f, "code", None) for f in filhas}
    faltando = CODIGOS_DE_DOMINIO - codigos
    assert not faltando, f"sem exceção tipada para: {sorted(faltando)}"
    for f in filhas:
        assert isinstance(getattr(f, "status_code", None), int)


def test_req_032_handler_global_responde_code_message_com_status_adequado(client, device):
    resp = chamar(client, "GET", "/exercicios", "REQ-032", device="nao-e-uuid")
    assert resp.status_code == 400 or resp.status_code == 422
    assert set(resp.json()) == {"code", "message"}
    assert resp.json()["code"] == "DEVICE_INVALIDO"
    # Falha de validação do framework também passa pelo mesmo formato.
    resp = chamar(client, "POST", "/respostas", "REQ-032", device=device, content="{ isto nao e json",
                  headers={"content-type": "application/json"})
    assert 400 <= resp.status_code < 500
    assert set(resp.json()) == {"code", "message"}


def test_req_033_nao_vaza_stack_trace_prompt_ou_detalhe_interno(client, rota_que_explode, device):
    resp = client.get(rota_que_explode)
    texto = resp.text
    assert resp.status_code == 500
    for vazamento in ("Traceback", 'File "', SEGREDO_INTERNO, "RuntimeError", ".py",
                      "system prompt", "executar_python"):
        assert vazamento not in texto, f"vazou: {vazamento}"
    # Mesma regra nos erros de validação.
    r2 = chamar(client, "POST", "/respostas", "REQ-033", device=device, json={"exercicio_id": 1})
    assert "pydantic" not in r2.text.lower() and '"loc"' not in r2.text


def test_req_034_erro_imprevisto_vira_erro_interno_com_id_de_correlacao(
        client, rota_que_explode, caplog):
    caplog.set_level(logging.ERROR)
    resp = client.get(rota_que_explode)
    assert resp.status_code == 500
    if "json" not in resp.headers.get("content-type", ""):
        nao_implementado("REQ-034", "sem handler global: 500 sem corpo {code, message}")
    corpo = resp.json()
    assert corpo["code"] == "ERRO_INTERNO"
    # id de correlação no corpo ou em header, e o mesmo id aparece no log do servidor.
    candidatos = [v for k, v in corpo.items() if "correla" in k.lower() or "request" in k.lower()]
    candidatos += [v for k, v in resp.headers.items()
                   if "correlation" in k.lower() or "request-id" in k.lower()]
    assert candidatos, "resposta sem id de correlação"
    log = caplog.text  # inclui o traceback formatado
    assert SEGREDO_INTERNO in log and "RuntimeError" in log, "stack trace deve ir só para o log"
    assert str(candidatos[0]) in log


def test_req_035_banco_indisponivel(client, app, device):
    db = carregar("app.db", "REQ-035")
    if not hasattr(db, "get_session"):
        nao_implementado("REQ-035", "app.db.get_session (dependência de sessão) não existe")

    def sem_banco():
        raise ConnectionError("banco fora do ar")
        yield  # pragma: no cover

    app.dependency_overrides[db.get_session] = sem_banco
    try:
        saude = client.get("/health")
        assert saude.status_code >= 500
        for rota in ["/exercicios", "/progresso"]:
            resp = chamar(client, "GET", rota, "REQ-035", device=device)
            assert resp.json()["code"] == "INDISPONIVEL"
            assert resp.status_code == 503
    finally:
        app.dependency_overrides.pop(db.get_session, None)


def test_req_044_health_expoe_status_da_api_e_do_banco(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    corpo = resp.json()
    assert "db" in corpo, "GET /health precisa informar o banco, não só {'status': 'ok'}"
    assert corpo.get("api", corpo.get("status")) == "ok"
    assert corpo["db"] == "ok"
