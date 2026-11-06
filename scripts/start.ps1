$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$env:PYTHONIOENCODING = 'utf-8'
$taskPython = Get-Command python -ErrorAction SilentlyContinue
if ($taskPython) { & $taskPython.Source -m backend.server; exit $LASTEXITCODE }
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) { & $bundledPython -m backend.server; exit $LASTEXITCODE }
Write-Error '请安装 Python 3.11 或更高版本，然后重新运行。'
