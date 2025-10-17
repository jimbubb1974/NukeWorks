# NukeWorks Uninstaller
# This script removes NukeWorks installation and all associated files

param(
    [switch]$Force,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

# NukeWorks installation details
$AppName = "NukeWorks"
$InstallDir = "${env:ProgramFiles}\NukeWorks"
$AppDataDir = "${env:LOCALAPPDATA}\NukeWorks"
$RegistryKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\NukeWorks"

function Write-Status {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor Green
    }
}

function Write-Error {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host "ERROR: $Message" -ForegroundColor Red
    }
}

function Write-Warning {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host "WARNING: $Message" -ForegroundColor Yellow
    }
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remove-NukeWorksFiles {
    Write-Status "Removing NukeWorks files..."
    
    # Remove main installation directory
    if (Test-Path $InstallDir) {
        try {
            Remove-Item -Path $InstallDir -Recurse -Force
            Write-Status "✓ Removed installation directory: $InstallDir"
        }
        catch {
            Write-Error "Failed to remove installation directory: $($_.Exception.Message)"
            if (-not $Force) {
                throw
            }
        }
    }
    else {
        Write-Status "Installation directory not found: $InstallDir"
    }
    
    # Remove AppData directory (user data)
    if (Test-Path $AppDataDir) {
        try {
            Remove-Item -Path $AppDataDir -Recurse -Force
            Write-Status "✓ Removed user data directory: $AppDataDir"
        }
        catch {
            Write-Warning "Failed to remove user data directory: $($_.Exception.Message)"
        }
    }
    else {
        Write-Status "User data directory not found: $AppDataDir"
    }
}

function Remove-NukeWorksRegistry {
    Write-Status "Removing registry entries..."
    
    try {
        if (Test-Path $RegistryKey) {
            Remove-Item -Path $RegistryKey -Recurse -Force
            Write-Status "✓ Removed registry key: $RegistryKey"
        }
        else {
            Write-Status "Registry key not found: $RegistryKey"
        }
    }
    catch {
        Write-Warning "Failed to remove registry key: $($_.Exception.Message)"
    }
}

function Remove-NukeWorksShortcuts {
    Write-Status "Removing shortcuts..."
    
    $shortcutPaths = @(
        "${env:PUBLIC}\Desktop\NukeWorks.lnk",
        "${env:USERPROFILE}\Desktop\NukeWorks.lnk",
        "${env:APPDATA}\Microsoft\Windows\Start Menu\Programs\NukeWorks.lnk"
    )
    
    foreach ($shortcut in $shortcutPaths) {
        if (Test-Path $shortcut) {
            try {
                Remove-Item -Path $shortcut -Force
                Write-Status "✓ Removed shortcut: $shortcut"
            }
            catch {
                Write-Warning "Failed to remove shortcut: $shortcut - $($_.Exception.Message)"
            }
        }
    }
}

function Show-UninstallSummary {
    Write-Status ""
    Write-Status "=========================================="
    Write-Status "NukeWorks Uninstall Summary"
    Write-Status "=========================================="
    Write-Status "✓ Installation directory removed"
    Write-Status "✓ User data directory removed"
    Write-Status "✓ Registry entries removed"
    Write-Status "✓ Shortcuts removed"
    Write-Status ""
    Write-Status "NukeWorks has been successfully uninstalled."
    Write-Status "You may need to restart your computer to complete the removal."
}

# Main uninstall process
try {
    Write-Status "=========================================="
    Write-Status "NukeWorks Uninstaller"
    Write-Status "=========================================="
    Write-Status ""
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-Error "This uninstaller must be run as Administrator."
        Write-Status "Please right-click and 'Run as Administrator'"
        exit 1
    }
    
    # Confirm uninstall unless forced
    if (-not $Force) {
        Write-Status "This will completely remove NukeWorks and all its data."
        $confirm = Read-Host "Are you sure you want to continue? (y/N)"
        if ($confirm -ne 'y' -and $confirm -ne 'Y') {
            Write-Status "Uninstall cancelled."
            exit 0
        }
    }
    
    Write-Status ""
    Write-Status "Starting NukeWorks uninstall..."
    
    # Stop any running NukeWorks processes
    Write-Status "Stopping NukeWorks processes..."
    try {
        Get-Process -Name "NukeWorks" -ErrorAction SilentlyContinue | Stop-Process -Force
        Write-Status "✓ Stopped NukeWorks processes"
    }
    catch {
        Write-Status "No NukeWorks processes found"
    }
    
    # Remove files and directories
    Remove-NukeWorksFiles
    
    # Remove registry entries
    Remove-NukeWorksRegistry
    
    # Remove shortcuts
    Remove-NukeWorksShortcuts
    
    # Show summary
    Show-UninstallSummary
    
    Write-Status ""
    Write-Status "Uninstall completed successfully!"
}
catch {
    Write-Error "Uninstall failed: $($_.Exception.Message)"
    Write-Status ""
    Write-Status "You may need to manually remove:"
    Write-Status "  - $InstallDir"
    Write-Status "  - $AppDataDir"
    Write-Status "  - $RegistryKey"
    exit 1
}
