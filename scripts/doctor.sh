#!/usr/bin/env bash
# Só leitura: mostra OK/FALTA das ferramentas e do ambiente. Nunca imprime valores do .env.
# Uso: scripts/doctor.sh [RAIZ_DO_PROJETO]
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT" || exit 1
REQUIRED=(NEXT_PUBLIC_API_URL DATABASE_URL CORS_ORIGIN MODEL_PROVIDER MODEL_NAME GEMINI_API_KEY GROQ_API_KEY)
FALTAS=0
linha() { printf '%-7s %-28s %s\n' "$1" "$2" "$3"; if [ "$1" = "FALTA" ]; then FALTAS=$((FALTAS+1)); fi; return 0; }
ver() { "$@" 2>&1 | head -1; }
# Lê o valor de uma chave do .env sem exibir (usado só para testar se está vazio).
valor() {
  grep -E "^[[:space:]]*$1[[:space:]]*=" .env | tail -1 | cut -d= -f2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\\(.*\\)'\$/\\1/"
}

echo "== Ferramentas =="
if command -v git >/dev/null; then linha OK git "$(ver git --version)"; else linha FALTA git "instale o Git"; fi
if command -v node >/dev/null; then linha OK node "$(ver node -v)"; else linha FALTA node "instale o Node 22 LTS"; fi
if command -v npm >/dev/null; then linha OK npm "$(ver npm -v)"; else linha FALTA npm "vem com o Node"; fi
if command -v uv >/dev/null; then
  linha OK uv "$(ver uv --version)"
  PY312="$(uv python find 3.12 2>/dev/null)"
  if [ -n "$PY312" ]; then linha OK "python 3.12" "$PY312"; else linha FALTA "python 3.12" "rode: uv python install 3.12"; fi
else
  linha FALTA uv "instale: https://docs.astral.sh/uv/getting-started/installation/"
  linha FALTA "python 3.12" "instale o uv e rode: uv python install 3.12"
fi
if command -v docker >/dev/null; then linha OK docker "$(ver docker --version)"; else linha AVISO docker "ausente (só preciso para Postgres local)"; fi

echo; echo "== Projeto =="
VPY=""
if [ -x apps/api/.venv/bin/python ]; then VPY=apps/api/.venv/bin/python
elif [ -x apps/api/.venv/Scripts/python.exe ]; then VPY=apps/api/.venv/Scripts/python.exe; fi
if [ -n "$VPY" ]; then
  V="$("$VPY" --version 2>&1)"
  case "$V" in
    *3.12.*) linha OK "venv da API" "$V" ;;
    *) linha AVISO "venv da API" "$V (esperado 3.12; apague apps/api/.venv e rode scripts/setup)" ;;
  esac
  if "$VPY" -c "import fastapi, pytest" >/dev/null 2>&1 && "$VPY" -m ruff --version >/dev/null 2>&1; then
    linha OK "deps da API" "fastapi, pytest, ruff"
  else linha FALTA "deps da API" "rode scripts/setup"; fi
else linha FALTA "venv da API" "rode scripts/setup"; fi
if [ -d node_modules ]; then linha OK node_modules "instalado"; else linha FALTA node_modules "rode scripts/setup"; fi
HP="$(git config core.hooksPath 2>/dev/null)"
if [ -n "$HP" ] && [ -f .husky/pre-commit ] && [ -d "$HP" ]; then linha OK "hook pre-commit" "core.hooksPath=$HP"
else linha FALTA "hook pre-commit" "rode scripts/setup"; fi

echo; echo "== .env (valores não são exibidos) =="
if [ -f .env ]; then
  linha OK ".env" "presente"
  for k in "${REQUIRED[@]}"; do
    if [ -n "$(valor "$k")" ]; then linha OK "$k" "preenchida"; else linha FALTA "$k" "vazia ou ausente"; fi
  done
else linha FALTA ".env" "rode scripts/setup (copia o .env.example)"; fi

echo; echo "== Git =="
BR="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
linha OK "branch" "$BR"
if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
  UP="$(git rev-parse --abbrev-ref '@{u}')"
  read -r BEHIND AHEAD <<<"$(git rev-list --left-right --count '@{u}...HEAD')"
  if [ "$BEHIND" = 0 ] && [ "$AHEAD" = 0 ]; then linha OK "sincronia" "igual a $UP (último fetch)"
  else linha AVISO "sincronia" "$UP: $AHEAD à frente, $BEHIND atrás (último fetch; rode git fetch)"; fi
else linha AVISO "sincronia" "sem upstream (git push -u origin $BR)"; fi
if [ -n "$(git status --porcelain)" ]; then linha AVISO "árvore" "há alterações não commitadas"; else linha OK "árvore" "limpa"; fi

echo
if [ "$FALTAS" -eq 0 ]; then echo "Tudo certo."; else echo "$FALTAS item(ns) em FALTA."; fi
exit 0
