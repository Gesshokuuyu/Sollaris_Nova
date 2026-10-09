# Cria atalhos oficiais com icone personalizado no Desktop e na raiz do projeto
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$IconPath = Join-Path $ProjectRoot "assets\sollaris_nova.ico"
$SilentLauncher = Join-Path $ScriptDir "launch_silent.vbs"

$WshShell = New-Object -ComObject WScript.Shell

# 1. Atalho na Area de Trabalho (Desktop)
$DesktopShortcutPath = Join-Path $DesktopPath "Sollaris Nova.lnk"
if (Test-Path $DesktopShortcutPath) {
    Remove-Item -Force $DesktopShortcutPath
}
$Shortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$SilentLauncher`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = "$IconPath, 0"
$Shortcut.Description = "Sollaris Nova - PC Optimizer"
$Shortcut.Save()
Write-Host "[OK] Atalho criado na Area de Trabalho: $DesktopShortcutPath" -ForegroundColor Green

# 2. Atalho na pasta raiz do projeto
$RootShortcutPath = Join-Path $ProjectRoot "Sollaris Nova.lnk"
if (Test-Path $RootShortcutPath) {
    Remove-Item -Force $RootShortcutPath
}
$RootShortcut = $WshShell.CreateShortcut($RootShortcutPath)
$RootShortcut.TargetPath = "wscript.exe"
$RootShortcut.Arguments = "`"$SilentLauncher`""
$RootShortcut.WorkingDirectory = $ProjectRoot
$RootShortcut.IconLocation = "$IconPath, 0"
$RootShortcut.Description = "Sollaris Nova - PC Optimizer"
$RootShortcut.Save()
Write-Host "[OK] Atalho criado na raiz do projeto: $RootShortcutPath" -ForegroundColor Green

# Forca o Windows Shell a invalidar o cache de icones e redesenhar a Area de Trabalho imediatamente
try {
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    public class ShellRefresh {
        [DllImport("shell32.dll")]
        public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
    }
"@
    [ShellRefresh]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
    Write-Host "[OK] Cache de icones do Windows atualizado." -ForegroundColor Cyan
} catch {
    [ShellRefresh]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
}
