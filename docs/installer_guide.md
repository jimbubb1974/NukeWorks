# NukeWorks Windows Installer Guide

This document walks through building the self-contained Windows distribution and installer for NukeWorks. The process produces two artifacts:

1. A PyInstaller `onedir` bundle that includes Python, dependencies, and application assets.
2. A Windows installer (`*.exe`) built with Inno Setup that deploys the bundle, creates shortcuts, and optionally runs the app.

Both stages are orchestrated by scripts in the `installer/` directory.

---

## 1. Prerequisites

- **Windows 10 or later** with administrative rights (installer targets `Program Files`).
- **Python 3.12 (64-bit)** installed locally. SQLAlchemy 2.0.23 is not compatible with Python 3.13+, so the build environment must use Python 3.12.
- **Inno Setup 6.x** installed. The scripts look for `ISCC.exe` in the default install locations (`C:\Program Files (x86)\Inno Setup 6\`).
- **PowerShell 7+** (`pwsh`) to run the helper scripts.
- Optional (but recommended): valid code-signing credentials and access to your signing service.

> **Tip:** If your development virtual environment targets Python 3.13, create a separate packaging environment that points to Python 3.12 to run the build scripts.

---

## 2. Prepare the packaging environment

```pwsh
# From the repo root
py -3.12 -m venv .venv-packaging
.venv-packaging\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt    # installs PyInstaller and app deps
```

Leave the environment activated while running the build commands below. (The default scripts assume the interpreter is at `.\venv\Scripts\python.exe`; update the `-PythonPath` argument if you use a different venv.)

---

## 3. Build the PyInstaller bundle

```pwsh
pwsh installer/build_executable.py
```

This command:

- Validates that Python ≤ 3.12 is in use.
- Generates `dist/NukeWorks/` containing `NukeWorks.exe`, Python runtime files, templates, migrations, the sample SQLite database, and other required assets.
- Produces temporary build artifacts under `build/`.

You can re-run this at any time; it automatically cleans previous outputs unless you pass `--no-clean`.

---

## 4. Build the Windows installer

```pwsh
pwsh installer/build_installer.ps1
```

The helper script performs the following:

1. (Optional) Rebuilds the PyInstaller bundle unless `-SkipExecutable` is supplied.
2. Locates `ISCC.exe` (use `-IsccPath` to override if Inno Setup is in a non-standard directory).
3. Reads `APPLICATION_VERSION` from `config.py` (or use `-Version` to set it explicitly).
4. Compiles `installer/nukeworks.iss`, writing the installer to `installer/out/NukeWorks-<version>-Setup.exe`.
5. Optionally signs binaries when `-SigningCommand` is provided.

Key arguments:

- `-PythonPath`: absolute or relative path to the Python interpreter running PyInstaller.
- `-SkipExecutable`: reuse an existing `dist/NukeWorks` directory.
- `-SkipInstallerBuild`: stop after creating the PyInstaller bundle.
- `-IsccPath`: point to a custom `ISCC.exe`.
- `-Version`: override the version embedded in the installer filename.
- `-SigningCommand`: command template to sign artifacts. Use `{file}` as a placeholder for the target path (see below).

Example with signing:

```pwsh
pwsh installer/build_installer.ps1 `
  -PythonPath .\.venv-packaging\Scripts\python.exe `
  -SigningCommand 'C:\Tools\signtool.exe sign /fd sha256 /tr http://timestamp.digicert.com /td sha256 /a "{file}"'
```

The script signs both `dist\NukeWorks\NukeWorks.exe` and the final installer if the command succeeds.

---

## 5. Code-signing workflow

NukeWorks binaries should be signed before distribution. The `-SigningCommand` parameter lets you integrate any signing solution that can be invoked via CLI.

Guidelines:

- Ensure the command replaces `{file}` with the file path, including quotes if required by your tool.
- If your signing service requires uploading files, adjust the script to call a wrapper that handles the upload and download steps.
- Sign the PyInstaller executable *before* building the installer so the signed binary is bundled.
- Sign the installer (`installer/out/NukeWorks-<version>-Setup.exe`) after compilation to avoid Windows SmartScreen warnings.

---

## 6. Customizing the installer

The Inno Setup script `installer/nukeworks.iss` controls installer metadata and assets.

- Update `MyAppPublisher` and `MyAppURL` with the correct organization details.
- Modify `AppId` only if you intentionally need a different uninstall identity.
- Add extra files or directories by extending the `[Files]` section (e.g., documentation PDFs).
- Adjust `OutputBaseFilename` if you prefer a different naming convention.
- To include an icon, add `SetupIconFile` to `[Setup]` and ship an `.ico` asset in the PyInstaller bundle.

Remember to keep `dist/NukeWorks` in sync with any additional resources referenced in the installer script.

---

## 7. Post-install behaviour

The installer:

- Deploys the PyInstaller bundle under `C:\Program Files\NukeWorks`.
- Creates `logs`, `uploads`, and `flask_sessions` directories (retained across upgrades/uninstalls).
- Adds Start Menu and optional desktop shortcuts.
- Offers to launch NukeWorks immediately after install.

Users can update configuration by editing `.env` in the installation directory or pointing `NUKEWORKS_DB_PATH` to a network database before launching.

---

## 8. Cleaning up

- Remove `build/` and `dist/` directories after validating the installer if you need to reclaim space.
- Delete `installer/out/` contents from previous builds to avoid confusion when distributing releases.

---

## 9. Troubleshooting

- **PyInstaller build fails with SQLAlchemy AssertionError:** Ensure you are running Python 3.12. Re-create the packaging virtual environment if necessary.
- **`ISCC.exe` not found:** Install Inno Setup 6 and re-run, or pass `-IsccPath` with the correct location.
- **Signing command fails:** Verify credentials, certificate passwords, and network connectivity for timestamp servers. The script stops on signing failures to prevent distributing unsigned binaries.
- **Installer missing assets:** Confirm the required files exist inside `dist/NukeWorks` before invoking Inno Setup; rerun `build_executable.py` after adding new resources to the project.

---

With these scripts in place, releasing a signed Windows installer becomes a repeatable, one-command process once prerequisites are installed. Adjust versioning, signing, and metadata details to align with your deployment policies.
