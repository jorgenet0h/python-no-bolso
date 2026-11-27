# Prepara o projeto neste computador. Idempotente. Não instala nada global e não grava/imprime segredos.
# Uso: scripts\setup.ps1 [-Root RAIZ_DO_PROJETO]   (a raiz serve para o worktree-testes)
param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$Here = $PSScriptRoot
Set-Location $Root
"Setup em: $Root"
function Tem($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

$falta = @()
if (-not (Tem git))  { $falta += 'Git: winget install --id Git.Git' }
if (-not (Tem node)) { $falta += 'Node 22 LTS: winget install --id OpenJS.NodeJS.LTS' }
if (-not (Tem uv))   { $falta += 'uv: winget install --id astral-sh.uv' }
# Python 3.12 só é exigido para criar o venv; um venv já existente apenas gera aviso (ver abaixo).
$venv = Join-Path $Root 'apps\api\.venv'
$vpy = Join-Path $venv 'Scripts\python.exe'
if ((-not (Test-Path $vpy)) -and (Tem uv) -and -not (& uv python find 3.12 2>$null)) { $falta += 'Python 3.12: uv python install 3.12' }
if (-not (Tem docker)) { 'AVISO: Docker não encontrado (só preciso para Postgres local): https://docs.docker.com/get-docker/' }
if ($falta.Count -gt 0) { 'Instale antes de continuar:'; $falta | ForEach-Object { "  - $_" }; exit 1 }

'== npm install =='
npm install; if ($LASTEXITCODE -ne 0) { exit 1 }

'== Ambiente da API =='
if (-not (Test-Path $vpy)) {
  uv venv --python 3.12 $venv; if ($LASTEXITCODE -ne 0) { exit 1 }
} elseif (-not ((& $vpy --version 2>&1 | Out-String) -match '3\.12\.')) {
  "AVISO: o venv existente não é 3.12; para recriar, apague $venv e rode de novo."
}
uv pip install --python $vpy -r (Join-Path $Root 'apps\api\requirements-dev.txt'); if ($LASTEXITCODE -ne 0) { exit 1 }

'== Playwright (chromium) =='
npx playwright install chromium; if ($LASTEXITCODE -ne 0) { 'AVISO: a instalação do chromium falhou; rode: npx playwright install chromium' }

'== Hook de pre-commit =='
npx husky *> $null
$hp = (git config core.hooksPath)
if ($hp) { "hook ativo (core.hooksPath=$hp)" } else { 'AVISO: hook não ativou; rode: npx husky' }

'== .env =='
$envFile = Join-Path $Root '.env'
if (Test-Path $envFile) { '.env já existe (não alterado).' }
else { Copy-Item (Join-Path $Root '.env.example') $envFile; '.env criado a partir do .env.example.' }
'Variáveis obrigatórias ainda vazias no .env:'
$linhas = Get-Content $envFile -Encoding UTF8
$vazias = 0
foreach ($k in 'NEXT_PUBLIC_API_URL','DATABASE_URL','CORS_ORIGIN','MODEL_PROVIDER','MODEL_NAME','GEMINI_API_KEY','GROQ_API_KEY') {
  $m = $linhas | Where-Object { $_ -match "^\s*$k\s*=" } | Select-Object -Last 1
  $val = if ($m) { ($m -replace '^[^=]*=', '').Trim().Trim('"').Trim("'") } else { '' }
  if (-not $val) { "  - $k"; $vazias++ }
}
if ($vazias -eq 0) { '  (nenhuma)' }

''; '== Doctor =='
& (Join-Path $Here 'doctor.ps1') -Root $Root
