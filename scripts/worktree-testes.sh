#!/usr/bin/env bash
# Cria ../python-no-bolso-testes na branch tests/suite para a sessão de testes (/testar).
# ATENÇÃO: o bloqueio de leitura em .claude/settings.local.json é uma TRAVA DE SEGURANÇA, não uma
# muralha: reduz o acesso acidental a apps/api/app e apps/web/src, mas não impede um Bash determinado.
# Limites (docs: code.claude.com/docs/en/permissions): Read deny cobre Read/Edit/Write e, em melhor esforço,
# Grep/Glob e cat/head/tail/sed; NÃO cobre `grep -r` a partir de pasta pai nem scripts. O sandbox (denyRead)
# não funciona no Windows nativo, por isso não é usado. Idempotente. Uso: scripts/worktree-testes.sh
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
DEST="$(cd "$ROOT/.." && pwd)/python-no-bolso-testes"
BR=tests/suite
cd "$ROOT" || exit 1

mesmo_repo() { [ "$(cd "$DEST" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" = "$(git rev-parse --path-format=absolute --git-common-dir)" ]; }
if [ -d "$DEST" ] && mesmo_repo; then
  echo "Worktree já existe em $DEST (reaproveitado)."
elif [ -e "$DEST" ]; then
  echo "ERRO: $DEST existe mas não é um worktree deste repositório. Mova ou apague."; exit 1
else
  git fetch origin "$BR" >/dev/null 2>&1 || true
  if git show-ref --verify --quiet "refs/heads/$BR"; then git worktree add "$DEST" "$BR" || exit 1
  elif git show-ref --verify --quiet "refs/remotes/origin/$BR"; then git worktree add -b "$BR" "$DEST" "origin/$BR" || exit 1
  else git worktree add -b "$BR" "$DEST" HEAD || exit 1; fi
fi

# O setup roda a partir deste repositório, mas sobre o worktree (a branch tests/suite pode não ter scripts/).
bash "$HERE/setup.sh" "$DEST" || exit 1

mkdir -p "$DEST/.claude"
cat > "$DEST/.claude/settings.local.json" <<'JSON'
{
  "permissions": {
    "deny": [
      "Read(/apps/api/app)",
      "Read(/apps/api/app/**)",
      "Read(/apps/web/src)",
      "Read(/apps/web/src/**)"
    ]
  }
}
JSON
echo "Criado $DEST/.claude/settings.local.json (trava de segurança, não muralha)."
echo "Abra o Claude Code em $DEST e rode /testar <requisitos>."
