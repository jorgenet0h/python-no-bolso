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
        # a listagem devolve ids "models/x"; a URL já tem "models/", então o prefixo não pode repetir
        self.modelo, self._chave = modelo.removeprefix("models/"), chave
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


# ---------------------------------------------------------------- listagem de modelos (CLI)

class ErroListagem(RuntimeError):
    """Falha ao listar modelos. Carrega só o tipo do erro e o status HTTP: nunca URL, header ou corpo."""

    def __init__(self, tipo: str, status: int | None = None):
        self.tipo, self.status = tipo, status
        super().__init__(f"{tipo}" + (f" (HTTP {status})" if status else ""))


def _get(url: str, headers: dict, params: dict | None = None) -> dict:
    try:
        r = httpx.get(url, headers=headers, params=params, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise ErroListagem("HTTPStatusError", e.response.status_code) from None
    except (httpx.HTTPError, ValueError) as e:
        raise ErroListagem(type(e).__name__) from None


def listar_modelos_gemini(chave: str) -> list[str]:
    """Modelos que suportam generateContent. A chave vai só no header x-goog-api-key."""
    nomes: list[str] = []
    token = None
    for _ in range(10):  # a API pagina; teto de páginas por segurança
        params = {"pageSize": 1000, **({"pageToken": token} if token else {})}
        corpo = _get("https://generativelanguage.googleapis.com/v1beta/models",
                     {"x-goog-api-key": chave}, params)
        for m in corpo.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                nomes.append(str(m.get("name", "")).removeprefix("models/"))
        token = corpo.get("nextPageToken")
        if not token:
            break
    return sorted(n for n in nomes if n)


def listar_modelos_groq(chave: str) -> list[str]:
    corpo = _get("https://api.groq.com/openai/v1/models", {"Authorization": f"Bearer {chave}"})
    return sorted(str(m.get("id", "")) for m in corpo.get("data", []) if m.get("id"))
