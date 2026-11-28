"""REQ-044: GET /health expõe o status da API e do banco.

Substitui o teste anterior, que só cobria a API (DISP-001, resolvido a favor da spec)."""

from tests.contrato import HEALTH_DEGRADADO, HEALTH_OK, banco_fora


def test_req_044_health_banco_acessivel_responde_200_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == HEALTH_OK, "GET /health precisa informar também o banco"


def test_req_044_health_banco_inacessivel_responde_503_degraded(client, app):
    with banco_fora(app, "REQ-044"):
        resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json() == HEALTH_DEGRADADO
