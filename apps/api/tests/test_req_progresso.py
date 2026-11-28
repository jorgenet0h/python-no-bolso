"""REQ-015, REQ-016, REQ-018: progresso por aparelho anônimo.
REQ-014 (UUID gerado no cliente) e REQ-017 (offline) são do front: Vitest e e2e."""

import pytest

from tests.contrato import (
    chamar,
    checar_erro,
    contar,
    novo_device,
    semear_exercicio,
    semear_tentativa,
)


def test_req_015_tentativas_ligadas_ao_device_sem_cadastro(client):
    ex = semear_exercicio("REQ-015", tema="funcoes")
    d1, d2 = novo_device(), novo_device()
    r = chamar(client, "POST", "/respostas", "REQ-015", device=d1,
               json={"exercicio_id": ex["id"], "resposta": ex["gabarito"]})
    assert r.status_code == 200  # sem login, e-mail ou senha
    assert contar("Tentativa", "REQ-015", device_id=d1) == 1
    assert contar("Tentativa", "REQ-015", device_id=d2) == 0
    p2 = chamar(client, "GET", "/progresso", "REQ-015", device=d2).json()
    assert p2["total_acertos"] == 0


def test_req_016_progresso_mostra_acertos_taxa_por_tipo_e_sequencia(client, device):
    certo = semear_exercicio("REQ-016", tipo="prever_saida")
    bug = semear_exercicio("REQ-016", tipo="achar_bug")
    for ex, resposta in [(certo, certo["gabarito"]), (bug, [0]), (bug, bug["gabarito"])]:
        chamar(client, "POST", "/respostas", "REQ-016", device=device,
               json={"exercicio_id": ex["id"], "resposta": resposta})
    p = chamar(client, "GET", "/progresso", "REQ-016", device=device).json()
    assert p["total_acertos"] == 2
    assert p["taxa_por_tipo"]["prever_saida"] == pytest.approx(1.0)
    assert p["taxa_por_tipo"]["achar_bug"] == pytest.approx(0.5)
    assert p["sequencia_dias"] == 1  # praticou hoje


@pytest.mark.parametrize("invalido", [
    "", "abc", "123", "00000000-0000-0000-0000-00000000000", "not-a-uuid",
    "' OR 1=1 --", "g" * 36, "../../etc/passwd",
])
def test_req_018_device_id_invalido_responde_device_invalido(client, invalido):
    for metodo, rota in [("GET", "/progresso"), ("GET", "/exercicios")]:
        resp = chamar(client, metodo, rota, "REQ-018", device=invalido)
        checar_erro(resp, "DEVICE_INVALIDO")


def test_req_018_device_id_ausente_tambem_e_invalido(client):
    resp = chamar(client, "GET", "/progresso", "REQ-018")
    checar_erro(resp, "DEVICE_INVALIDO")


def _praticar(device, ex, *dias_atras):
    for d in dias_atras:  # 0 = hoje, 1 = ontem, 2 = anteontem...
        semear_tentativa("REQ-016", device, ex["id"], dias_atras=d)


def _sequencia(client, device) -> int:
    return chamar(client, "GET", "/progresso", "REQ-016", device=device).json()["sequencia_dias"]


def test_req_016_praticou_ontem_mantem_a_sequencia(client, device):
    """D-12 (alterada pelo usuário): sem prática hoje, a sequência segue viva se ontem teve."""
    ex = semear_exercicio("REQ-016")
    _praticar(device, ex, 2, 1)  # anteontem e ontem, ainda não praticou hoje
    assert _sequencia(client, device) == 2
    _praticar(device, ex, 0)  # praticou hoje: a sequência cresce
    assert _sequencia(client, device) == 3


def test_req_016_pulou_um_dia_zera_a_sequencia(client, device):
    """D-12 (alterada pelo usuário): ficar um dia inteiro sem praticar quebra a sequência."""
    ex = semear_exercicio("REQ-016")
    _praticar(device, ex, 3, 2)  # praticou antes, mas ontem e hoje ficaram em branco
    assert _sequencia(client, device) == 0
    _praticar(device, ex, 0)  # volta hoje, tendo pulado ontem: recomeça do 1
    assert _sequencia(client, device) == 1


def test_req_016_sequencia_conta_dias_distintos_e_ignora_lacunas_antigas(client, device):
    ex = semear_exercicio("REQ-016")
    _praticar(device, ex, 9, 8, 6, 2, 1, 1, 0, 0, 0)  # várias tentativas no mesmo dia contam 1
    assert _sequencia(client, device) == 3  # hoje, ontem e anteontem; a lacuna do dia 3 quebra
