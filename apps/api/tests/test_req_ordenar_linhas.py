"""D-06 (alterada pelo usuário): a resposta de `ordenar_linhas` leva a ordem E a indentação de cada
linha, como pares [índice, nível]. Cobre REQ-007 (comparação), REQ-008 (só números) e REQ-010
(resposta inválida não registra tentativa). O outro lado da regra, "o exercício só vale se existir
UMA combinação ordem+indentação", está em test_req_validacao (REQ-026)."""

import pytest

from tests.contrato import chamar, checar_erro, contar, semear_exercicio


def _responder(client, req, device, ex_id, resposta):
    return chamar(client, "POST", "/respostas", req, device=device,
                  json={"exercicio_id": ex_id, "resposta": resposta})


def test_req_007_ordenar_linhas_confere_ordem_e_indentacao(client, device):
    ex = semear_exercicio("REQ-007", tipo="ordenar_linhas")
    certa = ex["gabarito"]  # [[3, 0], [1, 0], [2, 1], [0, 0]]
    mesma_ordem_sem_indentar = [[indice, 0] for indice, _ in certa]
    ordem_errada_com_indentacao_certa = [[1, 0], [3, 0], [2, 1], [0, 0]]
    indentacao_errada_no_lugar_errado = [[3, 0], [1, 1], [2, 1], [0, 0]]
    for resposta, correta in [
        (certa, True),
        (mesma_ordem_sem_indentar, False),  # a ordem está certa, falta indentar o corpo do laço
        (ordem_errada_com_indentacao_certa, False),
        (indentacao_errada_no_lugar_errado, False),
    ]:
        resp = _responder(client, "REQ-007", device, ex["id"], resposta)
        assert resp.status_code == 200
        assert resp.json()["correta"] is correta, f"resposta {resposta}"


@pytest.mark.parametrize("ruim", [
    [3, 1, 2, 0],                      # só a ordem, sem indentação (formato antigo)
    [[3, 0], [1, 0], [2, 1]],          # faltou uma peça
    [[3, 0], [1, 0], [2, 1], [2, 1]],  # peça repetida
    [[3, 0], [1, 0], [2, 1], [9, 0]],  # índice fora do intervalo
    [[3, 0], [1, 0], [2, -1], [0, 0]],  # indentação negativa
    [[3, 0], [1, 0], [2, 99], [0, 0]],  # indentação absurda
    [[3, 0], [1, 0], [2, 1.5], [0, 0]],  # número não inteiro
    [[3, 0], [1, 0], [2, True], [0, 0]],  # booleano não é número aqui
    [[3, 0], [1, 0], [2, "1"], [0, 0]],  # texto
    [[3, 0], [1, 0], [2], [0, 0]],     # par incompleto
    [[3, 0, 0], [1, 0], [2, 1], [0, 0]],  # par com 3 itens
    [{"indice": 3, "nivel": 0}] * 4,   # objeto no lugar de par
], ids=[f"ruim{i}" for i in range(12)])
def test_req_008_ordenar_linhas_exige_pares_indice_e_indentacao(client, device, ruim):
    ex = semear_exercicio("REQ-008", tipo="ordenar_linhas")
    resp = _responder(client, "REQ-008", device, ex["id"], ruim)
    checar_erro(resp, "RESPOSTA_INVALIDA")
    assert contar("Tentativa", "REQ-008", device_id=device) == 0


def test_req_008_pares_so_valem_para_ordenar_linhas(client, device):
    ex = semear_exercicio("REQ-008", tipo="prever_saida")
    for ruim in ([[1, 0]], [[1, 0], [0, 0]]):
        checar_erro(_responder(client, "REQ-008", device, ex["id"], ruim), "RESPOSTA_INVALIDA")
    assert contar("Tentativa", "REQ-008", device_id=device) == 0
