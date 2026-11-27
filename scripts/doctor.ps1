# Só leitura: mostra OK/FALTA das ferramentas e do ambiente. Nunca imprime valores do .env.
# Uso: scripts\doctor.ps1 [-Root RAIZ_DO_PROJETO]
param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Continue'
Set-Location $Root
$Required = 'NEXT_PUBLIC_API_URL','DATABASE_URL','CORS_ORIGIN','MODEL_PROVIDER','MODEL_NAME','GEMINI_API_KEY','GROQ_API_KEY'
$script:Faltas = 0
function Linha($s, $n, $d) {
  '{0,-7} {1,-28} {2}' -f $s, $n, $d
  if ($s -eq 'FALTA') { $script:Faltas++ }
}
function Tem($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Ver($c, $a) { (& $c $a 2>&1 | Select-Object -First 1) -as [string] }

'== Ferramentas =='
if (Tem git)  { Linha OK git (Ver git '--version') }   else { Linha FALTA git 'instale o Git' }
if (Tem node) { Linha OK node (Ver node '-v') }        else { Linha FALTA node 'instale o Node 22 LTS' }
if (Tem npm)  { Linha OK npm (Ver npm '-v') }          else { Linha FALTA npm 'vem com o Node' }
if (Tem uv) {
  Linha OK uv (Ver uv '--version')
  $py = (& uv python find 3.12 2>$null | Select-Object -First 1)
  if ($py) { Linha OK 'python 3.12' $py } else { Linha FALTA 'python 3.12' 'rode: uv python install 3.12' }
} else {
  Linha FALTA uv 'instale: winget install --id astral-sh.uv'
  Linha FALTA 'python 3.12' 'instale o uv e rode: uv python install 3.12'
}
if (Tem docker) { Linha OK docker (Ver docker '--version') } else { Linha AVISO docker 'ausente (só preciso para Postgres local)' }

''; '== Projeto =='
$vpy = Join-Path $Root 'apps\api\.venv\Scripts\python.exe'
if (-not (Test-Path $vpy)) { $vpy = Join-Path $Root 'apps/api/.venv/bin/python' }
if (Test-Path $vpy) {
  $v = (& $vpy --version 2>&1 | Out-String).Trim()
  if ($v -match '3\.12\.') { Linha OK 'venv da API' $v }
  else { Linha AVISO 'venv da API' "$v (esperado 3.12; apague apps\api\.venv e rode scripts\setup)" }
  & $vpy -c 'import fastapi, pytest' 2>$null; $a = $LASTEXITCODE
  & $vpy -m ruff --version 2>$null | Out-Null; $b = $LASTEXITCODE
  if ($a -eq 0 -and $b -eq 0) { Linha OK 'deps da API' 'fastapi, pytest, ruff' } else { Linha FALTA 'deps da API' 'rode scripts\setup' }
} else { Linha FALTA 'venv da API' 'rode scripts\setup' }
if (Test-Path (Join-Path $Root 'node_modules')) { Linha OK node_modules 'instalado' } else { Linha FALTA node_modules 'rode scripts\setup' }
$hp = (git config core.hooksPath 2>$null)
if ($hp -and (Test-Path (Join-Path $Root '.husky/pre-commit')) -and (Test-Path (Join-Path $Root $hp))) { Linha OK 'hook pre-commit' "core.hooksPath=$hp" }
else { Linha FALTA 'hook pre-commit' 'rode scripts\setup' }

''; '== .env (valores não são exibidos) =='
$envFile = Join-Path $Root '.env'
if (Test-Path $envFile) {
  Linha OK '.env' 'presente'
  $linhas = Get-Content $envFile -Encoding UTF8
  foreach ($k in $Required) {
    $m = $linhas | Where-Object { $_ -match "^\s*$k\s*=" } | Select-Object -Last 1
    $val = if ($m) { ($m -replace '^[^=]*=', '').Trim().Trim('"').Trim("'") } else { '' }
    if ($val) { Linha OK $k 'preenchida' } else { Linha FALTA $k 'vazia ou ausente' }
  }
} else { Linha FALTA '.env' 'rode scripts\setup (copia o .env.example)' }

''; '== Git =='
$br = (git rev-parse --abbrev-ref HEAD 2>$null)
Linha OK branch $br
$up = (git rev-parse --abbrev-ref '@{u}' 2>$null)
if ($LASTEXITCODE -eq 0 -and $up) {
  $c = (git rev-list --left-right --count '@{u}...HEAD') -split '\s+'
  if ($c[0] -eq '0' -and $c[1] -eq '0') { Linha OK sincronia "igual a $up (último fetch)" }
  else { Linha AVISO sincronia "${up}: $($c[1]) à frente, $($c[0]) atrás (último fetch; rode git fetch)" }
} else { Linha AVISO sincronia "sem upstream (git push -u origin $br)" }
if (git status --porcelain) { Linha AVISO 'árvore' 'há alterações não commitadas' } else { Linha OK 'árvore' 'limpa' }

''
if ($script:Faltas -eq 0) { 'Tudo certo.' } else { "$($script:Faltas) item(ns) em FALTA." }
exit 0
