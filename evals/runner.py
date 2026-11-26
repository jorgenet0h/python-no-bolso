"""Runner dos evals: roda a MESMA bateria (evals/casos.yaml) em cada modelo de evals/models.yaml.

Uso (a partir da raiz do repositório, com o venv da API ativo):
    python -m evals.runner                       # modelos reais; gasta cota; exige chaves no ambiente
    python -m evals.runner --modelos groq-llama  # um modelo só
    python -m evals.runner --deterministico      # mock, sem rede, sem cota (não mede modelo real)

Não roda no CI por padrão: gasta cota dos provedores gratuitos. Resultados em evals/results/.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

from evals import provedores
from evals.execucao import executar
from evals.metricas import metrica_a, metrica_b, metrica_c, metrica_d
from evals.selfbleu import self_bleu

RAIZ = Path(__file__).parent
MAX_PASSOS = 4
TOOLS = [{"nome": "executar_python", "descricao": "executa código Python e devolve a saída"}]
SISTEMA = (
    "Você gera exercícios de lógica de Python para estudo no celular. Responda SEMPRE com um único "
    "objeto JSON, sem texto fora dele. Para testar código antes de entregar, responda "
    '{"tool": "executar_python", "args": {"codigo": "..."}} e aguarde o resultado. Para entregar, '
    "responda o exercício com os campos: tipo, nivel, tema, enunciado, codigo, opcoes (lista de "
    "textos), gabarito (lista de índices inteiros das opções), saida_esperada (texto impresso pelo "
    "código), explicacao, explicacoes_por_opcao (objeto índice->texto). Regras por tipo: "
    "prever_saida: codigo imprime a saída e o gabarito aponta a opção com essa saída. "
    "completar_lacuna: codigo tem '___' e o gabarito aponta a opção que completa. "
    "ordenar_linhas: opcoes são as linhas do programa embaralhadas, gabarito é a ordem correta "
    "(índices em sequência de execução), codigo vazio, e só UMA ordem pode funcionar. "
    "achar_bug: codigo tem um defeito, codigo_corrigido é a versão correta, opcoes são as linhas "
    "do codigo, gabarito aponta a linha com defeito e saida_esperada é a saída da versão corrigida. "
    "Use apenas print e a biblioteca padrão básica (math, itertools, collections)."
)


def carregar_yaml(caminho: Path) -> dict:
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def gerar(provedor, caso: dict) -> tuple[object, list[str], str | None]:
    """Loop mínimo (espelha a arquitetura): modelo -> tool -> modelo, até o exercício final."""
    mensagens = [
        {"role": "system", "content": SISTEMA},
        {"role": "user", "content": f"tipo={caso['tipo']} nivel={caso['nivel']} "
                                    f"tema={caso['tema']} caso={caso['id']}"},
    ]
    tools: list[str] = []
    for _ in range(MAX_PASSOS):
        try:
            resp = provedor.completar(mensagens, TOOLS)
        except Exception as e:  # noqa: BLE001  rede, cota, HTTP: o eval registra e segue
            return None, tools, f"erro do provedor: {type(e).__name__}"
        if resp.get("tool") == "executar_python":
            tools.append("executar_python")
            res = executar(str(resp.get("args", {}).get("codigo", "")))
            mensagens.append({"role": "assistant", "content": json.dumps(resp, ensure_ascii=False)})
            mensagens.append({"role": "user", "content": json.dumps(
                {"resultado": {"ok": res.ok, "stdout": res.stdout[:500], "motivo": res.motivo}})})
            continue
        return resp.get("final", resp), tools, None
    return None, tools, "limite de passos sem exercício"


def avaliar_caso(provedor, caso: dict) -> dict:
    inicio = time.monotonic()
    exercicio, tools, erro = gerar(provedor, caso)
    saida = {"caso": caso["id"], "tipo": caso["tipo"], "tools": tools, "a": None, "b": None,
             "c": None, "d": None, "motivo": erro, "exercicio": exercicio}
    if exercicio is None:
        saida["acao"] = "falhou"
    else:
        saida["b"], motivo_b = metrica_b(exercicio)
        if not saida["b"]:
            saida["motivo"] = f"(b) {motivo_b}"
            saida["acao"] = "rejeitado"
        else:
            saida["a"], motivo_a = metrica_a(exercicio)
            saida["c"], motivo_c = metrica_c(exercicio)
            saida["d"], motivo_d = metrica_d(exercicio)
            falhas = [f"({k}) {m}" for k, ok, m in
                      [("a", saida["a"], motivo_a), ("c", saida["c"], motivo_c),
                       ("d", saida["d"], motivo_d)] if ok is False]
            saida["motivo"] = "; ".join(falhas) or None
            saida["acao"] = "rejeitado" if falhas else "aprovado"
    saida["duracao_s"] = round(time.monotonic() - inicio, 2)
    return saida


def _taxa(valores: list) -> float | None:
    aplicaveis = [v for v in valores if v is not None]
    return sum(1 for v in aplicaveis if v) / len(aplicaveis) if aplicaveis else None


def resumir(casos: list[dict]) -> dict:
    validos = [c["exercicio"] for c in casos if c["b"]]
    textos = [f"{e['enunciado']} {e['codigo']}" for e in validos]
    return {
        "casos": len(casos),
        "aprovados": sum(c["acao"] == "aprovado" for c in casos),
        "a_saida_afirmada_igual_a_obtida": _taxa([c["a"] for c in casos if c["b"]]),
        "b_json_valido_no_schema": _taxa([c["b"] if c["acao"] != "falhou" else False for c in casos]),
        "c_achar_bug_defeito_falha_e_correcao_funciona": _taxa([c["c"] for c in casos]),
        "d_ordenar_linhas_ordem_unica": _taxa([c["d"] for c in casos]),
        "e_self_bleu": self_bleu(textos),
    }


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:.0f}%"


def tabela_markdown(nome: str, cfg: dict, resumo: dict, casos: list[dict], deterministico: bool) -> str:
    aviso = ("> **Modo determinístico: respostas de um mock. Estes números NÃO medem modelo "
             "real.**\n\n" if deterministico else "")
    sb = resumo["e_self_bleu"]
    linhas = [
        f"## {nome} ({cfg['provedor']}/{cfg['modelo']})", "", aviso + "| Métrica | Resultado |",
        "|---|---|",
        f"| Casos aprovados | {resumo['aprovados']}/{resumo['casos']} |",
        f"| (a) saída afirmada = saída obtida | {_pct(resumo['a_saida_afirmada_igual_a_obtida'])} |",
        f"| (b) JSON válido no schema | {_pct(resumo['b_json_valido_no_schema'])} |",
        (f"| (c) achar-bug: defeito falha e correção funciona | "
        f"{_pct(resumo['c_achar_bug_defeito_falha_e_correcao_funciona'])} |"),
        f"| (d) montar-código: ordem única | {_pct(resumo['d_ordenar_linhas_ordem_unica'])} |",
        f"| (e) Self-BLEU (menor = mais variedade) | {'n/a' if sb is None else f'{sb:.3f}'} |",
        "", "| Caso | Tipo | Ação | Tools | a | b | c | d | Motivo |", "|---|---|---|---|---|---|---|---|---|",
    ]
    sinal = {True: "ok", False: "FALHA", None: "-"}
    for c in casos:
        linhas.append(
            f"| {c['caso']} | {c['tipo']} | {c['acao']} | {','.join(c['tools']) or '-'} | "
            f"{sinal[c['a']]} | {sinal[c['b']]} | {sinal[c['c']]} | {sinal[c['d']]} | "
            f"{(c['motivo'] or '').replace('|', '/')[:90]} |")
    return "\n".join(linhas) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--modelos", help="nomes separados por vírgula (padrão: todos de models.yaml)")
    ap.add_argument("--casos", type=int, help="usa só os N primeiros casos")
    ap.add_argument("--deterministico", action="store_true", help="mock, sem rede nem cota")
    ap.add_argument("--saida", type=Path, help="pasta de resultados (padrão: evals/results/<data>)")
    args = ap.parse_args(argv)

    casos = carregar_yaml(RAIZ / "casos.yaml")["casos"][: args.casos]
    modelos = carregar_yaml(RAIZ / "models.yaml")["modelos"]
    if args.modelos:
        pedidos = set(args.modelos.split(","))
        modelos = [m for m in modelos if m["nome"] in pedidos]
    if len(modelos) < 2 and not args.modelos:
        print("models.yaml precisa de 2 ou mais modelos (REQ-042)", file=sys.stderr)
        return 2
    saida = args.saida or RAIZ / "results" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    saida.mkdir(parents=True, exist_ok=True)

    partes_md = []
    for i, cfg in enumerate(modelos):
        try:
            provedor = provedores.criar(cfg, args.deterministico, i)
        except (RuntimeError, ValueError) as e:
            print(f"[{cfg['nome']}] pulado: {e}", file=sys.stderr)
            continue
        resultados = [avaliar_caso(provedor, c) for c in casos]
        resumo = resumir(resultados)
        (saida / f"{cfg['nome']}.json").write_text(json.dumps(
            {"modelo": cfg["nome"], "provedor": cfg["provedor"], "id_modelo": cfg["modelo"],
             "deterministico": args.deterministico, "resumo": resumo, "casos": resultados},
            ensure_ascii=False, indent=2), encoding="utf-8")
        md = tabela_markdown(cfg["nome"], cfg, resumo, resultados, args.deterministico)
        (saida / f"{cfg['nome']}.md").write_text(md, encoding="utf-8")
        partes_md.append(md)
        print(f"[{cfg['nome']}] {resumo['aprovados']}/{resumo['casos']} aprovados", file=sys.stderr)
    (saida / "resumo.md").write_text("# Resultados dos evals\n\n" + "\n".join(partes_md),
                                     encoding="utf-8")
    print(f"resultados em {saida}", file=sys.stderr)
    return 0 if partes_md else 1


if __name__ == "__main__":
    raise SystemExit(main())
