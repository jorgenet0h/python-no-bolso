"""REQ-007 a REQ-013: correção e explicação de erro."""

import pytest

from tests.contrato import (
    ProvedorFalso,
    atributo,
    carregar,
    chamar,
    checar_erro,
    contar,
    semear_exercicio,
)


def _responder(client, req, device, ex_id, resposta):
    return chamar(client, "POST", "/respostas", req, device=device,
                  json={"exercicio_id": ex_id, "resposta": resposta})


def _progresso(client, req, device):
    return chamar(client, "GET", "/progresso", req, device=device).json()


def test_req_007_compara_ao_gabarito_e_informa(client, device):
    ex = semear_exercicio("REQ-007")
    certa = _responder(client, "REQ-007", device, ex["id"], ex["gabarito"])
    errada = _responder(client, "REQ-007", device, ex["id"], [0])
    assert certa.status_code == 200 and certa.json()["correta"] is True
    assert errada.status_code == 200 and errada.json()["correta"] is False


@pytest.mark.parametrize("ruim", [
    "1", "opcao b", "print('oi')", {"texto": "x"}, [True], [1.5], ["1"], [None], [[1]],
])
def test_req_008_aceita_apenas_indices_numericos(client, device, ruim):
    ex = semear_exercicio("REQ-008")
    resp = _responder(client, "REQ-008", device, ex["id"], ruim)
    checar_erro(resp, "RESPOSTA_INVALIDA")
    assert contar("Tentativa", "REQ-008", device_id=device) == 0


def test_req_009_acerto_registra_tentativa_e_mostra_explicacao(client, device):
    ex = semear_exercicio("REQ-009")
    antes = _progresso(client, "REQ-009", device)
    resp = _responder(client, "REQ-009", device, ex["id"], ex["gabarito"])
    assert resp.json()["correta"] is True
    assert resp.json()["explicacao"] == ex["explicacao"]
    assert contar("Tentativa", "REQ-009", device_id=device, correta=True) == 1
    depois = _progresso(client, "REQ-009", device)
    assert depois["total_acertos"] == antes.get("total_acertos", 0) + 1


@pytest.mark.parametrize("ruim", [[99], [-1], [], "", None, [0, 0, 0, 0, 0, 0]])
def test_req_010_resposta_invalida_rejeitada_sem_registrar(client, device, ruim):
    ex = semear_exercicio("REQ-010")
    resp = _responder(client, "REQ-010", device, ex["id"], ruim)
    checar_erro(resp, "RESPOSTA_INVALIDA")
    assert contar("Tentativa", "REQ-010", device_id=device) == 0


def test_req_011_erro_mostra_explicacao_da_opcao_escolhida(client, device):
    ex = semear_exercicio("REQ-011")
    a = _responder(client, "REQ-011", device, ex["id"], [0]).json()
    c = _responder(client, "REQ-011", device, ex["id"], [2]).json()
    assert a["correta"] is False and c["correta"] is False
    assert a["explicacao"] and c["explicacao"]
    assert a["explicacao"] != c["explicacao"]


def test_req_012_explicador_recebe_so_id_e_opcao_e_nao_tem_tool(device):
    explicar = atributo("app.agent.explicador", "explicar", "REQ-012")
    ex = semear_exercicio("REQ-012")
    provedor = ProvedorFalso(respostas=[{"final": {"explicacao": "ok"}}])
    explicar(ex["id"], 0, provedor=provedor)
    assert provedor.chamadas, "o explicador deve chamar o modelo"
    for chamada in provedor.chamadas:
        assert not chamada["tools"], "explicador não pode ter tool (muito menos execução)"
    enviado = provedor.texto_enviado()
    assert ex["id"] in enviado or ex["enunciado"] in enviado
    assert "executar_python" not in enviado
    # Só id + opção: nenhum parâmetro de texto livre na assinatura.
    import inspect

    nomes = set(inspect.signature(explicar).parameters)
    assert not nomes & {"texto", "mensagem", "pergunta", "prompt", "comentario"}


def test_req_013_falha_do_explicador_cai_na_explicacao_generica(client, device, monkeypatch):
    # D-17: se a opção tem explicação armazenada o agente nem é chamado; REQ-013 vale sem ela.
    ex = semear_exercicio("REQ-013", explicacoes_por_opcao={})
    mod = carregar("app.agent.explicador", "REQ-013")

    def quebra(*a, **kw):
        raise TimeoutError("estourou o tempo")

    monkeypatch.setattr(mod, "explicar", quebra)
    resp = _responder(client, "REQ-013", device, ex["id"], [0])
    assert resp.status_code == 200
    assert resp.json()["correta"] is False
    assert resp.json()["explicacao"] == ex["explicacao"]
