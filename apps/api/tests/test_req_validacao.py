"""REQ-025 a REQ-030: validação por execução. O sandbox em si está em test_sandbox_adversarial."""

import copy

import pytest

from tests.contrato import (
    ExecutorFalso,
    ProvedorFalso,
    ResultadoExecucao,
    atributo,
    contar,
    exercicio_exemplo,
    listar,
    programa_ordenado,
    resposta_final,
)


def _validar(candidato, executor):
    validar = atributo("app.validador", "validar", "REQ-025")
    return validar(candidato, executor=executor)


def _gerar(ex, executor):
    gerar = atributo("app.agent.loop", "gerar", "REQ-028")
    provedor = ProvedorFalso(respostas=[resposta_final(ex)])
    return gerar("prever_saida", "iniciante", "variaveis", provedor=provedor,
                 executor=executor, max_passos=3)


def test_req_025_nao_salva_codigo_que_nao_executou_com_sucesso():
    executor = ExecutorFalso(ok=False)
    resultado = _gerar(exercicio_exemplo(), executor)
    assert resultado.status == "rejeitado"
    assert executor.chamadas, "o validador deve executar o código por conta própria"
    assert contar("Exercicio", "REQ-025") == 0


def test_req_026_saida_real_diferente_da_afirmada_rejeita():
    ex = exercicio_exemplo(saida_esperada="5\n")
    res = _validar(ex, ExecutorFalso(stdout="7\n"))
    assert res.aprovado is False
    assert "diverg" in res.motivo.lower()
    # Mesma saída (ignorando só o \n final) aprova.
    assert _validar(ex, ExecutorFalso(stdout="5")).aprovado is True


def test_req_026_achar_bug_com_bug_e_correcao_iguais_rejeita():
    ex = exercicio_exemplo(tipo="achar_bug", codigo_corrigido="n = 5\nprint(n)",
                           codigo="n = 5\nprint(n)")
    res = _validar(ex, ExecutorFalso(stdout="15\n"))  # as duas versões dão a mesma saída
    assert res.aprovado is False


def test_req_026_ordenar_linhas_sem_permutacao_errada_distinguivel_rejeita():
    ex = exercicio_exemplo(tipo="ordenar_linhas")
    # Toda ordem produz a mesma saída: o exercício não tem ordem única.
    res = _validar(ex, ExecutorFalso(stdout="3\n"))
    assert res.aprovado is False
    # Uma combinação errada que falha ao executar torna a ordem única: aprova.
    correto = programa_ordenado(ex)

    def seletivo(codigo, **kw):
        if codigo == correto:
            return ResultadoExecucao(ok=True, stdout="3\n")
        return ResultadoExecucao(ok=False, stderr="NameError")

    assert _validar(ex, seletivo).aprovado is True


def test_req_026_ordenar_linhas_com_indentacao_alternativa_valida_rejeita():
    """D-06: só vale se existir UMA combinação ordem+indentação. Aqui a mesma ordem, com
    `print(total)` dentro do laço, também roda e dá a mesma saída: a combinação não é única."""
    ex = exercicio_exemplo(tipo="ordenar_linhas")
    correto = programa_ordenado(ex)
    variante = programa_ordenado(ex, [[3, 0], [1, 0], [2, 1], [0, 1]])
    assert variante != correto

    def aceita_duas(codigo, **kw):
        if codigo in (correto, variante):
            return ResultadoExecucao(ok=True, stdout="3\n")
        return ResultadoExecucao(ok=False, stderr="IndentationError")

    assert _validar(ex, aceita_duas).aprovado is False
    # Sem a variante, a combinação é única e o exercício é aprovado.
    def so_correto(codigo, **kw):
        return aceita_duas(codigo) if codigo == correto else ResultadoExecucao(ok=False)

    assert _validar(ex, so_correto).aprovado is True


def test_req_028_validacao_aprovada_salva_com_status_validado():
    resultado = _gerar(exercicio_exemplo(), ExecutorFalso(stdout="5\n"))
    assert resultado.status == "aprovado"
    salvos = listar("Exercicio", "REQ-028")
    assert len(salvos) == 1 and salvos[0].status == "validado"
    assert [e.status for e in listar("ExecucaoGeracao", "REQ-028")] == ["aprovado"]


def test_req_029_validacao_rejeitada_descarta_e_registra_motivo():
    resultado = _gerar(exercicio_exemplo(saida_esperada="999\n"), ExecutorFalso(stdout="5\n"))
    assert resultado.status == "rejeitado"
    assert contar("Exercicio", "REQ-029") == 0
    execucoes = listar("ExecucaoGeracao", "REQ-029", status="rejeitado")
    assert len(execucoes) == 1 and execucoes[0].motivo


def _sem(campo):
    ex = exercicio_exemplo()
    del ex[campo]
    return ex


@pytest.mark.parametrize("invalido", [
    _sem("opcoes"), _sem("gabarito"), _sem("enunciado"), _sem("saida_esperada"),
    exercicio_exemplo(tipo="inventado"), exercicio_exemplo(nivel="expert"),
    exercicio_exemplo(tema="quantica"),
    exercicio_exemplo(opcoes=[]), exercicio_exemplo(gabarito=[7]),
    exercicio_exemplo(gabarito=["a"]), exercicio_exemplo(enunciado="x" * 100_000),
    exercicio_exemplo(codigo="x" * 1_000_000), exercicio_exemplo(opcoes=["a"] * 500),
    {"final": "texto solto, não é JSON de exercício"}, [], None,
    # ordenar_linhas: gabarito é lista de pares [índice, indentação] (D-06)
    exercicio_exemplo(tipo="ordenar_linhas", gabarito=[3, 1, 2, 0]),
    exercicio_exemplo(tipo="ordenar_linhas", gabarito=[[3, 0], [1, 0], [2, -1], [0, 0]]),
    exercicio_exemplo(tipo="ordenar_linhas", gabarito=[[3, 0], [1, 0], [2, 99], [0, 0]]),
    exercicio_exemplo(tipo="ordenar_linhas", gabarito=[[3, 0], [3, 0], [2, 1], [0, 0]]),
    exercicio_exemplo(tipo="ordenar_linhas", gabarito=[[3, 0], [1, 0], [2, 1]]),
    exercicio_exemplo(tipo="prever_saida", gabarito=[[1, 0]]),
], ids=[f"payload{i}" for i in range(22)])
def test_req_030_schema_invalido_rejeitado_antes_de_executar_codigo(invalido):
    executor = ExecutorFalso(stdout="5\n")
    res = _validar(copy.deepcopy(invalido), executor)
    assert res.aprovado is False
    assert executor.chamadas == [], "nenhum código pode rodar antes do schema ser validado"
