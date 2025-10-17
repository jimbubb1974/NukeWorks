#requires -Version 7.0
<#
.SYNOPSIS
Build and optionally sign the NukeWorks Windows installer.

.DESCRIPTION
Wraps the PyInstaller executable build and the Inno Setup compiler so the
entire packaging process can be triggered with a single command. Optionally
invokes a code-signing command for both the application executable and the
resulting installer bundle.

.PARAMETER PythonPath
The Python interpreter to use for running PyInstaller. Defaults to the
project's virtual environment at ..\venv\Scripts\python.exe.

.PARAMETER SkipExecutable
Skip rebuilding the PyInstaller bundle and reuse the contents of dist\NukeWorks.

.PARAMETER IsccPath
Path to Inno Setup's ISCC.exe compiler. If omitted, the script searches common
install locations.

.PARAMETER Version
Version string to embed in the installer file name. When omitted, the script
parses config.py (APPLICATION_VERSION) and falls back to 1.0.0 if not found.

.PARAMETER SigningCommand
Optional command template used to sign binaries. Include the literal token
{file} where the artifact path should be substituted, for example:
  signtool.exe sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a /f C:\certs\code_signing.pfx /p <PASSWORD> "{file}"

.PARAMETER SkipInstallerBuild
Skip running Inno Setup and only (re)build the PyInstaller bundle.

.EXAMPLE
pwsh installer/build_installer.ps1

.EXAMPLE
pwsh installer/build_installer.ps1 -Version 1.2.0 -SigningCommand 'C:\Tools\signtool.exe sign /fd sha256 /a /tr http://timestamp.digicert.com "{file}"'
#>
param(
    [string]$PythonPath = ".\venv\Scripts\python.exe",
    [switch]$SkipExecutable,
    [switch]$SkipInstallerBuild,
    [string]$IsccPath,
    [string]$Version,
    [string]$SigningCommand
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptRoot "..")

Push-Location $repoRoot
try {
    function Get-AppVersion {
        param([string]$Fallback = "1.0.0")
        $configPath = Join-Path $repoRoot "config.py"
        if (-not (Test-Path $configPath)) {
            return $Fallback
        }

        $match = Select-String -Path $configPath -Pattern "APPLICATION_VERSION\s*=\s*['""]([^'""]+)['""]" -ErrorAction SilentlyContinue
        if ($match -and $match.Matches.Count -gt 0) {
            return $match.Matches[0].Groups[1].Value
        }

        return $Fallback
    }

    function Resolve-IsccPath {
        param([string]$Override)
        if ($Override) {
            if (-not (Test-Path $Override)) {
                throw "Inno Setup compiler not found at override path '$Override'"
            }
            return (Resolve-Path $Override).Path
        }

        $candidates = @()
        if (${env:ProgramFiles(x86)}) {
            $candidates += (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
        }
        if ($env:ProgramFiles) {
            $candidates += (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
        }
        if ($env:ProgramW6432) {
            $candidates += (Join-Path $env:ProgramW6432 "Inno Setup 6\ISCC.exe")
        }

        foreach ($candidate in $candidates) {
            if ($candidate -and (Test-Path $candidate)) {
                return (Resolve-Path $candidate).Path
            }
        }

        throw "Unable to locate Inno Setup's ISCC.exe. Install Inno Setup 6 or supply -IsccPath."
    }

    function Invoke-CodeSign {
        param([string]$TargetPath)
        if ([string]::IsNullOrWhiteSpace($SigningCommand)) {
            return
        }

        if (-not (Test-Path $TargetPath)) {
            Write-Warning "Skipping signing for '$TargetPath' because the file was not found."
            return
        }

        if (-not $SigningCommand.Contains("{file}")) {
            throw "SigningCommand must include the literal '{file}' placeholder so the script can substitute the target path."
        }

        $quotedPath = '"' + (Resolve-Path $TargetPath).Path + '"'
        $commandToRun = $SigningCommand.Replace("{file}", $quotedPath)
        Write-Host "Signing $TargetPath using command: $SigningCommand"
        Invoke-Expression $commandToRun

        if ($LASTEXITCODE -ne 0) {
            throw "Code signing command exited with status $LASTEXITCODE"
        }
    }

    $resolvedPython = Resolve-Path $PythonPath -ErrorAction Stop
    Write-Host "Using Python: $resolvedPython"

    if (-not $SkipExecutable) {
        Write-Host "Building PyInstaller bundle..."
        & $resolvedPython installer/build_executable.py
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller build failed with exit code $LASTEXITCODE"
        }
    }
    else {
        Write-Host "Skipping PyInstaller build as requested."
    }

    $distDir = Join-Path $repoRoot "dist"
    $bundleDir = Join-Path $distDir "NukeWorks"
    if (-not (Test-Path $bundleDir)) {
        throw "Expected PyInstaller output at '$bundleDir'. Re-run without -SkipExecutable."
    }

    $appExe = Join-Path $bundleDir "NukeWorks.exe"
    Invoke-CodeSign -TargetPath $appExe

    if ($SkipInstallerBuild) {
        Write-Host "Skipping Inno Setup installer build as requested."
        return
    }

    $resolvedIscc = Resolve-IsccPath -Override $IsccPath
    Write-Host "Using Inno Setup compiler: $resolvedIscc"

    if (-not $Version) {
        $Version = Get-AppVersion
        Write-Host "Inferred version from config.py: $Version"
    }
    else {
        Write-Host "Using provided version: $Version"
    }

    $issPath = Join-Path $scriptRoot "nukeworks.iss"
    if (-not (Test-Path $issPath)) {
        throw "Inno Setup script not found at '$issPath'"
    }

    $outputDir = Join-Path $scriptRoot "out"
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir | Out-Null
    }

    Write-Host "Compiling installer..."
    & $resolvedIscc "/Qp" "/DMyAppVersion=$Version" $issPath
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compiler failed with exit code $LASTEXITCODE"
    }

    $installerName = "NukeWorks-$Version-Setup.exe"
    $installerPath = Join-Path $outputDir $installerName
    if (-not (Test-Path $installerPath)) {
        throw "Expected installer output not found at '$installerPath'"
    }

    Invoke-CodeSign -TargetPath $installerPath

    Write-Host ""
    Write-Host "Installer build complete."
    Write-Host " - Executable bundle: $bundleDir"
    Write-Host " - Installer: $installerPath"
}
finally {
    Pop-Location
}
