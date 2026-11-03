param([switch]$Offline)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 virtual environment creation failed' }
}
$dependencyFile = if (Test-Path 'requirements-lock.txt') { 'requirements-lock.txt' } else { 'requirements-dev.txt' }
if ($Offline) {
    .venv/Scripts/python.exe -m pip install --no-index --find-links wheelhouse -r $dependencyFile
} else {
    .venv/Scripts/python.exe -m pip install -r $dependencyFile
}
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
if (-not (Test-Path 'vendor/ARC-AGI-3-Agents/agents/agent.py')) {
    git clone --depth 1 https://github.com/arcprize/ARC-AGI-3-Agents.git vendor/ARC-AGI-3-Agents
    if ($LASTEXITCODE -ne 0) { throw 'Framework download failed' }
    git -C vendor/ARC-AGI-3-Agents fetch --depth 1 origin 4743e7d0aaae0ded0d98a89a7e282e63564cd58b
    if ($LASTEXITCODE -ne 0) { throw 'Pinned framework commit download failed' }
    git -C vendor/ARC-AGI-3-Agents checkout --detach 4743e7d0aaae0ded0d98a89a7e282e63564cd58b
    if ($LASTEXITCODE -ne 0) { throw 'Pinned framework checkout failed' }
}
.venv/Scripts/python.exe scripts/slim_framework.py
if ($LASTEXITCODE -ne 0) { throw 'Framework preparation failed' }
