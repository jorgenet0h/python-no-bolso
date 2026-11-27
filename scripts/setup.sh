#!/usr/bin/env bash
# Prepara o projeto neste computador. Idempotente. Não instala nada global e não grava/imprime segredos.
# Uso: scripts/setup.sh [RAIZ_DO_PROJETO]   (a raiz serve para o worktree-testes)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${1:-$(cd "$HERE/.." && pwd)}"
cd "$ROOT" || exit 1
echo "Setup em: $ROOT"

FALTA=()
command -v git >/dev/null || FALTA+=("Git: https://git-scm.com/downloads")
command -v node >/dev/null || FALTA+=("Node 22 LTS: https://nodejs.org (ou nvm install 22)")
command -v uv >/dev/null || FALTA+=("uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
# Python 3.12 só é exigido para criar o venv; um venv já existente apenas gera aviso (ver abaixo).
TEM_VENV=0
if [ -x apps/api/.venv/bin/python ] || [ -x apps/api/.venv/Scripts/python.exe ]; then TEM_VENV=1; fi
if [ "$TEM_VENV" = 0 ] && command -v uv >/dev/null && [ -z "$(uv python find 3.12 2>/dev/null)" ]; then
  FALTA+=("Python 3.12: uv python install 3.12")
fi
command -v docker >/dev/null || echo "AVISO: Docker não encontrado (só preciso para Postgres local): https://docs.docker.com/get-docker/"
if [ ${#FALTA[@]} -gt 0 ]; then
  echo "Instale antes de continuar:"; printf '  - %s\n' "${FALTA[@]}"; exit 1
fi

echo "== npm install =="
npm install || exit 1

echo "== Ambiente da API =="
VENV=apps/api/.venv
VPY=""
if [ -x "$VENV/bin/python" ]; then VPY="$VENV/bin/python"
elif [ -x "$VENV/Scripts/python.exe" ]; then VPY="$VENV/Scripts/python.exe"; fi
if [ -z "$VPY" ]; then
  uv venv --python 3.12 "$VENV" || exit 1
  if [ -x "$VENV/bin/python" ]; then VPY="$VENV/bin/python"; else VPY="$VENV/Scripts/python.exe"; fi
else
  case "$("$VPY" --version 2>&1)" in
    *3.12.*) ;;
    *) echo "AVISO: o venv existente não é 3.12; para recriar, apague $VENV e rode de novo." ;;
  esac
fi
uv pip install --python "$VPY" -r apps/api/requirements-dev.txt || exit 1

echo "== Playwright (chromium) =="
npx playwright install chromium || echo "AVISO: falhou; no Linux talvez precise de: npx playwright install --with-deps chromium (usa sudo)"

echo "== Hook de pre-commit =="
npx husky >/dev/null 2>&1 || true
if [ -n "$(git config core.hooksPath)" ]; then echo "hook ativo (core.hooksPath=$(git config core.hooksPath))"
else echo "AVISO: hook não ativou; rode: npx husky"; fi

echo "== .env =="
if [ -f .env ]; then echo ".env já existe (não alterado)."
else cp .env.example .env && echo ".env criado a partir do .env.example."; fi
echo "Variáveis obrigatórias ainda vazias no .env:"
VAZIAS=0
for k in NEXT_PUBLIC_API_URL DATABASE_URL CORS_ORIGIN MODEL_PROVIDER MODEL_NAME GEMINI_API_KEY GROQ_API_KEY; do
  v="$(grep -E "^[[:space:]]*$k[[:space:]]*=" .env | tail -1 | cut -d= -f2- | sed -e 's/[[:space:]]//g' -e 's/["'"'"']//g')"
  if [ -z "$v" ]; then echo "  - $k"; VAZIAS=1; fi
done
if [ "$VAZIAS" = 0 ]; then echo "  (nenhuma)"; fi

echo
echo "== Doctor =="
bash "$HERE/doctor.sh" "$ROOT"
