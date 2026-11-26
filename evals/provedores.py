"""Provedores de modelo dos evals. Interface única: completar(mensagens, tools) -> dict.

O dict devolvido é uma ação: {"tool": "executar_python", "args": {"codigo": ...}} ou o exercício
final (JSON do schema). Os provedores reais pedem JSON puro e fazem o parse; texto fora de JSON
vira {"_invalido": "<texto>"}, que o runner conta como falha de schema (b), nunca como exceção.

O provedor `mock` é determinístico, não faz rede e não mede modelo nenhum: serve para testar a
própria bateria de métricas (e para um passo de CI sem gastar cota).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
from typing import ClassVar, Protocol

import httpx


class Provedor(Protocol):
    def completar(self, mensagens: list[dict], tools: list[dict]) -> dict: ...


def extrair_json(texto: str) -> dict:
    texto = texto.strip()
    cerca = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texto, re.DOTALL)
    if cerca:
        texto = cerca.group(1)
    try:
        obj = json.loads(texto)
    except ValueError:
        return {"_invalido": texto[:300]}
    return obj if isinstance(obj, dict) else {"_invalido": texto[:300]}


class _HttpBase:
    def __init__(self, modelo: str, chave_env: str, timeout_s: float = 60.0):
        self.modelo = modelo
        self.chave = os.environ.get(chave_env)
        if not self.chave:
            raise RuntimeError(f"variável de ambiente {chave_env} não definida")
        self.cliente = httpx.Client(timeout=timeout_s)


class Gemini(_HttpBase):
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

    def completar(self, mensagens: list[dict], tools: list[dict]) -> dict:
        partes = [{"role": "model" if m["role"] == "assistant" else "user",
                   "parts": [{"text": m["content"]}]} for m in mensagens if m["role"] != "system"]
        sistema = " ".join(m["content"] for m in mensagens if m["role"] == "system")
        corpo = {"contents": partes, "systemInstruction": {"parts": [{"text": sistema}]},
                 "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
        r = self.cliente.post(self.URL.format(modelo=self.modelo), json=corpo,
                              headers={"x-goog-api-key": self.chave})
        r.raise_for_status()
        texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return extrair_json(texto)


class Groq(_HttpBase):
    URL = "https://api.groq.com/openai/v1/chat/completions"

    def completar(self, mensagens: list[dict], tools: list[dict]) -> dict:
        corpo = {"model": self.modelo, "messages": mensagens, "temperature": 0.9,
                 "response_format": {"type": "json_object"}}
        r = self.cliente.post(self.URL, json=corpo,
                              headers={"Authorization": f"Bearer {self.chave}"})
        r.raise_for_status()
        return extrair_json(r.json()["choices"][0]["message"]["content"])


# ----------------------------------------------------------------------------- mock

def _semente(*partes: str) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(partes).encode()).hexdigest()[:12], 16))


def _distratores(rng: random.Random, certo: int, n: int = 4) -> tuple[list[str], int]:
    valores = {certo}
    while len(valores) < n:
        valores.add(certo + rng.choice([-3, -2, -1, 1, 2, 3, 10]))
    lista = [str(v) for v in sorted(valores)]
    rng.shuffle(lista)
    return lista, lista.index(str(certo))


def _explicacoes(n: int) -> dict:
    return {str(i): f"A opção {i} não corresponde ao resultado da execução." for i in range(n)}


def exercicio_modelo(tipo: str, nivel: str, tema: str, caso: str, defeito: str | None = None) -> dict:
    """Gera um exercício VÁLIDO (passa em a-d) e, se `defeito`, injeta a falha escolhida."""
    rng = _semente(tipo, nivel, tema, caso)
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(1, 5)
    base = {"tipo": tipo, "nivel": nivel, "tema": tema, "explicacao": "Execute o código passo a passo."}
    if tipo == "prever_saida":
        saida = a * b + c
        opcoes, idx = _distratores(rng, saida)
        ex = {**base, "enunciado": f"Qual é a saída do programa sobre {tema}?",
              "codigo": f"a = {a}\nb = {b}\nprint(a * b + {c})", "opcoes": opcoes,
              "gabarito": [idx], "saida_esperada": f"{saida}\n"}
    elif tipo == "completar_lacuna":
        opcoes, idx = _distratores(rng, b)
        ex = {**base, "enunciado": f"Complete a lacuna para imprimir {a + b}.",
              "codigo": f"total = {a} + ___\nprint(total)", "opcoes": opcoes,
              "gabarito": [idx], "saida_esperada": f"{a + b}\n"}
    elif tipo == "ordenar_linhas":
        pecas = [f"x = {a}", f"y = x * {b}", "print(y)"]
        if defeito == "ordem_ambigua":
            pecas = [f"x = {a}", f"y = {b}", "print(x + y)"]  # duas ordens válidas
        ordem_embaralhada = [2, 0, 1]
        opcoes = [pecas[i] for i in ordem_embaralhada]
        gabarito = [ordem_embaralhada.index(i) for i in range(3)]
        saida = f"{a * b}\n" if defeito != "ordem_ambigua" else f"{a + b}\n"
        ex = {**base, "enunciado": "Ordene as linhas para o programa imprimir o resultado.",
              "codigo": "", "opcoes": opcoes, "gabarito": gabarito, "saida_esperada": saida}
    else:  # achar_bug
        n = a + 2
        buggy = f"n = {n}\nsoma = 0\nfor i in range(n):\n    soma += i\nprint(soma)"
        certo = f"n = {n}\nsoma = 0\nfor i in range(1, n + 1):\n    soma += i\nprint(soma)"
        linhas = buggy.splitlines()[:4]
        ex = {**base, "enunciado": "Qual linha impede o programa de somar de 1 até n?",
              "codigo": buggy, "codigo_corrigido": certo if defeito != "bug_igual" else buggy,
              "opcoes": linhas, "gabarito": [2], "saida_esperada": f"{n * (n + 1) // 2}\n"}
    ex["explicacoes_por_opcao"] = _explicacoes(len(ex["opcoes"]))
    if defeito == "saida_errada":
        ex["saida_esperada"] = "999\n"
    elif defeito == "schema":
        del ex["explicacao"]
    return ex


class Mock:
    """Perfil "perfeito": sempre válido, chama a tool uma vez antes de responder.
    Perfil "defeituoso": injeta uma falha determinística em parte dos casos."""

    DEFEITOS: ClassVar[dict[int, str]] = {0: "saida_errada", 3: "schema", 5: "ordem_ambigua", 6: "bug_igual"}

    def __init__(self, perfil: str = "perfeito"):
        self.perfil = perfil
        self.passo: dict[str, int] = {}

    def completar(self, mensagens: list[dict], tools: list[dict]) -> dict:
        usuario = next(m for m in reversed(mensagens) if m["role"] == "user" and "tipo=" in m["content"])
        campos = dict(re.findall(r"(\w+)=(\w+)", usuario["content"]))
        chave = campos["caso"]
        passo = self.passo[chave] = self.passo.get(chave, 0) + 1
        if passo == 1:
            return {"tool": "executar_python", "args": {"codigo": "print('verificando')"}}
        defeito = None
        if self.perfil == "defeituoso":
            indice = int(chave.lstrip("c")) - 1
            defeito = self.DEFEITOS.get(indice)
            if defeito == "ordem_ambigua" and campos["tipo"] != "ordenar_linhas":
                defeito = None
            if defeito == "bug_igual" and campos["tipo"] != "achar_bug":
                defeito = None
        return exercicio_modelo(campos["tipo"], campos["nivel"], campos["tema"], chave, defeito)


def criar(cfg: dict, deterministico: bool, indice: int) -> Provedor:
    if deterministico:
        return Mock("perfeito" if indice % 2 == 0 else "defeituoso")
    classes = {"gemini": Gemini, "groq": Groq}
    if cfg["provedor"] not in classes:
        raise ValueError(f"provedor desconhecido: {cfg['provedor']}")
    return classes[cfg["provedor"]](cfg["modelo"], cfg["chave_env"])
