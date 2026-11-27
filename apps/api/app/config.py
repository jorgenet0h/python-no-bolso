"""Configuração por variáveis de ambiente (REQ-023, D-20). Trocar de provedor ou modelo não muda o loop."""

import os

from app.agent.provedores import Gemini, Groq

# provedor -> (classe, variável com a chave)
PROVEDORES = {
    "gemini": (Gemini, "GEMINI_API_KEY"),
    "groq": (Groq, "GROQ_API_KEY"),
}


class ConfiguracaoInvalida(RuntimeError):
    """Só ocorre na CLI administrativa; nunca em requisição de usuário."""


def carregar_provedor():
    """Provedor escolhido por MODEL_PROVIDER e MODEL_NAME; a chave vem da variável do provedor."""
    nome = (os.environ.get("MODEL_PROVIDER") or "").strip().lower()
    modelo = (os.environ.get("MODEL_NAME") or "").strip()
    if nome not in PROVEDORES:
        raise ConfiguracaoInvalida(f"MODEL_PROVIDER deve ser um de: {', '.join(PROVEDORES)}")
    if not modelo:
        raise ConfiguracaoInvalida("MODEL_NAME não definido")
    classe, variavel_chave = PROVEDORES[nome]
    chave = os.environ.get(variavel_chave)
    if not chave:
        raise ConfiguracaoInvalida(f"{variavel_chave} não definida")
    return classe(modelo, chave)


def listar_modelos() -> list[str]:
    """Modelos do provedor de MODEL_PROVIDER (não exige MODEL_NAME). Só para a CLI."""
    from app.agent import provedores

    nome = (os.environ.get("MODEL_PROVIDER") or "").strip().lower()
    if nome not in PROVEDORES:
        raise ConfiguracaoInvalida(f"MODEL_PROVIDER deve ser um de: {', '.join(PROVEDORES)}")
    variavel = PROVEDORES[nome][1]
    chave = os.environ.get(variavel)
    if not chave:
        raise ConfiguracaoInvalida(f"{variavel} não definida")
    listar = {"gemini": provedores.listar_modelos_gemini, "groq": provedores.listar_modelos_groq}
    return listar[nome](chave)
