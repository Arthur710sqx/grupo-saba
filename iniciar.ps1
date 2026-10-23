$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$sabaPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $sabaPython)) { throw 'Crie o ambiente Python conforme o README.md.' }
& $sabaPython app.py
