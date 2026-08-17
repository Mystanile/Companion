$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $root "dist\Companion\Companion.exe"

if (-not (Test-Path $exe)) {
    Write-Error "Build first with: .\build.ps1"
}

$startup = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startup "Companion.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = Split-Path $exe -Parent
$shortcut.Description = "Companion voice assistant"
$shortcut.Save()

Write-Host "Added startup shortcut: $shortcutPath"
Write-Host "Companion will launch when you sign in to Windows."
