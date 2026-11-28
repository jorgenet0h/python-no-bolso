"""Testes da própria bateria de evals: sem rede, sem cota, sem modelo real.
Rodar da raiz do repositório: python -m pytest evals/tests (não faz parte do CI da API)."""

import copy
import json

import pytest

from evals import provedores, runner
from evals.execucao import barrar, executar
from evals.metricas import metrica_a, metrica_b, metrica_c, metrica_d
from evals.provedores import exercicio_modelo, extrair_json
from evals.selfbleu import self_bleu

# ----------------------------------------------------------------------------- executor

def test_executor_roda_codigo_legitimo():
    r = executar("print(sum(range(5)))")
    assert r.ok and r.stdout.strip() == "10"


@pytest.mark.parametrize("codigo", [
    "import os", "import subprocess", "import socket", "from os import system",
    "open('/etc/passwd')", "exec('1')", "eval('1')", "__import__('os')",
    "().__class__.__bases__", "__builtins__['__import__']('os')", "getattr(1, 'real')",
    "import importlib",
])
def test_executor_barra_codigo_perigoso_antes_de_executar(codigo):
    assert barrar(codigo) is not None
    assert executar(codigo).ok is False


def test_executor_timeout_em_loop_infinito():
    r = executar("while True:\n    pass", timeout_s=1)
    assert r.ok is False and r.motivo == "timeout"


# ----------------------------------------------------------------------------- self-bleu

def test_self_bleu_textos_iguais_sao_quase_1_e_variados_sao_menores():
    iguais = ["a = 1 print a + b", "a = 1 print a + b", "a = 1 print a + b"]
    variados = ["a = 1 print a + b", "for i in range 3 soma += i", "def f x return x * 2 lista"]
    assert self_bleu(iguais) > 0.9
    assert self_bleu(variados) < self_bleu(iguais) / 2


def test_self_bleu_precisa_de_pelo_menos_dois_textos():
    assert self_bleu(["so um"]) is None
    assert self_bleu([]) is None


# ----------------------------------------------------------------------------- métrica (b)

EX = {t: exercicio_modelo(t, "iniciante", "variaveis", "t") for t in
      ["prever_saida", "completar_lacuna", "ordenar_linhas", "achar_bug"]}


@pytest.mark.parametrize("tipo", list(EX))
def test_b_exercicio_valido_passa(tipo):
    assert metrica_b(EX[tipo]) == (True, None)


def test_b_rejeita_campo_faltando_extra_e_enum_invalido():
    base = EX["prever_saida"]
    sem = {k: v for k, v in base.items() if k != "opcoes"}
    assert metrica_b(sem)[0] is False
    assert metrica_b({**base, "campo_extra": 1})[0] is False
    assert metrica_b({**base, "tipo": "inventado"})[0] is False
    assert metrica_b({**base, "gabarito": ["a"]})[0] is False
    sem_corrigido = {k: v for k, v in EX["achar_bug"].items() if k != "codigo_corrigido"}
    assert metrica_b(sem_corrigido)[0] is False
    assert metrica_b("texto solto")[0] is False
    assert metrica_b(None)[0] is False


# ----------------------------------------------------------------------------- métrica (a)

@pytest.mark.parametrize("tipo", list(EX))
def test_a_saida_certa_passa(tipo):
    assert metrica_a(EX[tipo]) == (True, None)


def test_a_detecta_saida_afirmada_errada():
    ex = {**EX["prever_saida"], "saida_esperada": "999\n"}
    ok, motivo = metrica_a(ex)
    assert ok is False and "diverg" in motivo


def test_a_detecta_codigo_que_nao_executa():
    ex = {**EX["prever_saida"], "codigo": "print(nome_inexistente)"}
    assert metrica_a(ex)[0] is False


def test_a_nao_executa_codigo_perigoso_do_modelo():
    ex = {**EX["prever_saida"], "codigo": "import os\nprint(os.getcwd())"}
    ok, motivo = metrica_a(ex)
    assert ok is False and "proibido" in motivo


