# Cria atalhos oficiais com icone personalizado no Desktop e na raiz do projeto
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$IconPath = Join-Path $ScriptDir "assets\icon.ico"
$SilentLauncher = Join-Path $ScriptDir "launch_silent.vbs"

$WshShell = New-Object -ComObject WScript.Shell

# 1. Atalho na Area de Trabalho (Desktop)
$DesktopShortcutPath = Join-Path $DesktopPath "Sollaris Nova.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$SilentLauncher`""
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.IconLocation = "$IconPath, 0"
$Shortcut.Description = "Sollaris Nova - PC Optimizer"
$Shortcut.Save()
Write-Host "[OK] Atalho criado na Area de Trabalho: $DesktopShortcutPath" -ForegroundColor Green

# 2. Atalho na pasta raiz do projeto
$RootShortcutPath = Join-Path $ScriptDir "Sollaris Nova.lnk"
$RootShortcut = $WshShell.CreateShortcut($RootShortcutPath)
$RootShortcut.TargetPath = "wscript.exe"
$RootShortcut.Arguments = "`"$SilentLauncher`""
$RootShortcut.WorkingDirectory = $ScriptDir
$RootShortcut.IconLocation = "$IconPath, 0"
$RootShortcut.Description = "Sollaris Nova - PC Optimizer"
$RootShortcut.Save()
Write-Host "[OK] Atalho criado na raiz do projeto: $RootShortcutPath" -ForegroundColor Green

Write-Host ""
Write-Host "Pronto! Agora voce pode iniciar o Sollaris Nova com um clique duplo diretamente pelo icone na Area de Trabalho ou na raiz do projeto, sem nenhuma janela preta de terminal abrindo." -ForegroundColor Cyan
