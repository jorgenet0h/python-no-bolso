"""REQ-042 e REQ-043: evals e CI. A bateria de evals em si fica em evals/."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]


def test_req_042_evals_rodam_o_mesmo_conjunto_em_2_ou_mais_modelos(tmp_path):
    modelos = yaml.safe_load((RAIZ / "evals" / "models.yaml").read_text(encoding="utf-8"))
    assert len(modelos["modelos"]) >= 2
    saida = tmp_path / "resultados"
    proc = subprocess.run(
        [sys.executable, "-m", "evals.runner", "--deterministico", "--saida", str(saida)],
        cwd=RAIZ, capture_output=True, text=True, timeout=120, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    resultados = [json.loads(p.read_text(encoding="utf-8")) for p in saida.glob("*.json")]
    assert len(resultados) >= 2
    casos = [sorted(c["caso"] for c in r["casos"]) for r in resultados]
    assert all(c == casos[0] for c in casos), "modelos rodaram conjuntos de casos diferentes"
    for r in resultados:
        assert all(c["acao"] in {"aprovado", "rejeitado", "tool:executar_python", "falhou"}
                   for c in r["casos"])


def test_req_043_ci_roda_lint_testes_e_evals_deterministicos():
    ci = yaml.safe_load((RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    assert "pull_request" in (ci.get("on") or ci.get(True))
    comandos = "\n".join(
        passo.get("run", "") for job in ci["jobs"].values() for passo in job["steps"]
    )
    assert "ruff check" in comandos
    assert "pytest" in comandos
    assert "lint:web" in comandos
    if "evals" not in comandos:
        pytest.fail("NAO-IMPLEMENTADO [REQ-043] CI sem passo de evals determinísticos "
                    "(sugestão: python -m evals.runner --deterministico; ver docs/spec-gaps.md)",
                    pytrace=False)
    assert "--deterministico" in comandos, "CI não pode gastar cota de modelo real"