def test_a_aceita_diferenca_so_de_espaco_no_fim():
    ex = {**EX["prever_saida"]}
    ex["saida_esperada"] = ex["saida_esperada"].strip() + "   \n\n"
    assert metrica_a(ex)[0] is True


# ----------------------------------------------------------------------------- métrica (c)

def test_c_so_se_aplica_a_achar_bug():
    assert metrica_c(EX["prever_saida"]) == (None, None)


def test_c_defeito_falha_e_correcao_funciona():
    assert metrica_c(EX["achar_bug"]) == (True, None)


def test_c_defeito_igual_a_correcao_reprova():
    ex = {**EX["achar_bug"], "codigo_corrigido": EX["achar_bug"]["codigo"]}
    assert metrica_c(ex)[0] is False


def test_c_defeito_que_nao_falha_reprova():
    ex = copy.deepcopy(EX["achar_bug"])
    ex["codigo"] = ex["codigo_corrigido"] + "\n"  # "defeito" que na verdade funciona
    assert metrica_c(ex)[0] is False


def test_c_correcao_que_nao_funciona_reprova():
    ex = {**EX["achar_bug"], "codigo_corrigido": "print(0)"}
    assert metrica_c(ex)[0] is False


# ----------------------------------------------------------------------------- métrica (d)

def test_d_so_se_aplica_a_ordenar_linhas():
    assert metrica_d(EX["achar_bug"]) == (None, None)


def test_d_ordem_unica_passa():
    assert metrica_d(EX["ordenar_linhas"]) == (True, None)


def test_d_ordem_ambigua_reprova():
    ex = exercicio_modelo("ordenar_linhas", "iniciante", "lacos", "x", "ordem_ambigua")
    ok, motivo = metrica_d(ex)
    assert ok is False and "2 combinações" in motivo


def test_d_nenhuma_ordem_valida_reprova():
    ex = {**EX["ordenar_linhas"], "saida_esperada": "999\n"}
    ok, motivo = metrica_d(ex)
    assert ok is False and "0 combinações" in motivo


def test_d_indentacao_alternativa_tambem_valida_reprova():
    """D-06: mesma ordem, e a indentação sozinha deixa duas combinações válidas."""
    ex = {**EX["ordenar_linhas"],
          "opcoes": ["print('b')", "for i in range(1):", "print('a')"],
          "gabarito": [[1, 0], [2, 1], [0, 0]], "saida_esperada": "a\nb\n"}
    # for / print a (dentro) / print b (fora)  e  for / print a (dentro) / print b (dentro)
    # (e também print a / for / print b dentro) produzem a MESMA saída: não é única.
    assert metrica_a(ex) == (True, None)
    ok, motivo = metrica_d(ex)
    assert ok is False and motivo[0] in "23456789" and "combinações" in motivo  # mais de uma


def test_d_corpo_do_laco_exige_indentacao_para_ser_unica():
    ex = EX["ordenar_linhas"]
    assert metrica_d(ex) == (True, None)
    # A mesma ordem sem indentar `total += i` NÃO é a resposta certa (métrica a).
    errado = {**ex, "gabarito": [[p, 0] for p, _ in ex["gabarito"]]}
    assert metrica_a(errado)[0] is False


def test_combinacoes_podadas_pela_gramatica():
    from evals.metricas import combinacoes

    pecas = ["for i in range(2):", "print(i)"]
    todas = {tuple(c) for c in combinacoes(pecas)}
    # Só 'for' primeiro, com o corpo um nível abaixo; ou 'print' primeiro e 'for' depois.
    assert ((0, 0), (1, 1)) in todas
    assert ((1, 0), (0, 0)) in todas
    assert ((0, 0), (1, 0)) not in todas  # laço sem corpo
    assert all(c[0][1] == 0 for c in todas)  # a primeira linha nunca é indentada


