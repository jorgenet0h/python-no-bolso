# Cria ..\python-no-bolso-testes na branch tests/suite para a sessão de testes (/testar).
# ATENÇÃO: o bloqueio de leitura em .claude\settings.local.json é uma TRAVA DE SEGURANÇA, não uma
# muralha: reduz o acesso acidental a apps/api/app e apps/web/src, mas não impede um Bash determinado.
# Limites (docs: code.claude.com/docs/en/permissions): Read deny cobre Read/Edit/Write e, em melhor esforço,
# Grep/Glob e cat/head/tail/sed; NÃO cobre `grep -r` a partir de pasta pai nem scripts. O sandbox (denyRead)
# não funciona no Windows nativo, por isso não é usado. Idempotente. Uso: scripts\worktree-testes.ps1
$Here = $PSScriptRoot
$Root = Split-Path -Parent $Here
$Dest = Join-Path (Split-Path -Parent $Root) 'python-no-bolso-testes'
$Br = 'tests/suite'
Set-Location $Root

function CommonDir($dir) { (git -C $dir rev-parse --path-format=absolute --git-common-dir 2>$null) }
if ((Test-Path $Dest) -and (CommonDir $Dest) -and ((CommonDir $Dest) -eq (CommonDir $Root))) {
  "Worktree já existe em $Dest (reaproveitado)."
} elseif (Test-Path $Dest) {
  "ERRO: $Dest existe mas não é um worktree deste repositório. Mova ou apague."; exit 1
} else {
  git fetch origin $Br *> $null
  git show-ref --verify --quiet "refs/heads/$Br"
  if ($LASTEXITCODE -eq 0) { git worktree add $Dest $Br }
  else {
    git show-ref --verify --quiet "refs/remotes/origin/$Br"
    if ($LASTEXITCODE -eq 0) { git worktree add -b $Br $Dest "origin/$Br" }
    else { git worktree add -b $Br $Dest HEAD }
  }
  if ($LASTEXITCODE -ne 0) { exit 1 }
}

# O setup roda a partir deste repositório, mas sobre o worktree (a branch tests/suite pode não ter scripts/).
& (Join-Path $Here 'setup.ps1') -Root $Dest
if ($LASTEXITCODE -ne 0) { exit 1 }

New-Item -ItemType Directory -Force (Join-Path $Dest '.claude') | Out-Null
$json = @'
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
'@
[System.IO.File]::WriteAllText((Join-Path $Dest '.claude\settings.local.json'), $json, (New-Object System.Text.UTF8Encoding($false)))
"Criado $Dest\.claude\settings.local.json (trava de segurança, não muralha)."
"Abra o Claude Code em $Dest e rode /testar <requisitos>."
