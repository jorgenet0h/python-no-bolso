"""REQ-001 a REQ-006: exercícios. REQ-005 (só toques) é verificado no e2e do front."""

from tests.contrato import (
    CAMPOS_GABARITO,
    NIVEIS,
    TEMAS,
    TIPOS,
    chamar,
    contar,
    semear_exercicio,
)


def _pedir(client, req, device, **filtros):
    return chamar(client, "GET", "/exercicios", req, device=device, params=filtros)


def test_req_001_quatro_tipos_de_exercicio_sao_oferecidos(client, device):
    for tipo in TIPOS:
        semear_exercicio("REQ-001", tipo=tipo)
    for tipo in TIPOS:
        resp = _pedir(client, "REQ-001", device, tipo=tipo)
        assert resp.status_code == 200
        assert resp.json()["tipo"] == tipo


def test_req_002_exercicio_tem_nivel_e_tema_dos_enums(client, device):
    semear_exercicio("REQ-002", nivel="intermediario", tema="listas")
    corpo = _pedir(client, "REQ-002", device, nivel="intermediario", tema="listas")
    assert corpo.status_code == 200
    assert corpo.json()["nivel"] in NIVEIS
    assert corpo.json()["tema"] in TEMAS
    # Valor fora do enum no filtro é rejeitado com erro de domínio, nunca ignorado.
    ruim = _pedir(client, "REQ-002", device, tipo="tipo_que_nao_existe")
    assert 400 <= ruim.status_code < 500
    assert "code" in ruim.json()


def test_req_003_devolve_validado_priorizando_nao_resolvidos(client, device):
    resolvido = semear_exercicio("REQ-003", tema="lacos")
    pendente = semear_exercicio("REQ-003", tema="lacos")
    ok = chamar(client, "POST", "/respostas", "REQ-003", device=device,
                json={"exercicio_id": resolvido["id"], "resposta": resolvido["gabarito"]})
    assert ok.status_code == 200 and ok.json()["correta"] is True
    for _ in range(8):
        resp = _pedir(client, "REQ-003", device, tema="lacos")
        assert resp.status_code == 200
        assert resp.json()["id"] == pendente["id"]
    # Filtro opcional: sem nenhum filtro também devolve exercício.
    assert _pedir(client, "REQ-003", device).status_code == 200


def test_req_004_resposta_nao_inclui_gabarito(client, device):
    for tipo in TIPOS:
        semear_exercicio("REQ-004", tipo=tipo)
        corpo = _pedir(client, "REQ-004", device, tipo=tipo).json()
        vazados = [c for c in CAMPOS_GABARITO if c in corpo]
        assert not vazados, f"campos que entregam a resposta: {vazados}"


def test_req_006_sem_exercicio_devolve_erro_com_sugestao(client, device):
    assert contar("Exercicio", "REQ-006", tema="strings", nivel="intermediario",
                  tipo="achar_bug") == 0
    resp = _pedir(client, "REQ-006", device, tipo="achar_bug", nivel="intermediario",
                  tema="strings")
    assert 400 <= resp.status_code < 500
    corpo = resp.json()
    assert corpo["code"] == "SEM_EXERCICIO"
    assert "filtro" in corpo["message"].lower()  # sugere um filtro mais amplo
