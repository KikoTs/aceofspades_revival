$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Targets = @(
    "steam_emu.ini",
    "steam_emu copy.ini",
    "steam_api.cdx",
    "steam_api.rne",
    "steam_api.dll.,BACKUP"
)

foreach ($relativePath in $Targets) {
    $fullPath = Join-Path $Root $relativePath
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Force
        Write-Host "Removed $relativePath"
    }
}

Write-Host "Legacy steam_emu artifacts cleaned."
