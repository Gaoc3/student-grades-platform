# Get the directory of this script
$ScriptDir = Split-Path -Parent $PSCommandPath
if (-not $ScriptDir) {
    $ScriptDir = (Get-Item -Path ".").FullName
}

$VbsPath = Join-Path $ScriptDir "start_sync_background.vbs"

# Startup folder path
$StartupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$ShortcutPath = Join-Path $StartupFolder "AutoGitSync.lnk"

# Create COM Object for Shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$VbsPath`""
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "Auto Git Sync background service for student-grades-platform"
$Shortcut.Save()

Write-Output "Startup shortcut created successfully at: $ShortcutPath"
Write-Output "Auto Git Sync is now configured to start automatically on Windows logon."
