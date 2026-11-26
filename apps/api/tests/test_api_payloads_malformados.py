"""Payloads malformados e hostis na API. Nenhum pode causar 5xx, vazar detalhe ou gravar tentativa.
Vinculado a REQ-008, REQ-010, REQ-018, REQ-032 e REQ-033."""

import json
import uuid

import httpx
import pytest

from tests.contrato import chamar, contar, semear_exercicio

CORPOS_RUINS = {
    "json-quebrado": b"{ nao eh json",
    "vazio": b"",
    "array-no-lugar-de-objeto": b"[1, 2, 3]",
    "null": b"null",
    "string-solta": b'"oi"',
    "numero-solto": b"42",
    "utf8-invalido": b'{"exercicio_id": "\xff\xfe"}',
    "nan": b'{"exercicio_id": "x", "resposta": NaN}',
    "profundidade": b"[" * 5000 + b"]" * 5000,
    "campo-extra-hostil": json.dumps({"exercicio_id": str(uuid.uuid4()), "resposta": [0],
                                      "correta": True, "gabarito": [0], "__proto__": {}}).encode(),
    "corpo-enorme": json.dumps({"exercicio_id": "x", "resposta": [0] * 200_000}).encode(),
}


@pytest.mark.parametrize("nome", list(CORPOS_RUINS))
def test_req_032_corpo_malformado_em_respostas_nunca_vira_5xx(client, device, nome):
    resp = chamar(client, "POST", "/respostas", "REQ-032", device=device,
                  content=CORPOS_RUINS[nome], headers={"content-type": "application/json"})
    assert 400 <= resp.status_code < 500, f"{nome}: HTTP {resp.status_code}"
    corpo = resp.json()
    assert set(corpo) == {"code", "message"}
    assert "Traceback" not in resp.text


@pytest.mark.parametrize("exercicio_id", [
    "", "1", "nao-e-uuid", "00000000-0000-0000-0000-000000000000", "' OR '1'='1", None, 7,
    ["a"], {"$ne": None}, "A" * 10_000,
])
def test_req_010_exercicio_id_malformado_ou_inexistente(client, device, exercicio_id):
    resp = chamar(client, "POST", "/respostas", "REQ-010", device=device,
                  json={"exercicio_id": exercicio_id, "resposta": [0]})
    assert 400 <= resp.status_code < 500
    assert set(resp.json()) == {"code", "message"}
    assert contar("Tentativa", "REQ-010", device_id=device) == 0


def test_req_008_cliente_nao_consegue_forcar_correta_nem_gabarito(client, device):
    ex = semear_exercicio("REQ-008")
    errada = next(i for i in range(len(ex["opcoes"])) if [i] != ex["gabarito"])
    resp = chamar(client, "POST", "/respostas", "REQ-008", device=device,
                  json={"exercicio_id": ex["id"], "resposta": [errada],
                        "correta": True, "gabarito": [errada]})
    assert resp.status_code == 200
    assert resp.json()["correta"] is False


@pytest.mark.parametrize("params", [
    {"tipo": ["prever_saida", "achar_bug"]},
    {"tipo": "prever_saida' OR 1=1 --"},
    {"nivel": "%00"},
    {"tema": "a" * 5000},
    {"tipo": "../../etc/passwd"},
    {"tipo": "${jndi:ldap://x}"},
])
def test_req_002_filtros_malformados_em_exercicios(client, device, params):
    resp = chamar(client, "GET", "/exercicios", "REQ-002", device=device, params=params)
    assert 400 <= resp.status_code < 500
    assert set(resp.json()) == {"code", "message"}
    for eco in ("OR 1=1", "jndi", "passwd"):
        assert eco not in resp.json()["message"], "mensagem de erro ecoa o texto do usuário"


@pytest.mark.parametrize("device_header", [
    "\x00", "a" * 100_000, "00000000-0000-0000-0000-000000000000\r\nX-Injetado: 1",
], ids=["nul", "enorme", "crlf-injection"])
def test_req_018_device_header_hostil(client, device_header):
    try:
        resp = chamar(client, "GET", "/progresso", "REQ-018", device=device_header)
    except httpx.HTTPError:  # o cliente pode recusar enviar o header: não chegou à API
        return
    assert 400 <= resp.status_code < 500
    assert "x-injetado" not in {k.lower() for k in resp.headers}


def test_req_033_metodo_e_rota_inexistentes_seguem_o_formato_de_erro(client, device):
    for metodo, rota in [("DELETE", "/exercicios"), ("PUT", "/respostas"), ("GET", "/nao-existe")]:
        resp = client.request(metodo, rota, headers={"X-Device-Id": device})
        assert resp.status_code in (404, 405)
        corpo = resp.json()
        assert set(corpo) == {"code", "message"}, f"{metodo} {rota}: formato {sorted(corpo)}"