def test_b_gabarito_de_ordenar_linhas_exige_pares_e_nos_outros_tipos_indices():
    ordenar = EX["ordenar_linhas"]
    assert metrica_b({**ordenar, "gabarito": [3, 1, 2, 0]})[0] is False  # formato antigo
    assert metrica_b({**ordenar, "gabarito": [[3, 0], [1, 0], [2, 9], [0, 0]]})[0] is False
    assert metrica_b({**ordenar, "gabarito": [[3, 0], [1, 0], [2, 1.5], [0, 0]]})[0] is False
    assert metrica_b({**EX["prever_saida"], "gabarito": [[1, 0]]})[0] is False


def test_d_pecas_demais_reprova_sem_explodir():
    ex = {**EX["ordenar_linhas"], "opcoes": [f"x{i} = {i}" for i in range(7)]}
    assert metrica_d(ex)[0] is False


# ----------------------------------------------------------------------------- provedores e runner

def test_extrair_json_aceita_cerca_markdown_e_trata_lixo_como_invalido():
    assert extrair_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert "_invalido" in extrair_json("claro! aqui está o exercício")
    assert "_invalido" in extrair_json("[1, 2]")


def test_resposta_invalida_do_modelo_conta_como_falha_de_schema():
    class Lixo:
        def completar(self, mensagens, tools):
            return {"_invalido": "texto"}

    r = runner.avaliar_caso(Lixo(), {"id": "c1", "tipo": "prever_saida", "nivel": "iniciante",
                                     "tema": "variaveis"})
    assert r["b"] is False and r["acao"] == "rejeitado"


def test_provedor_que_levanta_excecao_vira_acao_falhou():
    class Quebrado:
        def completar(self, mensagens, tools):
            raise TimeoutError("cota")

    r = runner.avaliar_caso(Quebrado(), {"id": "c1", "tipo": "prever_saida", "nivel": "iniciante",
                                         "tema": "variaveis"})
    assert r["acao"] == "falhou" and "TimeoutError" in r["motivo"]


def test_modelo_que_nunca_entrega_atinge_o_limite_de_passos():
    class SoTool:
        def completar(self, mensagens, tools):
            return {"tool": "executar_python", "args": {"codigo": "print(1)"}}

    r = runner.avaliar_caso(SoTool(), {"id": "c1", "tipo": "prever_saida", "nivel": "iniciante",
                                       "tema": "variaveis"})
    assert r["acao"] == "falhou" and len(r["tools"]) == runner.MAX_PASSOS


def test_o_prompt_enviado_ao_modelo_so_tem_enums_e_id_do_caso():
    vistos = []

    class Espiao:
        def completar(self, mensagens, tools):
            vistos.append(mensagens)
            return {"_invalido": ""}

    caso = {"id": "c9", "tipo": "achar_bug", "nivel": "intermediario", "tema": "lacos"}
    runner.avaliar_caso(Espiao(), caso)
    usuario = [m["content"] for m in vistos[0] if m["role"] == "user"]
    assert usuario == ["tipo=achar_bug nivel=intermediario tema=lacos caso=c9"]


def test_bateria_deterministica_mesmos_casos_em_todos_os_modelos(tmp_path):
    assert runner.main(["--deterministico", "--saida", str(tmp_path)]) == 0
    por_modelo = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in tmp_path.glob("*.json")}
    assert len(por_modelo) >= 2
    conjuntos = [[c["caso"] for c in r["casos"]] for r in por_modelo.values()]
    assert all(c == conjuntos[0] for c in conjuntos)
    acoes = [tuple(c["acao"] for c in r["casos"]) for r in por_modelo.values()]
    assert acoes[0] != acoes[1], "a bateria deve distinguir o modelo bom do defeituoso"
    assert (tmp_path / "resumo.md").read_text(encoding="utf-8").count("| Métrica |") >= 2


def test_mock_perfeito_passa_em_todas_as_metricas():
    p = provedores.Mock("perfeito")
    casos = runner.carregar_yaml(runner.RAIZ / "casos.yaml")["casos"]
    resultados = [runner.avaliar_caso(p, c) for c in casos]
    assert {r["acao"] for r in resultados} == {"aprovado"}
