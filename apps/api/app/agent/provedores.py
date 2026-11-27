"""Provedores reais de modelo (Gemini e Groq, tier gratuito). Interface única (D-18):
completar(mensagens, tools) -> dict, com `nome` e `modelo` para o registro da execução.

O dict devolvido é uma ação ({"tool", "args"}) ou o exercício final. Texto que não seja um objeto
JSON vira {"_invalido": ...}: o validador o rejeita, nunca é executado. A chave vai em header,
nunca na URL, para não vazar em log de erro.
"""

import json
import re

import httpx


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


class Gemini:
    nome = "gemini"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

    def __init__(self, modelo: str, chave: str, timeout_s: float = 60.0):
        self.modelo, self._chave = modelo, chave
        self._cliente = httpx.Client(timeout=timeout_s)

    def completar(self, mensagens: list[dict], tools: list[dict] | None = None) -> dict:
        partes = [{"role": "model" if m["role"] == "assistant" else "user",
                   "parts": [{"text": m["content"]}]} for m in mensagens if m["role"] != "system"]
        sistema = " ".join(m["content"] for m in mensagens if m["role"] == "system")
        corpo = {"contents": partes, "systemInstruction": {"parts": [{"text": sistema}]},
                 "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}}
        r = self._cliente.post(self.URL.format(modelo=self.modelo), json=corpo,
                               headers={"x-goog-api-key": self._chave})
        r.raise_for_status()
        return extrair_json(r.json()["candidates"][0]["content"]["parts"][0]["text"])


class Groq:
    nome = "groq"
    URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, modelo: str, chave: str, timeout_s: float = 60.0):
        self.modelo, self._chave = modelo, chave
        self._cliente = httpx.Client(timeout=timeout_s)

    def completar(self, mensagens: list[dict], tools: list[dict] | None = None) -> dict:
        corpo = {"model": self.modelo, "messages": mensagens, "temperature": 0.9,
                 "response_format": {"type": "json_object"}}
        r = self._cliente.post(self.URL, json=corpo,
                               headers={"Authorization": f"Bearer {self._chave}"})
        r.raise_for_status()
        return extrair_json(r.json()["choices"][0]["message"]["content"])
